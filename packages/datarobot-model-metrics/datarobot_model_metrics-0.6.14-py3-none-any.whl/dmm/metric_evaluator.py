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
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from dmm.constants import ColumnName, DataGroups, TimeBucket
from dmm.data_source.data_source_base import DataSourceBase
from dmm.exceptions import ConflictError
from dmm.metric.geo_metrics import GeospatialSupport
from dmm.metric.metric_base import MetricBase
from dmm.metric.sklearn_metric import SklearnMetric

logger = logging.getLogger(__name__)

DMM_ME_RESERVED_MISSING = "DMM_ME_RESERVED_MISSING"


@dataclass
class MetricEvaluatorData:
    """
    Helper data class containing the metric and additional information used in the metric evaluator
    """

    metric_name: str
    metric: Union[MetricBase, SklearnMetric]
    segment: Optional[str] = None


class MetricEvaluatorStats:
    """
    This object contains stats about the metric evaluator.
    """

    def __init__(self):
        self.total_rows = 0
        self.nr_calls_to_score = 0
        self.nr_calls_to_reduce = 0

    def __str__(self):
        return "total rows: {}, score calls: {}, reduce calls: {}".format(
            self.total_rows, self.nr_calls_to_score, self.nr_calls_to_reduce
        )


class MetricEvaluatorBase:
    def __init__(self, metric: Union[str, MetricBase]):
        self._metrics = [
            MetricEvaluatorData(metric_name=metric.name, metric=metric)
            for metric in self._validate_and_convert_metrics(metric)
        ]
        self._stats = MetricEvaluatorStats()

    def reset_stats(self) -> None:
        """
        Reset the metric evaluator stats
        """
        self._stats = MetricEvaluatorStats()

    def stats(self) -> MetricEvaluatorStats:
        """
        Return MetricEvaluatorStats object with the current stats
        :return: MetricEvaluatorStats
        """
        return self._stats

    def fit(self, data: pd.DataFrame) -> None:
        for me_data in self._metrics:
            me_data.metric.fit(data)

    @staticmethod
    def _validate_and_convert_metrics(
        metric: Union[str, MetricBase],
    ) -> List[MetricBase]:
        if not metric:
            raise ValueError("No metric(s) provided!")
        metrics = metric if isinstance(metric, list) else [metric]
        after_sklearn_conversion = []
        for metric in metrics:
            if metric is None:
                raise ValueError(
                    "A metric object in the list of metrics has a None value"
                )
            elif isinstance(metric, str):
                after_sklearn_conversion.append(SklearnMetric(metric))
            elif isinstance(metric, MetricBase):
                after_sklearn_conversion.append(metric)
            else:
                raise ValueError(
                    "One of the metrics provided is not based on MetricBase and is not an SKLearn metric"
                )
        return after_sklearn_conversion

    def _reduce_bucket_metric(
        self, bucket_metric_parts: Dict[str, List[float]]
    ) -> Dict[str, float]:
        """
        :param bucket_metric_parts: Bucket to list of values mapping to be reduced.
        :return: Dict of metric name: reduced value
        """
        reduced_values = {}
        for me_data in self._metrics:
            metric_name = me_data.metric_name
            metric = me_data.metric

            # skip reduce if no values to reduce
            if not bucket_metric_parts[metric_name]:
                reduced_values[metric_name] = None
                continue

            reduced_values[metric_name] = metric.reduce_func()(
                bucket_metric_parts[metric_name]
            )
            self._stats.nr_calls_to_reduce += 1
        return reduced_values


class MetricEvaluator(MetricEvaluatorBase):
    """
    Evaluate a Model Metric using training data and scoring data. This class is
    used to "stream" data through the metric object and generate the metric values.
    """

    def __init__(
        self,
        metric: Union[str, MetricBase, List[str], List[MetricBase]],
        source: DataSourceBase,
        time_bucket: TimeBucket,
        prediction_col: str = ColumnName.PREDICTIONS,
        actuals_col: str = ColumnName.ACTUALS,
        timestamp_col: str = ColumnName.TIMESTAMP,
        filter_actuals: bool = False,
        filter_predictions: bool = False,
        filter_scoring_data: bool = False,
        segment_attribute: str = None,
        segment_value: Union[str, List[str]] = None,
    ):
        """
        Initialize the MetricEvaluator framework.
        :param metric: A single metric or a list of metrics. Metrics need to be based on ModelMetric class or a string
        representing a name of an SKLearn metric.
        :param source: A data source object that will be usd to get the data in chunks
        :param time_bucket: The time bucket size to use for evaluating metrics
        :param prediction_col: The name of the prediction column
        :param actuals_col: The name of the actuals column
        :param timestamp_col: The name of the timestamp column
        :param filter_actuals: whether the metric evaluator removes missing actuals values before scoring.
        :param filter_predictions: whether the metric evaluator removes missing predictions values before scoring.
        :param filter_scoring_data: whether the metric evaluator removes missing scoring values before scoring.
        :param segment_attribute The name of the column with segment values
        :param segment_value A single value or a list of values of the segment attribute to segment on
        """
        super().__init__(metric)
        self._metrics = [
            MetricEvaluatorData(metric_name=metric.name, metric=metric)
            for metric in self._validate_and_convert_metrics(metric)
        ]
        self._data_source = source
        if self._data_source is None:
            raise ConflictError("Can not evaluate a metric without a data source")

        self._time_bucket = time_bucket
        self._prediction_col = prediction_col
        self._actuals_col = actuals_col
        self._timestamp_col = timestamp_col
        self._groups_to_filter = self._get_groups_to_filter(
            filter_actuals, filter_predictions, filter_scoring_data
        )
        self._segment_attribute = segment_attribute
        self._segment_values = segment_value
        if self._segment_values and not self._segment_attribute:
            raise ConflictError(
                "Segment attribute must be specified when segment value is specified"
            )
        if isinstance(self._segment_values, str):
            self._segment_values = [self._segment_values]

        # handle the missing segment value scenario
        if self._segment_values and "" in self._segment_values:
            self._segment_values = [
                DMM_ME_RESERVED_MISSING if seg_val == "" else seg_val
                for seg_val in self._segment_values
            ]

        if self._segment_attribute:
            seg_metrics = []  # metrics broken down into segments
            for me_data in self._metrics:
                metric = me_data.metric
                metric_name = me_data.metric_name
                for segment_value in self._segment_values:
                    seg_metric_name = (
                        metric_name + f" [{segment_value}]"
                        if segment_value != DMM_ME_RESERVED_MISSING
                        else metric_name + f" [missing]"
                    )
                    _me_data = MetricEvaluatorData(
                        metric_name=seg_metric_name,
                        metric=metric,
                        segment=segment_value,
                    )
                    seg_metrics.append(_me_data)
            self._metrics = seg_metrics

    def _run_score(self, chunk_of_data: pd.DataFrame) -> Dict[str, float]:
        scored_values = {}
        for me_data in self._metrics:
            metric_name = me_data.metric_name
            metric = me_data.metric
            segment = me_data.segment

            if segment:
                metric_data = chunk_of_data.copy().loc[
                    chunk_of_data[self._segment_attribute] == segment
                ]
            else:
                metric_data = chunk_of_data

            if metric_data.empty:
                continue

            scored_values[metric_name] = metric.score(
                predictions=(
                    self._get_predictions(metric_data)
                    if metric.need_predictions()
                    else None
                ),
                actuals=(
                    self._get_actuals(metric_data) if metric.need_actuals() else None
                ),
                scoring_data=(
                    self._get_scoring_data(metric_data)
                    if metric.need_scoring_data()
                    else None
                ),
            )
            self._stats.nr_calls_to_score += 1
        return scored_values

    def _get_data_chunk(self) -> Tuple[Union[pd.DataFrame, None], int, bool]:
        done = False
        chunk_of_data, time_bucket_id = self._data_source.get_data()

        if chunk_of_data is None:
            done = True
            return chunk_of_data, time_bucket_id, done

        if len(chunk_of_data) > self._data_source.max_rows:
            raise ConflictError("Chunk of data has too many rows")

        if self._segment_attribute:
            if self._segment_attribute not in chunk_of_data:
                raise ConflictError(
                    f"Segment attribute: {self._segment_attribute} not found in exported data"
                )
            if DMM_ME_RESERVED_MISSING in self._segment_values:
                chunk_of_data.fillna(DMM_ME_RESERVED_MISSING, inplace=True)
            chunk_of_data = chunk_of_data.loc[
                chunk_of_data[self._segment_attribute].isin(self._segment_values)
            ]

        self._stats.total_rows += len(chunk_of_data)
        return chunk_of_data, time_bucket_id, done

    def _validate_data_chunk(
        self, data_chunk: pd.DataFrame
    ) -> Tuple[pd.DataFrame, bool]:
        is_valid = True
        for me_data in self._metrics:
            metric_name = me_data.metric_name
            metric = me_data.metric

            if metric.need_predictions() and self._prediction_col not in data_chunk:
                logger.warning(
                    f"Metric {metric_name} requires predictions, but data chunk is missing column "
                    f"'{self._prediction_col}'"
                )
                is_valid = False
                return data_chunk, is_valid
            if metric.need_actuals() and self._actuals_col not in data_chunk:
                logger.warning(
                    f"Metric {metric_name} requires actuals, but data chunk is missing column "
                    f"'{self._actuals_col}'"
                )
                is_valid = False
                return data_chunk, is_valid
        if self._groups_to_filter:
            data_chunk = self._drop_missing_values_from_data_chunk(data_chunk)
        return data_chunk, is_valid

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

        if (
            self._actuals_col in data_chunk
            and DataGroups.ACTUALS in self._groups_to_filter
        ):
            data_chunk = data_chunk.dropna(subset=[self._actuals_col])

        if DataGroups.SCORING in self._groups_to_filter:
            subset = [
                col_name
                for col_name in data_chunk.columns
                if col_name not in [self._actuals_col, self._prediction_col]
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
                self._actuals_col,
                self._prediction_col,
            ],
            errors="ignore",
        )
        _chunk_of_data = _chunk_of_data.rename(
            {self._timestamp_col: ColumnName.DMM_RESERVED_TS}, axis=1, errors="ignore"
        )
        return _chunk_of_data

    def _get_predictions(self, chunk_of_data: pd.DataFrame) -> np.ndarray:
        predictions = (
            chunk_of_data[self._prediction_col].to_numpy()
            if self._prediction_col in chunk_of_data
            else None
        )
        return predictions

    def _get_actuals(self, chunk_of_data: pd.DataFrame) -> np.ndarray:
        actuals = (
            chunk_of_data[self._actuals_col].to_numpy()
            if self._actuals_col in chunk_of_data
            else None
        )
        return actuals

    @staticmethod
    def _get_groups_to_filter(
        filter_actuals: bool, filter_predictions: bool, filter_scoring_data: bool
    ) -> List[DataGroups]:
        groups_to_filter = []
        if filter_predictions:
            groups_to_filter.append(DataGroups.PREDICTIONS)
        if filter_actuals:
            groups_to_filter.append(DataGroups.ACTUALS)
        if filter_scoring_data:
            groups_to_filter.append(DataGroups.SCORING)
        return groups_to_filter

    def score(self) -> pd.DataFrame:
        """
        Steps to evaluate a metric
        1. Get Data from source
        2. Check that data is within the requested time window
        3. Chunk data into max_rows per metric and into time buckets
        4. Feed data to the metric transform
        5. Reduce transform results into the necessary time buckets
        6. Return Dataframe where there is a column per metric and a row per time bucket
        :return: a Dataframe with a row per time bucket in the data. For each time bucket there will be
                 the value of the metric, number of samples used to calculate the metric and the timestamp
        """
        self._data_source.init(self._time_bucket)

        done = False
        prev_time_bucket_id = None
        time_bucket_metric_nr_samples = 0
        time_bucket_timestamp = None

        time_bucket_scores = {me_data.metric_name: [] for me_data in self._metrics}
        final_scores = {me_data.metric_name: [] for me_data in self._metrics}

        output_nr_samples_list = []
        output_bucket_timestamp_list = []

        is_geo = bool(
            self._metrics and getattr(self._metrics[0].metric, "_is_geospatial", False)
        )
        geo_attr = "geometry" if is_geo else None
        geo = GeospatialSupport(
            geo_attr=geo_attr,
            timestamp_col=self._timestamp_col,
            metric_name=self._metrics[0].metric_name if self._metrics else "metric",
        )
        while not done:
            data_chunk, time_bucket_id, done = self._get_data_chunk()

            # Moved to a new time bucket so calling reduce on the previous values
            if time_bucket_id != prev_time_bucket_id:
                # We don't reduce in the first time we get data (as prev is None and id is not None)
                if prev_time_bucket_id is not None:
                    # Moved to a new time bucket (or done).. need to reduce
                    reduced_values = self._reduce_bucket_metric(time_bucket_scores)
                    if reduced_values:
                        output_nr_samples_list.append(time_bucket_metric_nr_samples)
                        output_bucket_timestamp_list.append(time_bucket_timestamp)
                    for metric, value in reduced_values.items():
                        final_scores[metric].append(value)
                        time_bucket_scores[metric].clear()
                    geo.reduce_bucket(time_bucket_timestamp)
                time_bucket_metric_nr_samples = 0
                prev_time_bucket_id = time_bucket_id
            # Running the score and keeping the value until it is time to reduce
            # If we are done - we will not call the transform.
            if done:
                continue

            data_chunk, is_valid = self._validate_data_chunk(data_chunk)
            if not is_valid:
                logger.warning(
                    "data chunk does not require all the necessary columns, skipping scoring..."
                )
                continue
            if data_chunk.index.size == 0:
                logger.warning("data chunk is empty, skipping scoring...")
                continue

            geo.ingest_chunk(data_chunk)

            for metric_name, value in self._run_score(data_chunk).items():
                time_bucket_scores[metric_name].append(value)
            time_bucket_metric_nr_samples += data_chunk.index.size

            # corner case when TIMESTAMP column is duplicated
            if isinstance(data_chunk[self._timestamp_col], pd.DataFrame):
                column_selector = ~data_chunk[self._timestamp_col].columns.duplicated()
                time_bucket_timestamp = (
                    data_chunk[self._timestamp_col]
                    .loc[:, column_selector]
                    .squeeze()
                    .iat[0]
                )
            else:
                time_bucket_timestamp = data_chunk[self._timestamp_col].iat[0]

        result_df = pd.DataFrame(
            {
                ColumnName.TIMESTAMP: output_bucket_timestamp_list,
                ColumnName.NR_SAMPLES: output_nr_samples_list,
                **final_scores,
            }
        )
        result_df.dropna(subset=list(final_scores.keys()), how="all", inplace=True)
        if is_geo:
            geo_df = geo.finalize(result_df)
            return geo_df
        return result_df
