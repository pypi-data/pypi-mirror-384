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
from typing import List, Tuple, Union

import numpy as np
import pandas as pd

from dmm.constants import ColumnName, DataGroups
from dmm.custom_metric import SingleMetricResult
from dmm.data_source.data_source_base import DataSourceBase
from dmm.exceptions import ConflictError
from dmm.metric.metric_base import MetricBase

logger = logging.getLogger(__name__)


class IndividualMetricEvaluatorStats:
    """
    This object contains stats about the individual metric evaluator.
    """

    def __init__(self):
        self.total_rows = 0
        self.total_scored_rows = 0

    def __str__(self):
        return "total rows: {}, total scored rows calls: {}".format(
            self.total_rows, self.total_scored_rows
        )


class IndividualMetricEvaluatorBase:
    def __init__(self, metric: MetricBase):
        self._metric = metric
        self._stats = IndividualMetricEvaluatorStats()

    def reset_stats(self) -> None:
        """
        Reset the metric evaluator stats
        """
        self._stats = IndividualMetricEvaluatorStats()

    def stats(self) -> IndividualMetricEvaluatorStats:
        """
        Return IndividualMetricEvaluatorStats object with the current stats
        :return: IndividualMetricEvaluatorStats
        """
        return self._stats

    def fit(self, data: pd.DataFrame) -> None:
        self._metric.fit(data)


class IndividualMetricEvaluator(IndividualMetricEvaluatorBase):
    """
    Evaluate an individual metric without data aggregation.
    Perform metric calculations on all exported data, return a list of individual results.
    To use this evaluator with custom metric, it is necessary to provide score method that
    contains, among others, the following parameters: 'timestamps' and 'association_ids'.
    """

    def __init__(
        self,
        metric: MetricBase,
        source: DataSourceBase,
        prediction_col: str = ColumnName.PREDICTIONS,
        actuals_col: str = ColumnName.ACTUALS,
        timestamp_col: str = ColumnName.TIMESTAMP,
        association_id_col: str = ColumnName.ASSOCIATION_ID_COLUMN,
        filter_actuals: bool = False,
        filter_predictions: bool = False,
        filter_scoring_data: bool = False,
    ):
        """
        Initialize the IndividualMetricEvaluator framework.
        :param metric: A single metric based on MetricBase class,
        :param source: A data source object that will be usd to get the data in chunks
        :param prediction_col: The name of the prediction column
        :param actuals_col: The name of the actuals column
        :parma association_id_col: The name of the association_id column
        :param timestamp_col: The name of the timestamp column
        :param filter_actuals: Whether the metric evaluator removes missing actuals values before scoring
        :param filter_predictions: Whether the metric evaluator removes missing predictions values before scoring
        :param filter_scoring_data: Whether the metric evaluator removes missing scoring values before scoring
        """
        super().__init__(metric)
        self._metric = metric
        self._data_source = source
        if self._data_source is None:
            raise ConflictError("Can not evaluate a metric without a data source")

        self._prediction_col = prediction_col
        self._actuals_col = actuals_col
        self._timestamp_col = timestamp_col
        self._association_id_col = association_id_col
        self._groups_to_filter = self._get_groups_to_filter(
            filter_actuals, filter_predictions, filter_scoring_data
        )

    def _get_all_data(self) -> Union[pd.DataFrame, None]:
        """
        Export all available data for a given time window in a data source.
        """
        data = self._data_source.get_all_data()

        if data is None:
            return data

        self._stats.total_rows += len(data)
        return data

    def _validate_exported_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
        is_valid = True
        if self._metric.need_predictions() and self._prediction_col not in data:
            logger.warning(
                f"Metric {self._metric.name} requires predictions, but data is missing column "
                f"'{self._prediction_col}'"
            )
            is_valid = False
            return data, is_valid
        if self._metric.need_actuals() and self._actuals_col not in data:
            logger.warning(
                f"Metric {self._metric.name} requires actuals, but data is missing column "
                f"'{self._actuals_col}'"
            )
            is_valid = False
            return data, is_valid
        if self._groups_to_filter:
            data = self._drop_missing_values_from_data_chunk(data)
        return data, is_valid

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

    @staticmethod
    def _get_required_column(name: str, data: pd.DataFrame) -> np.ndarray:
        if name in data:
            required_column = data[name].to_numpy()
        else:
            raise ValueError(
                f"A required {name} column was not found in the exported data"
            )
        return required_column

    @staticmethod
    def _get_optional_column(name: str, data: pd.DataFrame) -> np.ndarray:
        optional_column = data[name].to_numpy() if name in data else np.array([])
        return optional_column

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

    def _score_metric(self, data: pd.DataFrame) -> List[SingleMetricResult]:
        _predictions = (
            self._get_required_column(self._prediction_col, data)
            if self._metric.need_predictions()
            else None
        )
        _actuals = (
            self._get_required_column(self._actuals_col, data)
            if self._metric.need_actuals()
            else None
        )
        _scoring_data = (
            self._get_scoring_data(data) if self._metric.need_scoring_data() else None
        )
        _timestamps = self._get_required_column(self._timestamp_col, data)

        _association_ids = self._get_optional_column(self._association_id_col, data)

        metric_results = self._metric.score(
            predictions=_predictions,
            actuals=_actuals,
            scoring_data=_scoring_data,
            timestamps=_timestamps,
            association_ids=_association_ids,
        )

        if not isinstance(metric_results, list):
            raise ConflictError(
                "The selected metric does not support 'IndividualMetricEvaluator', "
                "to use it, return a list of 'SingleMetricResult' from your custom metric score method"
            )
        self._stats.total_scored_rows += len(metric_results)
        return metric_results

    def score(self) -> List[SingleMetricResult]:
        """
        Score each prediction data row separately, return all results at once.
        """
        data = self._get_all_data()
        if data is None:
            logger.warning("no data found for the selected export period...")
            return []

        data, is_valid = self._validate_exported_data(data)
        if data.index.size == 0:
            logger.warning("exported data is empty, skipping scoring...")
            return []
        if not is_valid:
            logger.warning(
                "exported data does not require all the necessary columns, skipping scoring..."
            )
            return []

        metric_results = self._score_metric(data)
        return metric_results
