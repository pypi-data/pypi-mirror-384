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
from __future__ import annotations

import datetime
import errno
import logging
import os
import tempfile
from typing import Callable, Generator, Iterator, List, Optional

import pandas as pd
import pytz
import requests
from datarobot.errors import AsyncProcessUnsuccessfulError
from dateutil.parser import parse

from dmm.constants import ColumnName, ExportType, TimeBucket
from dmm.data_source.data_source_base import DataSourceBase
from dmm.data_source.datarobot.deployment import (
    Deployment,
    DeploymentType,
    deployment_factory,
)
from dmm.data_source.datarobot.export_provider import (
    ExportProvider,
    get_export_provider,
)
from dmm.datarobot_api_client import (
    DataRobotApiClient,
    DataRobotClient,
    api_client_factory,
)
from dmm.exceptions import (
    ConflictError,
    DataExportJobError,
    DataRobotAPIError,
    DRSourceNotSupported,
)
from dmm.time_bucket import (
    check_if_in_same_time_bucket,
    check_if_in_same_time_bucket_vectorized,
)
from dmm.utils import hour_rounder_down, hour_rounder_up

logger = logging.getLogger(__name__)


class DataRobotSource(DataSourceBase):
    """
    A DataSourceBase that talks with DataRobot API. Internally, it performs relevant exports and fetches the data.

    Requested data may not fit into the memory, this source tries to fetch as relatively small chunks of data and be
    as lazy as possible.
    """

    def __init__(
        self,
        deployment_id: str,
        start: datetime.datetime,
        end: datetime.datetime,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        client: Optional[DataRobotClient] = None,
        model_id: str = None,
        max_rows: int = 10000,
        delete_exports: bool = False,
        use_cache: bool = False,
        actuals_with_matched_predictions: bool = True,
        needs_actuals: bool = True,
    ):
        super().__init__(max_rows)
        if max_rows <= 0:
            raise ValueError(f"max_rows must be > 0, got {max_rows}")

        self._deployment_id = deployment_id
        self._start = start
        self._end = end
        self._model_id = model_id
        self._delete_exports = delete_exports
        self._use_cache = use_cache
        self._current_chunk_id = 0
        self._prev_chunk_datetime = None
        self._actuals_caches = {}
        self._actuals_with_matched_predictions = actuals_with_matched_predictions
        self._needs_actuals = needs_actuals

        self._api = api_client_factory(client=client, token=token, url=base_url)
        self._deployment = deployment_factory(
            api=self._api, deployment_id=deployment_id
        )

        self._prediction_data_provider = self._get_prediction_data_provider()
        self._actuals_data_provider = self._get_actuals_data_provider()
        self._association_id = self._api.get_association_id(deployment_id)

    def init(self, time_bucket: TimeBucket) -> DataRobotSource:
        """
        Init function will be called prior to calling getting data by the Metric Evaluator runner.

        Parameters
        ----------
        time_bucket: TimeBucket
        """
        self._time_bucket = time_bucket
        self.reset()
        return self

    def reset(self) -> None:
        """
        Resets the current state of data exports to the beginning of the data.
        """
        self._prediction_data_provider = self._get_prediction_data_provider()
        self._actuals_data_provider = self._get_actuals_data_provider()
        self._actuals_caches = {}

    def get_deployment(self) -> Deployment:
        """
        Gets the deployment object that was instantiated during construction.

        This avoids fetching the data a second time when a reference to the deployment is needed.

        :return:
            Deployment: deployment object
        """
        return self._deployment

    def get_actuals_data(
        self, return_original_column_names: bool = False
    ) -> (pd.DataFrame, int):
        """
        Method to return a chunk of actuals data that can be sent to a metric object to be transformed.
        :return:
            - DataFrame: if there is more data to process, or None
            - int: ID of the time bucket
        """
        actuals_df, chunk_id = self._actuals_data_provider.get_data(
            return_original_column_names
        )
        return actuals_df, chunk_id

    def get_all_actuals_data(self) -> pd.DataFrame:
        """
        Returns all actuals data available for that source object in a single DataFrame.
        :return:
            DataFrame: Actuals data for all chunks.
        """
        return self._get_all(self.get_actuals_data)

    def get_prediction_data(self) -> (pd.DataFrame, int):
        """
        Method to return a chunk of prediction data that can be sent to a metric object to be transformed.
        :return:
            - DataFrame: if there is more data to process, or None
            - int: ID of the time bucket
        """
        prediction_df, chunk_id = self._prediction_data_provider.get_data()
        return prediction_df, chunk_id

    def get_all_prediction_data(self) -> pd.DataFrame:
        """
        Returns all prediction data available for that source object in a single DataFrame.
        :return:
            DataFrame: Prediction data for all chunks.
        """
        return self._get_all(self.get_prediction_data)

    def get_training_data(self) -> pd.DataFrame:
        """
        Method to return training data that can be sent to a metric object to be transformed.
        :return:
            DataFrame: if training data found otherwise None
        """
        training_data_provider = self._get_training_data_provider()
        training_df = training_data_provider.get_data()
        return training_df

    def get_data(self) -> (pd.DataFrame, int):
        """
        Method to return a chunk of data that can be sent to a metric object to be transformed.
        :return:
            - DataFrame: if there is more data to process, or None
            - int: ID of the time bucket
        """
        if self._prev_chunk_datetime is None and self._current_chunk_id != -1:
            self.reset()

        prediction_df, chunk_id = self._prediction_data_provider.get_data()
        if prediction_df is None:
            logger.info("data export for the given time range completed")
            return prediction_df, chunk_id

        last_prediction_timestamp = (
            self._prediction_data_provider.get_last_prediction_timestamp(prediction_df)
        )
        prediction_chunk_ts = self._prediction_data_provider.get_chunk_timestamp()
        prediction_df = self._format_prediction_df(prediction_df)

        actuals_df = pd.DataFrame()
        if self._association_id and self._needs_actuals:
            actuals_export_start = hour_rounder_down(prediction_chunk_ts)
            actuals_export_end = hour_rounder_up(last_prediction_timestamp)
            self._remove_unwanted_actuals_caches(actuals_export_start)

            last_actuals_ts = self._get_last_actuals_timestamp_from_caches()
            # fetch new actuals data
            if not last_actuals_ts or actuals_export_end > last_actuals_ts:
                actuals_export_start = (
                    last_actuals_ts if last_actuals_ts else actuals_export_start
                )
                actuals_data_provider = ActualsDataExportProvider(
                    api=self._api,
                    deployment_id=self._deployment_id,
                    start=actuals_export_start,
                    end=actuals_export_end,
                    max_rows=self.max_rows,
                    delete_exports=self._delete_exports,
                    use_cache=self._use_cache,
                )
                actuals_df = self._get_corresponding_actuals(actuals_data_provider)
                actuals_df_from_caches = self._get_actuals_df_from_caches()
                if not actuals_df.empty:
                    self._update_actuals_caches(actuals_df)
                actuals_df = pd.concat([actuals_df, actuals_df_from_caches])

            # get actuals data from the caches
            else:
                actuals_df = self._get_actuals_df_from_caches()

        df = (
            pd.merge(
                prediction_df,
                self._format_actuals_df_before_merge(actuals_df),
                on=ColumnName.ASSOCIATION_ID_COLUMN,
                how="left",
            )
            if not actuals_df.empty
            else prediction_df
        )
        self._update_chunk_info(prediction_chunk_ts)
        return df, self._current_chunk_id

    def get_all_data(self) -> pd.DataFrame:
        """
        Returns all combined data available for that source object in a single DataFrame.
        :return:
            DataFrame: Prediction data for all chunks.
        """
        return self._get_all(self.get_data)

    def _get_actuals_data_provider(self) -> ActualsDataExportProvider:
        """
        Retrieves a new instance of the ActualsDataExportProvider class.
        """
        return ActualsDataExportProvider(
            api=self._api,
            deployment_id=self._deployment_id,
            start=self._start,
            end=self._end,
            model_id=self._model_id,
            time_bucket=self._time_bucket,
            max_rows=self.max_rows,
            delete_exports=self._delete_exports,
            use_cache=self._use_cache,
            only_matched_predictions=self._actuals_with_matched_predictions,
        )

    def _get_prediction_data_provider(self) -> PredictionDataExportProvider:
        """
        Retrieves a new instance of the PredictionDataExportProvider class.
        """
        return PredictionDataExportProvider(
            api=self._api,
            deployment_id=self._deployment_id,
            start=self._start,
            end=self._end,
            model_id=self._model_id,
            time_bucket=self.time_bucket,
            max_rows=self.max_rows,
            delete_exports=self._delete_exports,
            use_cache=self._use_cache,
        )

    def _get_training_data_provider(self) -> TrainingDataExportProvider:
        """
        Retrieves a new instance of the TrainingDataExportProvider class.
        """
        return TrainingDataExportProvider(
            api=self._api,
            deployment_id=self._deployment_id,
            model_id=self._model_id,
        )

    def _update_chunk_info(self, chunk_dt: datetime.datetime) -> None:
        """
        Source must keep track of a small piece of state to differentiate time bucketed chunks.
        This method updates this state.

        Parameters
        ----------
        chunk_dt: datetime
            datetime of any event within the chunk
        """
        if self._prev_chunk_datetime and not check_if_in_same_time_bucket(
            self._prev_chunk_datetime, chunk_dt, self._time_bucket
        ):
            self._current_chunk_id += 1
        self._prev_chunk_datetime = chunk_dt

    @staticmethod
    def _get_corresponding_actuals(
        actuals_data_provider: ActualsDataExportProvider,
    ) -> pd.DataFrame:
        """
        Retrieves corresponding actuals for the time range from prediction data export.

        Parameters
        ----------
        actuals_data_provider: ActualsDataExportProvider
        """
        chunk_id = 0
        chunks = []
        while chunk_id != -1:
            actuals_df, chunk_id = actuals_data_provider.get_data()
            if actuals_df is not None:
                chunks.append(actuals_df)
        if chunks:
            actuals_df = pd.concat(chunks)
            return actuals_df
        else:
            return pd.DataFrame()

    def _format_prediction_df(self, pred_df: pd.DataFrame) -> pd.DataFrame:
        """
        Formats data from prediction data export, before merging with actuals.
        Renames the columns to standardize the output names.

        Parameters
        ----------
        pred_df: pd.DataFrame
        """
        rename_columns = {
            ColumnName.DR_TIMESTAMP_COLUMN: ColumnName.TIMESTAMP,
        }
        association_id = self._api.get_association_id(self._deployment_id)

        if association_id and (ColumnName.ACTUALS in pred_df.columns):
            logger.warning(
                f"Predictions data contains a reserved column name: '{ColumnName.ACTUALS}'"
                f", adding the prefix 'DMM_RESTRICTED_NAME' to it."
            )
            rename_columns.update(
                {ColumnName.ACTUALS: "DMM_RESERVED_NAME_" + ColumnName.ACTUALS}
            )

        if association_id and (association_id in pred_df.columns):
            rename_columns.update({association_id: ColumnName.ASSOCIATION_ID_COLUMN})
        elif association_id and (
            ColumnName.INTERNAL_ASSOCIATION_ID_COLUMN_NAME in pred_df.columns
        ):
            rename_columns.update(
                {
                    ColumnName.INTERNAL_ASSOCIATION_ID_COLUMN_NAME: ColumnName.ASSOCIATION_ID_COLUMN
                }
            )

        if ColumnName.PREDICTIONS in pred_df.columns:
            logger.warning(
                f"Predictions data contains a reserved column name: '{ColumnName.PREDICTIONS}'"
                f", adding the prefix 'DMM_RESTRICTED_NAME' to it."
            )
            rename_columns.update(
                {ColumnName.PREDICTIONS: "DMM_RESERVED_NAME_" + ColumnName.PREDICTIONS}
            )

        if self._deployment.type == DeploymentType.REGRESSION:
            rename_columns.update(
                {ColumnName.DR_PREDICTION_COLUMN: ColumnName.PREDICTIONS}
            )
        elif self._deployment.type == DeploymentType.BINARY_CLASSIFICATION:
            positive_class_column = f"{ColumnName.DR_PREDICTION_COLUMN}_{self._deployment.positive_class_label}"
            if "-" in positive_class_column:
                positive_class_column = positive_class_column.replace("-", "_")
            negative_class_column = f"{ColumnName.DR_PREDICTION_COLUMN}_{self._deployment.negative_class_label}"
            if "-" in negative_class_column:
                negative_class_column = negative_class_column.replace("-", "_")

            # drop predictions from negative class
            pred_df = pred_df.drop(columns=[negative_class_column], axis=1)

            # apply prediction threshold
            pred_df[ColumnName.PREDICTED_CLASS] = (
                pred_df[positive_class_column] >= self._deployment.prediction_threshold
            )
            pred_df[ColumnName.PREDICTED_CLASS] = pred_df[
                ColumnName.PREDICTED_CLASS
            ].map(
                {
                    True: self._deployment.positive_class_label,
                    False: self._deployment.negative_class_label,
                }
            )
            rename_columns.update({positive_class_column: ColumnName.PREDICTIONS})
        elif self._deployment.type == DeploymentType.MULTICLASS:
            for label in self._deployment.class_labels:
                class_column = f"{ColumnName.DR_PREDICTION_COLUMN}_{label}"
                rename_columns.update(
                    {class_column: f"{ColumnName.PREDICTIONS}_{label}"}
                )
        elif self._deployment.type == DeploymentType.TEXT_GENERATION:
            rename_columns.update(
                {ColumnName.DR_PREDICTION_COLUMN: ColumnName.PREDICTIONS}
            )
        else:
            raise DataRobotAPIError(
                f"Unsupported deployment type {self._deployment.type}"
            )

        pred_df = pred_df.rename(rename_columns, axis=1)
        return pred_df

    def _format_actuals_df_before_merge(self, actuals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Formats data from actuals data export, before merging with prediction data.
        Drops columns to avoid duplication

        Parameters
        ----------
        actuals_df: pd.DataFrame
        """
        columns_to_drop = [ColumnName.PREDICTIONS, ColumnName.TIMESTAMP]
        # for binary classification, drop the predicted class to avoid columns with the same content
        if self._deployment.type == DeploymentType.BINARY_CLASSIFICATION:
            columns_to_drop.append(ColumnName.PREDICTED_CLASS)
        actuals_df = actuals_df.drop(columns_to_drop, axis=1)
        return actuals_df

    def _remove_unwanted_actuals_caches(self, start_dt: datetime.datetime) -> None:
        """
        Removes actuals from caches, that are no longer needed.

        Parameters
        ----------
        start_dt: datetime
        """
        unwanted = [
            actuals_dt
            for actuals_dt in self._actuals_caches
            if parse(actuals_dt) < start_dt
        ]
        for unwanted_key in unwanted:
            del self._actuals_caches[unwanted_key]

    def _update_actuals_caches(self, actuals_df: pd.DataFrame) -> None:
        """
        Update the actuals cache with the newly exported actuals.
        Caches are stored like actuals in Postgres - aggregated over an hour.

        Parameters
        ----------
        actuals_df: pd.DataFrame
        """
        grouped_actuals = actuals_df.groupby(ColumnName.TIMESTAMP)
        for group, df in grouped_actuals:
            self._actuals_caches[group] = df

    def _get_actuals_df_from_caches(self) -> pd.DataFrame:
        """
        Returns all cached actuals in the form of the concatenated pandas data frame.
        If there are no actuals caches, returns an empty pandas data frame.
        """
        if self._actuals_caches:
            return pd.concat(self._actuals_caches.values())
        else:
            return pd.DataFrame()

    def _get_last_actuals_timestamp_from_caches(self) -> Optional[datetime.datetime]:
        """
        Returns last timestamp from caches, which means an hour which is the end of the hourly interval.
        """
        if self._actuals_caches:
            last_hourly_start = parse(list(self._actuals_caches)[-1])
            last_hourly_end = last_hourly_start + datetime.timedelta(hours=1)
            return last_hourly_end
        else:
            return None

    @staticmethod
    def _get_all(provider: Callable[[], (pd.DataFrame, int)]) -> pd.DataFrame:
        """
        Utility method that polls provider (matches get_prediction_data / get_actuals_data signature) and concatenates
        all available frames.
        """
        result, chunk_id = provider()
        while chunk_id != -1:
            df, chunk_id = provider()
            if df is not None:
                result = pd.concat([result, df])
        return result


class BatchDataRobotSource(DataSourceBase):
    def __init__(
        self,
        deployment_id: str,
        batch_ids: List[str],
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        client: Optional[DataRobotClient] = None,
        model_id: str = None,
        max_rows: int = 10000,
        delete_exports: bool = False,
        actuals_with_matched_predictions: bool = True,
    ):
        super().__init__(max_rows)
        if max_rows <= 0:
            raise ValueError(f"max_rows must be > 0, got {max_rows}")

        self._deployment_id = deployment_id
        self._model_id = model_id
        self._current_chunk_id = 0
        self._prev_chunk_batch_id = None
        self._batch_ids = batch_ids

        self._api = api_client_factory(client=client, url=base_url, token=token)
        self._deployment = deployment_factory(
            api=self._api, deployment_id=deployment_id
        )
        self._start = self._deployment.created_at
        self._end = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        self._delete_exports = delete_exports
        self._prediction_data_provider = self._get_prediction_data_provider()
        self._actuals_with_matched_predictions = actuals_with_matched_predictions

    def init(self, time_bucket: TimeBucket):
        pass

    def reset(self):
        self._prediction_data_provider = self._get_prediction_data_provider()

    def get_data(self) -> (pd.DataFrame, int):
        """
        Method to return a chunk of data that can be sent to a metric object to be transformed.
        :return:
            - DataFrame: if there is more data to process, or None
            - int: ID of the time bucket
        """
        if self._prev_chunk_batch_id is None and self._current_chunk_id != -1:
            self.reset()

        prediction_df, chunk_id = self._prediction_data_provider.get_data()
        if prediction_df is None:
            logger.info("data export for the given time range completed")
            return prediction_df, chunk_id

        prediction_chunk_batch_id = self._prediction_data_provider.get_chunk_batch_id()
        prediction_df = self._format_prediction_df(prediction_df)

        self._update_chunk_info(prediction_chunk_batch_id)
        return prediction_df, self._current_chunk_id

    def get_prediction_data(self) -> (pd.DataFrame, int):
        """
        Method to return a chunk of prediction data that can be sent to a metric object to be transformed.
        :return:
            - DataFrame: if there is more data to process, or None
            - int: ID of the time bucket
        """
        prediction_df, chunk_id = self._prediction_data_provider.get_data()
        return prediction_df, chunk_id

    def get_all_prediction_data(self) -> pd.DataFrame:
        """
        Returns all prediction data available for that source object in a single DataFrame.
        :return:
            DataFrame: Prediction data for all chunks.
        """
        return self._get_all(self.get_prediction_data)

    def get_training_data(self) -> pd.DataFrame:
        """
        Method to return training data that can be sent to a metric object to be transformed.
        :return:
            DataFrame: if training data found otherwise None
        """
        training_data_provider = self._get_training_data_provider()
        training_df = training_data_provider.get_data()
        return training_df

    def _get_prediction_data_provider(self) -> BatchPredictionDataExportProvider:
        """
        Retrieves a new instance of the PredictionDataExportProvider class.
        """
        return BatchPredictionDataExportProvider(
            api=self._api,
            deployment_id=self._deployment_id,
            start=self._start,
            end=self._end,
            model_id=self._model_id,
            max_rows=self.max_rows,
            batch_ids=self._batch_ids,
            delete_exports=self._delete_exports,
        )

    def _get_training_data_provider(self) -> TrainingDataExportProvider:
        """
        Retrieves a new instance of the TrainingDataExportProvider class.
        """
        return TrainingDataExportProvider(
            api=self._api,
            deployment_id=self._deployment_id,
            model_id=self._model_id,
        )

    def _format_prediction_df(self, pred_df: pd.DataFrame) -> pd.DataFrame:
        """
        Formats data from prediction data export, before merging with actuals.
        Renames the columns to standardize the output names.

        Parameters
        ----------
        pred_df: pd.DataFrame
        """
        rename_columns = {
            ColumnName.DR_TIMESTAMP_COLUMN: ColumnName.TIMESTAMP,
            ColumnName.DR_BATCH_ID_COLUMN: ColumnName.BATCH_ID_COLUMN,
        }

        if self._deployment.type == DeploymentType.REGRESSION:
            prediction_col = ColumnName.DR_PREDICTION_COLUMN
        elif self._deployment.type == DeploymentType.BINARY_CLASSIFICATION:
            positive_class_column = f"{ColumnName.DR_PREDICTION_COLUMN}_{self._deployment.positive_class_label}"
            if "-" in positive_class_column:
                positive_class_column = positive_class_column.replace("-", "_")
            negative_class_column = f"{ColumnName.DR_PREDICTION_COLUMN}_{self._deployment.negative_class_label}"
            if "-" in negative_class_column:
                negative_class_column = negative_class_column.replace("-", "_")

            # drop predictions from negative class
            pred_df = pred_df.drop(columns=[negative_class_column], axis=1)

            # get predictions from positive class
            prediction_col = positive_class_column

            # apply prediction threshold
            pred_df[ColumnName.PREDICTED_CLASS] = (
                pred_df[positive_class_column] >= self._deployment.prediction_threshold
            )
            pred_df[ColumnName.PREDICTED_CLASS] = pred_df[
                ColumnName.PREDICTED_CLASS
            ].map(
                {
                    True: self._deployment.positive_class_label,
                    False: self._deployment.negative_class_label,
                }
            )
        else:
            raise DataRobotAPIError(
                f"Unsupported deployment type {self._deployment.type}"
            )

        rename_columns.update({prediction_col: ColumnName.PREDICTIONS})
        pred_df = pred_df.rename(rename_columns, axis=1)
        return pred_df

    def _update_chunk_info(self, chunk_batch_id: str) -> None:
        """
        Source must keep track of a small piece of state to differentiate time bucketed chunks.
        This method updates this state.

        Parameters
        ----------
        chunk_batch_id: str
            batch_id of any event within the chunk
        """
        if self._prev_chunk_batch_id and self._prev_chunk_batch_id != chunk_batch_id:
            self._current_chunk_id += 1
        self._prev_chunk_batch_id = chunk_batch_id

    @staticmethod
    def _get_all(provider: Callable[[], (pd.DataFrame, int)]) -> pd.DataFrame:
        """
        Utility method that polls provider (matches get_prediction_data signature) and concatenates
        all available frames.
        """
        result, chunk_id = provider()
        while chunk_id != -1:
            df, chunk_id = provider()
            if df is not None:
                result = pd.concat([result, df])
        return result


class DataRobotExportBase:
    """
    The base class for exporting data via DataRobot API in the time bucket chunk manner.
    """

    def __init__(
        self,
        api: DataRobotApiClient,
        deployment_id: str,
        model_id: str | None,
        start: datetime.datetime,
        end: datetime.datetime,
        timestamp_col: str,
        max_rows: int,
        time_bucket: TimeBucket,
        export_type: ExportType,
        delete_exports: bool = False,
        use_cache: bool = False,
        actuals_with_matched_predictions: bool = True,
    ):
        self._api = api
        self._deployment_id = deployment_id
        self._model_id = model_id
        self._deployment = deployment_factory(
            api=self._api, deployment_id=deployment_id
        )
        self._start = start
        self._end = end
        self._time_bucket = time_bucket
        self._max_rows = max_rows
        self._timestamp_col = timestamp_col
        self._export_type = export_type
        self._actuals_with_matched_predictions = actuals_with_matched_predictions
        self._delete_exports = delete_exports
        self._use_cache = use_cache
        if self._use_cache and self._delete_exports:
            raise ConflictError(
                "Data exports cannot be deleted when use_caching is set to True"
            )

        self._export_provider = get_export_provider(
            export_type=self._export_type, api=api
        )
        self._time_bucket_chunks = self._get_time_bucket_chunks()
        self._current_chunk_id = 0
        self._prev_bucket_id = None

    def set_new_export_parameters(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
        time_bucket: TimeBucket,
        max_rows: int,
    ) -> DataRobotExportBase:
        self._start = start
        self._end = end
        self._time_bucket = time_bucket
        self._max_rows = max_rows
        self.reset()
        return self

    def reset(self) -> None:
        self._current_chunk_id = 0
        self._prev_bucket_id = None
        self._time_bucket_chunks = self._get_time_bucket_chunks()

    def _get_time_bucket_chunks(self) -> TimeBucketChunks:
        dataset_ids = None
        if self._use_cache:
            model_id = (
                self._api.get_deployment(self._deployment_id)["model"]["id"]
                if self._model_id is None
                else self._model_id
            )
            data_export = self._api.find_data_export(
                self._deployment_id,
                model_id,
                self._start,
                self._end,
                self._export_type,
                self._actuals_with_matched_predictions,
            )
            dataset_ids = (
                self._export_provider.get_export_dataset_ids(
                    self._deployment_id, data_export
                )
                if data_export
                else None
            )

        if dataset_ids:
            return TimeBucketChunks(
                self._timestamp_col,
                PushBackFrameIterator(
                    iter(
                        DataRobotChunksIteratorFromCache(
                            api=self._api,
                            dataset_ids=dataset_ids,
                            start_dt=self._start,
                            end_dt=self._end,
                            timestamp_column=self._timestamp_col,
                            sort_column=self._timestamp_col,
                            actuals_with_matched_predictions=self._actuals_with_matched_predictions,
                        )
                    )
                ),
            )

        else:
            return TimeBucketChunks(
                self._timestamp_col,
                PushBackFrameIterator(
                    iter(
                        DataRobotChunksIterator(
                            api=self._api,
                            deployment_id=self._deployment_id,
                            model_id=self._model_id,
                            start_dt=self._start,
                            end_dt=self._end,
                            export_provider=self._export_provider,
                            sort_column=self._timestamp_col,
                            delete_exports=self._delete_exports,
                            actuals_with_matched_predictions=self._actuals_with_matched_predictions,
                        )
                    )
                ),
            )

    def _update_chunk_info(self, bucket_id: any):
        """
        Source must keep track of a small piece of state to differentiate time bucketed chunks.
        This method updates this state.

        Parameters
        ----------
        bucket_id: any
            identifier of a chunk (e.g. time bucket timestamp or batch_id)
        """
        if self._prev_bucket_id and not check_if_in_same_time_bucket(
            self._prev_bucket_id, bucket_id, self._time_bucket
        ):
            self._current_chunk_id += 1
        self._prev_bucket_id = bucket_id


class PredictionDataExportProvider(DataRobotExportBase):
    def __init__(
        self,
        api: DataRobotApiClient,
        deployment_id: str,
        start: datetime.datetime,
        end: datetime.datetime,
        model_id: str = None,
        timestamp_col: str = ColumnName.DR_TIMESTAMP_COLUMN,
        max_rows: int = 10000,
        time_bucket: TimeBucket = TimeBucket.ALL,
        delete_exports: bool = False,
        use_cache: bool = False,
    ):
        if max_rows <= 0:
            raise ValueError(f"max_rows must be > 0, got {max_rows}")

        super().__init__(
            api=api,
            deployment_id=deployment_id,
            model_id=model_id,
            start=start,
            end=end,
            timestamp_col=timestamp_col,
            max_rows=max_rows,
            time_bucket=time_bucket,
            export_type=ExportType.PREDICTIONS,
            delete_exports=delete_exports,
            use_cache=use_cache,
        )

    def get_data(self) -> (pd.DataFrame, int):
        """
        Method to return a chunk of prediction data that can be sent to a metric object to be transformed.
        :return:
            - DataFrame: if there is more data to process, or None
            - int: ID of the time bucket
        """
        if self._time_bucket_chunks.finished():
            return None, -1

        chunk_df, chunk_ts = self._time_bucket_chunks.load_time_bucket_chunk(
            time_bucket=self._time_bucket, max_rows=self._max_rows
        )

        self._update_chunk_info(chunk_ts)
        return chunk_df, self._current_chunk_id

    def get_last_prediction_timestamp(
        self, prediction_df: pd.DataFrame
    ) -> datetime.datetime:
        last_timestamp = prediction_df[self._timestamp_col].iloc[-1]
        return parse(last_timestamp)

    def get_chunk_timestamp(self) -> datetime.datetime:
        return self._prev_bucket_id


class DataRobotBatchExportBase:
    """
    The base class for exporting data via DataRobot API in the time bucket chunk manner.
    """

    def __init__(
        self,
        api: DataRobotApiClient,
        deployment_id: str,
        model_id: str | None,
        start: datetime.datetime,
        end: datetime.datetime,
        max_rows: int,
        export_provider: ExportProvider,
        delete_exports: bool,
        actuals_with_matched_predictions: bool = True,
    ):
        self._api = api
        self._deployment_id = deployment_id
        self._model_id = model_id
        self._deployment = deployment_factory(
            api=self._api, deployment_id=deployment_id
        )
        self._start = start
        self._end = end
        self._max_rows = max_rows
        self._export_provider = export_provider
        self._delete_exports = delete_exports
        self._actuals_with_matched_predictions = actuals_with_matched_predictions
        self._batch_bucket_chunks = self._get_batch_bucket_chunks()

        self._current_chunk_id = 0
        self._prev_bucket_id = None

    def set_new_export_parameters(self, max_rows: int) -> DataRobotBatchExportBase:
        self._max_rows = max_rows
        self.reset()
        return self

    def reset(self) -> None:
        self._current_chunk_id = 0
        self._prev_bucket_id = None
        self._batch_bucket_chunks = self._get_batch_bucket_chunks()

    def _get_batch_bucket_chunks(self) -> BatchBucketChunks:
        return BatchBucketChunks(
            ColumnName.DR_BATCH_ID_COLUMN,
            PushBackFrameIterator(
                iter(
                    DataRobotChunksIterator(
                        api=self._api,
                        deployment_id=self._deployment_id,
                        model_id=self._model_id,
                        start_dt=self._start,
                        end_dt=self._end,
                        export_provider=self._export_provider,
                        delete_exports=self._delete_exports,
                        actuals_with_matched_predictions=self._actuals_with_matched_predictions,
                    )
                )
            ),
        )

    def _update_chunk_info(self, bucket_id: str):
        """
        Source must keep track of a small piece of state to differentiate time bucketed chunks.
        This method updates this state.

        Parameters
        ----------
        chunk_dt: datetime
            datetime of any event within the chunk
        """
        if self._prev_bucket_id and self._prev_bucket_id != bucket_id:
            self._current_chunk_id += 1
        self._prev_bucket_id = bucket_id


class BatchPredictionDataExportProvider(DataRobotBatchExportBase):
    def __init__(
        self,
        api: DataRobotApiClient,
        deployment_id: str,
        start: datetime.datetime,
        end: datetime.datetime,
        batch_ids: List[str],
        model_id: str = None,
        max_rows: int = 10000,
        delete_exports: bool = False,
    ):
        if max_rows <= 0:
            raise ValueError(f"max_rows must be > 0, got {max_rows}")

        super().__init__(
            api=api,
            deployment_id=deployment_id,
            model_id=model_id,
            start=start,
            end=end,
            max_rows=max_rows,
            export_provider=get_export_provider(
                ExportType.PREDICTIONS, api
            ).with_batches(batch_ids),
            delete_exports=delete_exports,
        )

    def get_data(self) -> (pd.DataFrame, int):
        """
        Method to return a chunk of prediction data that can be sent to a metric object to be transformed.
        :return:
            - DataFrame: if there is more data to process, or None
            - int: ID of the time bucket
        """
        if self._batch_bucket_chunks.finished():
            return None, -1

        chunk_df, bucket_id = self._batch_bucket_chunks.load_batch_bucket_chunk(
            max_rows=self._max_rows
        )

        self._update_chunk_info(bucket_id)
        return chunk_df, self._current_chunk_id

    def get_chunk_batch_id(self) -> str:
        return self._prev_bucket_id


class ActualsDataExportProvider(DataRobotExportBase):
    def __init__(
        self,
        api: DataRobotApiClient,
        deployment_id: str,
        start: datetime.datetime,
        end: datetime.datetime,
        model_id: str = None,
        timestamp_col: str = ColumnName.TIMESTAMP,
        max_rows: int = 10000,
        time_bucket: TimeBucket = TimeBucket.ALL,
        delete_exports: bool = False,
        use_cache: bool = False,
        only_matched_predictions: bool = True,
    ):
        if max_rows <= 0:
            raise ValueError(f"max_rows must be > 0, got {max_rows}")

        super().__init__(
            api=api,
            deployment_id=deployment_id,
            model_id=model_id,
            start=start,
            end=end,
            timestamp_col=timestamp_col,
            max_rows=max_rows,
            time_bucket=time_bucket,
            export_type=ExportType.ACTUALS,
            delete_exports=delete_exports,
            use_cache=use_cache,
            actuals_with_matched_predictions=only_matched_predictions,
        )

    def get_data(
        self, return_original_column_names: bool = False
    ) -> (pd.DataFrame, int):
        """
        Method to return a chunk of actuals data that can be sent to a metric object to be transformed.
        :return:
            - DataFrame: if there is more data to process, or None
            - int: ID of the time bucket
        """
        supported_time_buckets = self.get_supported_time_buckets()
        if self._time_bucket not in supported_time_buckets:
            raise DRSourceNotSupported(
                f"For actuals export {self._time_bucket} time bucket is not supported, "
                f"select time bucket from {supported_time_buckets}"
            )

        if self._time_bucket_chunks.finished():
            return None, -1

        chunk_df, chunk_ts = self._time_bucket_chunks.load_time_bucket_chunk(
            time_bucket=self._time_bucket, max_rows=self._max_rows
        )
        if self._deployment.type == DeploymentType.BINARY_CLASSIFICATION:
            chunk_df = self._drop_negative_class(chunk_df)
            self._add_column_with_predicted_class(chunk_df)

        if self._deployment.type == DeploymentType.MULTICLASS:
            # the exported actual column has values in quotation marks and square brackets e.g. ['actual_value']
            chunk_df[ColumnName.ACTUALS] = chunk_df[ColumnName.ACTUALS].apply(
                lambda x: x[2:-2]
            )
            for label in self._deployment.class_labels:
                chunk_df[f"{ColumnName.ACTUALS}_{label}"] = chunk_df[
                    ColumnName.ACTUALS
                ].apply(lambda x: 1 if x == label else 0)
            chunk_df.rename(
                columns={ColumnName.ACTUALS: f"{ColumnName.ACTUALS}_classes"},
                inplace=True,
            )
        if return_original_column_names:
            chunk_df = self._rename_to_original_names(chunk_df)

        self._update_chunk_info(chunk_ts)
        return chunk_df, self._current_chunk_id

    @staticmethod
    def get_supported_time_buckets():
        return [
            TimeBucket.HOUR,
            TimeBucket.DAY,
            TimeBucket.WEEK,
            TimeBucket.MONTH,
            TimeBucket.ALL,
        ]

    def _drop_negative_class(self, actuals_df: pd.DataFrame) -> pd.DataFrame:
        return actuals_df[
            actuals_df.label.astype("str") == self._deployment.positive_class_label
        ]

    def _add_column_with_predicted_class(self, actuals_df: pd.DataFrame) -> None:
        actuals_df[ColumnName.PREDICTED_CLASS] = (
            actuals_df[ColumnName.PREDICTIONS] >= self._deployment.prediction_threshold
        )
        actuals_df[ColumnName.PREDICTED_CLASS] = actuals_df[
            ColumnName.PREDICTED_CLASS
        ].map(
            {
                True: self._deployment.positive_class_label,
                False: self._deployment.negative_class_label,
            }
        )

    def _rename_to_original_names(self, chunk_df: pd.DataFrame) -> pd.DataFrame:
        rename_columns = {
            ColumnName.ASSOCIATION_ID_COLUMN: self._api.get_association_id(
                self._deployment_id
            ),
            ColumnName.PREDICTIONS: self._deployment.target_column,
        }
        chunk_df = chunk_df.rename(rename_columns, axis=1)
        return chunk_df


class TrainingDataExportProvider:
    def __init__(
        self,
        api: DataRobotApiClient,
        deployment_id: str,
        model_id: str = None,
    ):
        self._api = api
        self._deployment_id = deployment_id
        self._model_id = model_id

    def get_data(self) -> pd.DataFrame:
        """
        Method to return training data that can be sent to a metric object to be transformed.
        :return:
            DataFrame: if training data found otherwise None
        """
        response = self._api.start_training_data_export(
            self._deployment_id, self._model_id
        )

        if response.status_code != 202:
            raise DataRobotAPIError(
                f"DataRobot export API failed with {response.status_code}: {response.text}"
            )

        status_url = response.headers["Location"]
        export_id = status_url.split("/")[-2]

        dataset_id = self._api.get_training_export_dataset_id(status_url)

        dataset = self._api.fetch_dataset_sync(dataset_id)
        tempfile_path = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
        with open(tempfile_path, "wb") as f:
            try:
                dataset.get_file(file_path=tempfile_path)
            except OSError as e:
                if e.errno == errno.ENOSPC:
                    raise Exception(
                        f"We ran out of disk space for training data export: {export_id}"
                    )
                raise e
            try:
                result = pd.read_csv(f.name)
            except MemoryError:
                os.remove(tempfile_path)
                raise Exception(
                    f"We ran out of memory for training data export: {export_id}"
                )
        os.remove(tempfile_path)

        return result


class PushBackFrameIterator:
    """
    Extends iterator functionality to push back elements.
    """

    def __init__(self, iterator: Iterator[pd.DataFrame]):
        self._buffer = []
        self._iterator = iterator
        self._finished = False

    def finished(self) -> bool:
        """
        Returns status of a load. True if the records were exhausted.
        """
        self._load_next()
        return not self._buffer and self._finished

    def next(self) -> Optional[pd.DataFrame]:
        """
        Returns next chunk from source or None if finished.
        """
        if self._buffer:
            return self._buffer.pop()
        self._load_next()
        return self._buffer.pop() if self._buffer else None

    def push_back(self, df: pd.DataFrame) -> None:
        """
        Pushes a frame back to the iterator. This frame should be returned on the next call to next.
        """
        self._buffer.append(df)

    def peek_row(self) -> Optional[pd.Series]:
        """
        Returns the first row from DataFrame to be returned without consuming the frame.
        """
        if self._buffer:
            return self._buffer[0].iloc[0]
        self._load_next()
        return self._buffer[0].iloc[0] if self._buffer else None

    def _load_next(self):
        if self._finished or self._buffer:
            return
        try:
            self._buffer.append(next(self._iterator))
        except StopIteration:
            self._finished = True


class DataRobotChunksIterator:
    """
    Uses DataRobot API to perform exports and read data in chunk-by-chunk fashion.
    """

    def __init__(
        self,
        api: DataRobotApiClient,
        deployment_id: str,
        model_id: str | None,
        start_dt: datetime.datetime,
        end_dt: datetime.datetime,
        export_provider: ExportProvider,
        delete_exports: bool = False,
        sort_column: Optional[str] = None,
        actuals_with_matched_predictions: bool = True,
    ):
        self._deployment_id = deployment_id
        self._model_id = model_id
        self._start_dt = start_dt
        self._end_dt = end_dt
        self._sort_column = sort_column
        self._api = api
        self._export_provider = export_provider
        self._delete_exports = delete_exports
        self._actuals_with_matched_predictions = actuals_with_matched_predictions

    def __iter__(self) -> Generator[pd.DataFrame, None, None]:
        """
        Returns an iterator over chunks for time range defined in the constructor. It returns data sorted by timestamp.
        The way it works is as follows
        - it is a generator to lazily fetch data from DR API,
        - it will try to perform a full export (start_dt to end_dt),
            - if this fails with PAYLOAD_TOO_LARGE, we cut interval in half and retry
        - due to sorting requirement, it has to load single successful export into the memory and iterate over it
        - it will perform subsequent exports once previous iteration is exhausted
        """
        interval = self._end_dt - self._start_dt
        start_dt = self._start_dt
        while start_dt != self._end_dt:
            df, interval = self._fetch_subset(start_dt, interval)
            start_dt += interval
            if df.empty:
                continue
            sorted_df = (
                df.sort_values(by=self._sort_column) if self._sort_column else df
            )
            yield sorted_df

    def _fetch_subset(
        self, start_dt: datetime.datetime, interval: datetime.timedelta
    ) -> (pd.DataFrame, datetime.timedelta):
        export_type = self._export_provider.export_type
        logger.info(
            f"fetching the next {export_type} dataframe... {start_dt} - {start_dt + interval}"
        )
        response, interval = self._get_export_response(start_dt, interval)
        try:
            export_id = self._api.get_export_id_sync(response)
        except AsyncProcessUnsuccessfulError as e:
            if export_type:
                fail_msg = f"failed to export {export_type} data for {start_dt} - {start_dt + interval} interval: {str(e)}"
            else:
                fail_msg = f"failed to export data for {start_dt} - {start_dt + interval} interval: {str(e)}"

            # for an export period where there is no data, return an empty data frame
            if "'No saved rows for requested time frame'" in str(e):
                logger.info(fail_msg)
                return pd.DataFrame(), interval
            # otherwise raise an error
            else:
                raise DataExportJobError(fail_msg)

        result = pd.DataFrame()
        for dataset_id in self._export_provider.get_export_dataset_ids(
            self._deployment_id, export_id
        ):
            dataset = self._api.fetch_dataset_sync(dataset_id)
            tempfile_path = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
            with open(tempfile_path, "wb") as f:
                try:
                    dataset.get_file(file_path=tempfile_path)
                except OSError as e:
                    if e.errno == errno.ENOSPC:
                        raise Exception(
                            f"We ran out of disk space for interval {start_dt} - {start_dt + interval}. "
                            f"Consider fetching smaller chunks of data"
                        )
                    raise e
                try:
                    result = pd.concat([result, pd.read_csv(f.name)])
                except MemoryError:
                    os.remove(tempfile_path)
                    raise Exception(
                        f"We ran out of memory for interval {start_dt} - {start_dt + interval}. "
                        f"Consider fetching smaller chunks of data"
                    )
            os.remove(tempfile_path)
            if self._delete_exports:
                self._api.remove_dataset_with_exported_data(dataset_id)

        return result, interval

    def _get_export_response(
        self, from_dt: datetime.datetime, suggested_interval: datetime.timedelta
    ) -> (requests.Response, datetime.timedelta):
        # we try to increase interval to mitigate too aggressive shrinking
        interval = min(self._end_dt - from_dt, 2 * suggested_interval)
        response = self._export_provider.start_data_export(
            deployment_id=self._deployment_id,
            start=from_dt,
            end=from_dt + interval,
            model_id=self._model_id,
            only_matched_predictions=self._actuals_with_matched_predictions,
        )

        while response.status_code == 413:
            interval /= 2
            logger.info(
                f"requested too many rows. trying smaller interval {from_dt} - {from_dt + interval}"
            )
            response = self._export_provider.start_data_export(
                deployment_id=self._deployment_id,
                start=from_dt,
                end=from_dt + interval,
                model_id=self._model_id,
                only_matched_predictions=self._actuals_with_matched_predictions,
            )

        if response.status_code != 202:
            raise DataRobotAPIError(
                f"DataRobot export API failed with {response.status_code}: {response.text}"
            )
        return response, interval


class DataRobotChunksIteratorFromCache:
    """
    Uses DataRobot API to perform exports and read data in chunk-by-chunk fashion.
    """

    def __init__(
        self,
        api: DataRobotApiClient,
        dataset_ids: List[str],
        start_dt: datetime.datetime,
        end_dt: datetime.datetime,
        timestamp_column: str,
        sort_column: Optional[str] = None,
        actuals_with_matched_predictions: bool = True,
    ):
        self._dataset_ids = dataset_ids
        self._start_dt = start_dt
        self._end_dt = end_dt
        self._timestamp_column = timestamp_column
        self._sort_column = sort_column
        self._api = api
        self._actuals_with_matched_predictions = actuals_with_matched_predictions

    def __iter__(self) -> Generator[pd.DataFrame, None, None]:
        """
        Returns an iterator over chunks for time range defined in the constructor. It returns data sorted by timestamp.
        """
        interval = self._end_dt - self._start_dt
        start_dt = self._start_dt
        while start_dt != self._end_dt:
            df, interval = self._fetch_subset(start_dt, interval)
            df = df[
                pd.to_datetime(df[self._timestamp_column]).between(
                    str(start_dt), str(self._end_dt)
                )
            ]
            start_dt += interval
            if df.empty:
                continue
            sorted_df = (
                df.sort_values(by=self._sort_column) if self._sort_column else df
            )
            yield sorted_df

    def _fetch_subset(
        self, start_dt: datetime.datetime, interval: datetime.timedelta
    ) -> (pd.DataFrame, datetime.timedelta):
        result = pd.DataFrame()
        for dataset_id in self._dataset_ids:
            dataset = self._api.fetch_dataset_sync(dataset_id)
            tempfile_path = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
            with open(tempfile_path, "wb") as f:
                try:
                    dataset.get_file(file_path=tempfile_path)
                except OSError as e:
                    if e.errno == errno.ENOSPC:
                        raise Exception(
                            f"We ran out of disk space for interval {start_dt} - {start_dt + interval}. "
                            f"Consider fetching smaller chunks of data"
                        )
                    raise e
                try:
                    result = pd.concat([result, pd.read_csv(f.name)])
                except MemoryError:
                    os.remove(tempfile_path)
                    raise Exception(
                        f"We ran out of memory for interval {start_dt} - {start_dt + interval}. "
                        f"Consider fetching smaller chunks of data"
                    )
            os.remove(tempfile_path)
        return result, interval


class TimeBucketChunks:
    """
    Builds chunks out of rows returned by PushBackFrameIterator.
    """

    def __init__(self, timestamp_column: str, chunks_iterator: PushBackFrameIterator):
        self._timestamp_column = timestamp_column
        self._chunks_iterator = chunks_iterator

    def finished(self) -> bool:
        """
        True if the records in underlying iterator were exhausted.
        """
        return self._chunks_iterator.finished()

    def load_time_bucket_chunk(
        self, time_bucket: TimeBucket, max_rows: int
    ) -> (pd.DataFrame, datetime.datetime):
        """
        Pulls rows from rows_iterator respecting two rules
        - all records must belong to the same time bucket
        - chunk cannot be larger than max_rows

        Parameters
        ----------
        time_bucket: TimeBucket
            All rows within a chunk fall into the same time bucket.
        max_rows: int
            Upperbound on the size of the chunk.
        """
        row = self._chunks_iterator.peek_row()
        if row is None:
            raise ConflictError(
                "fetch_time_bucket_chunk shouldn't be called against exhausted source"
            )
        self._validate_row(row)
        chunk_ts = parse(row[self._timestamp_column])

        chunks = []
        total_rows = 0
        while not self._chunks_iterator.finished() and total_rows < max_rows:
            df = self._chunks_iterator.next()
            same_chunk, others = self._partition_by_time_bucket(
                df, time_bucket, chunk_ts, max_rows - total_rows
            )
            chunks.append(same_chunk)
            total_rows += len(same_chunk)
            if not others.empty:
                self._chunks_iterator.push_back(others)
                break
        return pd.concat(chunks), chunk_ts

    def _partition_by_time_bucket(
        self,
        df: pd.DataFrame,
        time_bucket: TimeBucket,
        chunk_ts: datetime.datetime,
        max_rows: int,
    ) -> (pd.DataFrame, pd.DataFrame):
        """
        Returns a subframe with records that belong to the bucket defined by `chunk_ts` + `time_bucket` arguments.
        It respects `max_rows` constraint - thus some records from that bucket might end up in `others` frame.
        The remaining records are present in the latter data frame.
        Assumes that the rows in `df` are sorted by timestamp. `same_bucket` frame is always a prefix of `df`.
        """
        filter_condition = check_if_in_same_time_bucket_vectorized(
            df[self._timestamp_column].apply(lambda x: parse(x)), chunk_ts, time_bucket
        )
        same_bucket = df[filter_condition].iloc[:max_rows]
        others = df.iloc[len(same_bucket) :]
        return same_bucket, others

    def _validate_row(self, row: pd.Series) -> None:
        if self._timestamp_column not in row:
            logger.debug(
                "Got row without %s column: %s",
                self._timestamp_column,
                row.to_string(header=False, index=False),
            )
            raise ConflictError(f"Got row without {self._timestamp_column} column")


class BatchBucketChunks:
    """
    Builds chunks out of rows returned by PushBackFrameIterator.
    """

    def __init__(self, batch_id_column: str, chunks_iterator: PushBackFrameIterator):
        self._batch_id_column = batch_id_column
        self._chunks_iterator = chunks_iterator

    def finished(self) -> bool:
        """
        True if the records in underlying iterator were exhausted.
        """
        return self._chunks_iterator.finished()

    def load_batch_bucket_chunk(self, max_rows: int) -> (pd.DataFrame, str):
        """
        Pulls rows from rows_iterator respecting two rules
        - all records must belong to the same batch bucket
        - chunk cannot be larger than max_rows

        Parameters
        ----------
        max_rows: int
            Upperbound on the size of the chunk.
        """
        row = self._chunks_iterator.peek_row()
        if row is None:
            raise ConflictError(
                "fetch_time_bucket_chunk shouldn't be called against exhausted source"
            )
        self._validate_row(row)
        batch_id = row[self._batch_id_column]

        chunks = []
        total_rows = 0
        while not self._chunks_iterator.finished() and total_rows < max_rows:
            df = self._chunks_iterator.next()
            same_chunk, others = self._partition_by_batch_bucket(
                df, batch_id, max_rows - total_rows
            )
            chunks.append(same_chunk)
            total_rows += len(same_chunk)
            if not others.empty:
                self._chunks_iterator.push_back(others)
                break
        return pd.concat(chunks), batch_id

    def _partition_by_batch_bucket(
        self,
        df: pd.DataFrame,
        batch_id: str,
        max_rows: int,
    ) -> (pd.DataFrame, pd.DataFrame):
        """
        Returns a subframe with records that belong to the bucket defined by `batch_id`.
        It respects `max_rows` constraint - thus some records from that bucket might end up in `others` frame.
        The remaining records are present in the latter data frame.
        Assumes that the rows in `df` are sorted by batch ID. `same_bucket` frame is always a prefix of `df`.
        """
        filter_condition = df[self._batch_id_column] == batch_id
        same_bucket = df[filter_condition].iloc[:max_rows]
        others = df.iloc[len(same_bucket) :]
        return same_bucket, others

    def _validate_row(self, row: pd.Series) -> None:
        if self._batch_id_column not in row:
            logger.debug(
                "Got row without %s column: %s",
                self._batch_id_column,
                row.to_string(header=False, index=False),
            )
            raise ConflictError(f"Got row without {self._batch_id_column} column")
