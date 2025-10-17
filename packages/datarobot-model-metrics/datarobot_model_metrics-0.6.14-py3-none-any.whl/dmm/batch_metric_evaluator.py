#
# Copyright 2022-2024 DataRobot, Inc. and its affiliates.
#
# All rights reserved.
#
# DataRobot, Inc.
#
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
#
# Released under the terms of DataRobot Tool and Utility Agreement.
import logging
from typing import Dict, List, Tuple, Union

import pandas as pd

from dmm.constants import ColumnName, DataGroups
from dmm.data_source.datarobot_source import BatchDataRobotSource
from dmm.metric.metric_base import MetricBase
from dmm.metric_evaluator import MetricEvaluatorBase

logger = logging.getLogger(__name__)


class BatchMetricEvaluator(MetricEvaluatorBase):
    """
    Evaluate a Model Metric using training data and scoring data. This class is
    used to "stream" data through the metric object and generate the metric values.
    Used with batch custom metrics.
    """

    def __init__(
        self,
        metric: Union[str, MetricBase],
        source: BatchDataRobotSource,
        prediction_col: str = ColumnName.PREDICTIONS,
        batch_id_col: str = ColumnName.BATCH_ID_COLUMN,
        timestamp_col: str = ColumnName.TIMESTAMP,
        filter_predictions: bool = False,
        filter_scoring_data: bool = False,
        segment_attribute: str = None,
        segment_value: str = None,
    ):
        """
        Initialize the MetricEvaluator framework.
        :param metric: A single metric or a list of metrics. Metrics need to be based on ModelMetric class or a string
        representing a name of an SKLearn metric.
        :param source: A data source object that will be usd to get the data in chunks
        :param prediction_col: The name of the prediction column
        :param batch_id_col: The name of the batch ID column
        :param filter_predictions: whether the metric evaluator removes missing predictions values before scoring.
        :param filter_scoring_data: whether the metric evaluator removes missing scoring values before scoring.
        :param segment_attribute The name of the column with segment values
        :param segment_value The value of the segment attribute to segment on
        """
        super().__init__(metric=metric)
        self._data_source = source
        if self._data_source is None:
            raise Exception("Can not evaluate a metric without a data source")

        self._prediction_col = prediction_col
        self._batch_id_col = batch_id_col
        self._timestamp_col = timestamp_col
        self._groups_to_filter = self._get_groups_to_filter(
            filter_predictions, filter_scoring_data
        )
        self._segment_attribute = segment_attribute
        self._segment_value = segment_value
        if self._segment_value and not self._segment_attribute:
            raise Exception(
                "Segment attribute must be specified when segment value is specified"
            )

    def _run_score(self, chunk_of_data: pd.DataFrame) -> Dict[str, float]:
        scored_values = {}
        predictions = (
            chunk_of_data[self._prediction_col].to_numpy()
            if self._prediction_col in chunk_of_data
            else None
        )

        for me_data in self._metrics:
            metric_name = me_data.metric_name
            metric = me_data.metric
            scored_values[metric_name] = metric.score(
                predictions=predictions if metric.need_predictions() else None,
                actuals=None,
                scoring_data=(
                    self._get_scoring_data(chunk_of_data)
                    if metric.need_scoring_data()
                    else None
                ),
            )
            self._stats.nr_calls_to_score += 1
        return scored_values

    def _get_data_chunk(
        self,
    ) -> Tuple[Union[pd.DataFrame, None], int, bool]:
        done = False
        chunk_of_data, bucket_id = self._data_source.get_data()

        if chunk_of_data is None:
            done = True
            return chunk_of_data, bucket_id, done

        if len(chunk_of_data) > self._data_source.max_rows:
            raise Exception("Chunk of data has too many rows")

        if self._segment_attribute:
            if self._segment_attribute not in chunk_of_data:
                raise Exception(
                    f"Segment attribute: {self._segment_attribute} not found in exported data"
                )
            chunk_of_data = chunk_of_data.loc[
                chunk_of_data[self._segment_attribute] == self._segment_value
            ]

        self._stats.total_rows += len(chunk_of_data)
        return chunk_of_data, bucket_id, done

    def _validate_data_chunk(self, data_chunk: pd.DataFrame) -> pd.DataFrame:
        for me_data in self._metrics:
            metric_name = me_data.metric_name
            metric = me_data.metric
            if metric.need_predictions() and self._prediction_col not in data_chunk:
                raise Exception(
                    f"Metric {metric_name} requires predictions, but data chunk is missing column "
                    f"{self._prediction_col}, columns present: {', '.join(data_chunk.columns)}"
                )
        if self._groups_to_filter:
            data_chunk = self._drop_missing_values_from_data_chunk(data_chunk)
        return data_chunk

    def _drop_missing_values_from_data_chunk(
        self, data_chunk: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Remove missing values from a chunk of data based on selected groups to be filtered.
        """
        original_length = len(data_chunk)
        if (
            self._prediction_col in data_chunk
            and DataGroups.PREDICTIONS in self._groups_to_filter
        ):
            data_chunk = data_chunk.dropna(subset=[self._prediction_col])

        if DataGroups.SCORING in self._groups_to_filter:
            subset = [
                col_name
                for col_name in data_chunk.columns
                if col_name not in [self._prediction_col]
            ]
            data_chunk = data_chunk.dropna(subset=subset)

        if original_length != len(data_chunk):
            rows_difference = original_length - len(data_chunk)
            logger.warning(
                f"removed {rows_difference} rows out of {original_length} in the data chunk "
                f"before scoring, due to missing values in {self._groups_to_filter} data"
            )

        return data_chunk

    def _get_scoring_data(self, chunk_of_data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract only data used in scoring
        """
        _chunk_of_data = chunk_of_data.copy()
        _chunk_of_data = _chunk_of_data.drop(
            columns=[
                self._prediction_col,
                self._timestamp_col,
                self._batch_id_col,
                ColumnName.ASSOCIATION_ID_COLUMN,
            ],
            errors="ignore",
        )
        return _chunk_of_data

    @staticmethod
    def _get_groups_to_filter(
        filter_predictions: bool, filter_scoring_data: bool
    ) -> List[DataGroups]:
        groups_to_filter = []
        if filter_predictions:
            groups_to_filter.append(DataGroups.PREDICTIONS)
        if filter_scoring_data:
            groups_to_filter.append(DataGroups.SCORING)
        return groups_to_filter

    def score(self) -> pd.DataFrame:
        """
        Steps to evaluate a metric
        1. Get Data from source
        2. Chunk data into max_rows per metric and into buckets
        4. Feed data to the metric transform
        5. Reduce transform results into the necessary buckets
        6. Return Dataframe where there is a column per metric and a row per bucket
        :return: a Dataframe with a row per bucket in the data. For each bucket there will be
                 the value of the metric, number of samples used to calculate the metric and the batch ID
        """
        done = False
        prev_bucket_id = None
        bucket_metric_nr_samples = 0
        bucket_batch_id = None

        bucket_scores = {me_data.metric_name: [] for me_data in self._metrics}
        final_scores = {me_data.metric_name: [] for me_data in self._metrics}

        output_nr_samples_list = []
        output_bucket_batch_list = []
        while not done:
            data_chunk, bucket_id, done = self._get_data_chunk()

            # Moved to a new time bucket so calling reduce on the previous values
            if bucket_id != prev_bucket_id:
                # We don't reduce in the first time we get data (as prev is None and id is not None)
                if prev_bucket_id is not None:
                    # Moved to a new time bucket (or done).. need to reduce
                    reduced_values = self._reduce_bucket_metric(bucket_scores)
                    if reduced_values:
                        output_nr_samples_list.append(bucket_metric_nr_samples)
                        output_bucket_batch_list.append(bucket_batch_id)
                    for metric, value in reduced_values.items():
                        final_scores[metric].append(value)
                        bucket_scores[metric].clear()
                bucket_metric_nr_samples = 0
                prev_bucket_id = bucket_id

            # Running the score and keeping the value until it is time to reduce
            # If we are done - we will not call the transform.
            if done:
                continue

            data_chunk = self._validate_data_chunk(data_chunk)
            if data_chunk.index.size == 0:
                logger.warning(f"data chunk is empty, skipping scoring...")
                continue

            for metric_name, value in self._run_score(data_chunk).items():
                bucket_scores[metric_name].append(value)
            bucket_metric_nr_samples += data_chunk.index.size
            bucket_batch_id = data_chunk[self._batch_id_col].iat[0]

        result_df = pd.DataFrame(
            {
                ColumnName.BATCH_ID_COLUMN: output_bucket_batch_list,
                ColumnName.NR_SAMPLES: output_nr_samples_list,
                **final_scores,
            }
        )
        return result_df
