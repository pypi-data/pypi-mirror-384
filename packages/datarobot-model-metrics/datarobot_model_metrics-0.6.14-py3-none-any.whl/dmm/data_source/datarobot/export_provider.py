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

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

import requests

from dmm.constants import ExportType
from dmm.datarobot_api_client import DataRobotApiClient


class ExportProvider(ABC):
    export_type: ExportType

    @abstractmethod
    def start_data_export(
        self,
        deployment_id: str,
        start: datetime,
        end: datetime,
        model_id: Optional[str],
        only_matched_predictions: bool = True,
    ):
        """
        Starts data export between start (inclusive) and end (exclusive).
        We cannot assume anything about the order of returned records.

        Parameters
        ----------
        deployment_id: str
        start: datetime
            Inclusive start of the time range.
        end: datetime
            Exclusive end of the time range.
        model_id: Optional[str]
        only_matched_predictions : bool
            If true, exports actuals with matching predictions only.
        """
        pass

    @abstractmethod
    def get_export_dataset_ids(self, deployment_id: str, export_id: str) -> List[str]:
        """
        Fetches identifiers of datasets associated with given export.

        Parameters
        ----------
        deployment_id: str
        export_id: str
            Identifier of a completed export.
        """
        pass

    @abstractmethod
    def with_batches(self, batch_ids: List[str]) -> ExportProvider:
        """
        Returns batch version of this export provider.

        Parameters
        ----------
        batch_ids: List[str]
            Batch IDs associated with future exports.
        """
        pass


def get_export_provider(
    export_type: ExportType, api: DataRobotApiClient
) -> ExportProvider:
    if export_type == ExportType.PREDICTIONS:
        return _PredictionsExportProvider(api)
    elif export_type == ExportType.ACTUALS:
        return _ActualsExportProvider(api)
    else:
        raise Exception(
            f"Can't determine data export provider. Unknown export type, allowed export types: {ExportType.all()}"
        )


class _PredictionsExportProvider(ExportProvider):
    export_type = ExportType.PREDICTIONS

    def __init__(self, api: DataRobotApiClient):
        self._api = api

    def start_data_export(
        self,
        deployment_id: str,
        start: datetime,
        end: datetime,
        model_id: Optional[str],
        only_matched_predictions: bool = True,
    ) -> requests.Response:
        return self._api.start_prediction_data_export(
            deployment_id=deployment_id,
            start=start,
            end=end,
            model_id=model_id,
        )

    def get_export_dataset_ids(self, deployment_id: str, export_id: str) -> List[str]:
        return self._api.get_prediction_export_dataset_ids(
            deployment_id=deployment_id, export_id=export_id
        )

    def with_batches(self, batch_ids: List[str]) -> ExportProvider:
        return _BatchPredictionsExportProvider(api=self._api, batch_ids=batch_ids)


class _BatchPredictionsExportProvider(_PredictionsExportProvider):
    def __init__(self, api: DataRobotApiClient, batch_ids: List[str]):
        super().__init__(api)
        self._batch_ids = batch_ids

    def start_data_export(
        self,
        deployment_id: str,
        start: datetime,
        end: datetime,
        model_id: Optional[str],
        only_matched_predictions: bool = True,
    ) -> requests.Response:
        return self._api.start_batch_prediction_data_export(
            batch_ids=self._batch_ids,
            deployment_id=deployment_id,
            start=start,
            end=end,
            model_id=model_id,
        )


class _ActualsExportProvider(ExportProvider):
    export_type = ExportType.ACTUALS

    def __init__(self, api: DataRobotApiClient):
        self._api = api

    def start_data_export(
        self,
        deployment_id: str,
        start: datetime,
        end: datetime,
        model_id: Optional[str],
        only_matched_predictions: bool = True,
    ) -> requests.Response:
        return self._api.start_actuals_export(
            deployment_id=deployment_id,
            start=start,
            end=end,
            model_id=model_id,
            only_matched_predictions=only_matched_predictions,
        )

    def get_export_dataset_ids(self, deployment_id: str, export_id: str) -> List[str]:
        return self._api.get_actuals_export_dataset_ids(
            deployment_id=deployment_id, export_id=export_id
        )

    def with_batches(self, batch_ids: List[str]) -> ExportProvider:
        return _BatchActualsExportProvider(api=self._api, batch_ids=batch_ids)


class _BatchActualsExportProvider(_ActualsExportProvider):
    def __init__(self, api: DataRobotApiClient, batch_ids: List[str]):
        super().__init__(api)
        self._batch_ids = batch_ids

    def start_data_export(
        self,
        deployment_id: str,
        start: datetime,
        end: datetime,
        model_id: Optional[str],
        only_matched_predictions: bool = True,
    ) -> requests.Response:
        raise Exception("Batch actuals data export is not yet supported!")
