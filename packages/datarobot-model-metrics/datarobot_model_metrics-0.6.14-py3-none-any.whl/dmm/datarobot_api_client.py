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
import json
import logging
import time
from typing import Any, List, Optional, Union

import datarobot as dr
import datarobot.errors
import requests
from datarobot import Client as DataRobotClient
from datarobot.errors import AsyncProcessUnsuccessfulError
from dateutil.parser import parse

from dmm.constants import ExportType
from dmm.exceptions import (
    CustomMetricLimitExceeded,
    DataRobotAPIError,
    DuplicateCustomMetricName,
)
from dmm.utils import wait_for_result_from_status_url, wait_for_result_raw

logger = logging.getLogger(__name__)

_global_api_client: Optional[DataRobotApiClient] = None


def get_global_api_client() -> Optional[DataRobotApiClient]:
    global _global_api_client
    return _global_api_client


def set_global_api_client(
    api_client: Optional[DataRobotApiClient], source: str
) -> None:
    global _global_api_client
    logger.info(
        f"Setting global client from {source}: {api_client.url() if api_client else ''}"
    )
    _global_api_client = api_client


def api_client_factory(
    client: Optional[DataRobotClient] = None,
    url: Optional[str] = None,
    token: Optional[str] = None,
) -> DataRobotApiClient:
    global_client = get_global_api_client()

    # if nothing is specified, create/use the global client
    if not any([client, all([url, token])]):
        if global_client:
            logger.info(f"Using default global client: {global_client.url()}")
            return global_client

        api = DataRobotApiClient(client=DataRobotClient())
        set_global_api_client(api, "environment")
        return api

    # NOTE: jumping through extra hoops here to avoid another "validation"
    use_global_client = False
    if global_client and client:
        use_global_client = global_client.same(client.endpoint, client.token)
    elif global_client and url and token:
        use_global_client = global_client.same(url, token)

    if use_global_client:
        logger.debug(f"Using global DataRobot API client: {global_client.url()}")
        return global_client

    # if client is not passed, use the passed url/token to create the client
    if not client:
        client = DataRobotClient(token=token, endpoint=url)

    api = DataRobotApiClient(client=client)
    if not _global_api_client:
        set_global_api_client(api, "url/token")
    else:
        logger.info(f"Using different client: {api.url()}")
    return api


class DataRobotApiClient:
    """
    Wrapper around DataRobotClient that exposes required operations against DataRobot API.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        client: Optional[DataRobotClient] = None,
    ):
        if client:
            _api = client
        elif token and base_url:
            if not self._is_v2_api(base_url) and not self._is_api_gw(base_url):
                base_url += "/api/v2/"
            _api = DataRobotClient(token=token, endpoint=base_url)
        elif (token and not base_url) or (not token and base_url):
            raise ValueError("Two parameters need to be provided: token and base_url")
        else:
            _api = DataRobotClient()
        self._client = _api

    @staticmethod
    def _is_v2_api(base_url: str) -> bool:
        return base_url.endswith("/api/v2") or base_url.endswith("/api/v2/")

    @staticmethod
    def _is_api_gw(base_url: str) -> bool:
        return base_url.endswith("/api-gw") or base_url.endswith("/api-gw/")

    def same(self, url: str, token: str) -> bool:
        """Check to see if using same URL and token"""
        return self._client.endpoint == url and self._client.token == token

    def url(self) -> str:
        """Get the base url"""
        return self._client.endpoint

    def start_prediction_data_export(
        self,
        deployment_id: str,
        start: datetime.datetime,
        end: datetime.datetime,
        model_id: Union[str, None],
        **kwargs,
    ) -> requests.Response:
        return self._start_prediction_data_export(
            deployment_id, start, end, model_id, batch_ids=None
        )

    def start_batch_prediction_data_export(
        self,
        batch_ids: List[str],
        deployment_id: str,
        start: datetime.datetime,
        end: datetime.datetime,
        model_id: Union[str, None],
        **kwargs,
    ) -> requests.Response:
        return self._start_prediction_data_export(
            deployment_id, start, end, model_id, batch_ids=batch_ids
        )

    def _start_prediction_data_export(
        self,
        deployment_id: str,
        start: datetime.datetime,
        end: datetime.datetime,
        model_id: Union[str, None],
        batch_ids: Optional[List[str]],
    ) -> requests.Response:
        """
        Starts prediction data export between start (inclusive) and end (exclusive).
        We cannot assume anything about the order of returned records.

        Parameters
        ----------
        deployment_id: str
        start: datetime
            Inclusive start of the time range.
        end: datetime
            Exclusive end of the time range.
        model_id: Optional[str]
        batch_ids: Optional[List[str]]
            If present, it will perform batch export for the passed IDs.
        """
        return self._client.post(
            f"deployments/{deployment_id}/predictionDataExports/",
            data={
                "start": start,
                "end": end,
                "modelId": model_id,
                "batch_ids": batch_ids,
            },
        )

    def start_actuals_export(
        self,
        deployment_id: str,
        start: datetime.datetime,
        end: datetime.datetime,
        model_id: Union[str, None],
        only_matched_predictions: bool = True,
        **kwargs,
    ) -> requests.Response:
        """
        Starts actuals data export between start (inclusive) and end (exclusive).
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
        return self._client.post(
            f"deployments/{deployment_id}/actualsDataExports/",
            data={
                "start": start,
                "end": end,
                "modelId": model_id,
                "onlyMatchedPredictions": only_matched_predictions,
            },
        )

    def start_training_data_export(
        self,
        deployment_id: str,
        model_id: Union[str, None],
    ) -> requests.Response:
        """
        Starts export of training data for the given model.
        If model_id is not given, export for current deployment champion.
        We cannot assume anything about the order of returned records.

        Parameters
        ----------
        deployment_id: str
        model_id: Optional[str]
        """
        return self._client.post(
            f"deployments/{deployment_id}/trainingDataExports/",
            data={"modelId": model_id},
        )

    def get_export_id_sync(self, start_export_response: requests.Response) -> str:
        """
        Waits until ready and fetches export_id after the export finishes. This method is blocking.

        Parameters
        ----------
        start_export_response: requests.Response
            Result of relevant start export call
        """
        export_id_response = wait_for_result_raw(self._client, start_export_response)
        export_id_response = json.loads(export_id_response)
        if export_id_response["status"] == "FAILED":
            raise AsyncProcessUnsuccessfulError(export_id_response["error"]["message"])
        return export_id_response["id"]

    def get_prediction_export_dataset_ids(
        self, deployment_id: str, export_id: str
    ) -> List[str]:
        """
        Export data can be fetched as datasets. This method fetches identifiers of these datasets.

        Parameters
        ----------
        deployment_id: str
        export_id: str
            Identifier of a completed export.
        """
        response = self._client.get(
            f"deployments/{deployment_id}/predictionDataExports/{export_id}"
        )
        data = response.json()["data"]
        dataset_ids = []
        if data:
            for item in data:
                try:
                    self._client.get(f"datasets/{item['id']}")
                except datarobot.errors.ClientError:
                    logger.info(
                        f"dataset {item['id']} not found for prediction export id {export_id}"
                        f" - was previously deleted"
                    )
                else:
                    dataset_ids.append(item["id"])
            return dataset_ids
        else:
            logger.info(f"no datasets found for prediction export id {export_id}")
            return []

    def get_actuals_export_dataset_ids(
        self, deployment_id: str, export_id: str
    ) -> List[str]:
        """
        Export data can be fetched as datasets. This method fetches identifiers of these datasets.

        Parameters
        ----------
        deployment_id: str
        export_id: str
            Identifier of a completed export.
        """
        response = self._client.get(
            f"deployments/{deployment_id}/actualsDataExports/{export_id}"
        )
        data = response.json()["data"]
        dataset_ids = []
        if data:
            for item in data:
                try:
                    self._client.get(f"datasets/{item['id']}")
                except datarobot.errors.ClientError:
                    logger.info(
                        f"dataset {item['id']} not found for actuals export id {export_id}"
                        f" - was previously deleted"
                    )
                else:
                    dataset_ids.append(item["id"])
            return dataset_ids
        else:
            logger.info(f"no datasets found for actuals export id {export_id}")
            return []

    def get_training_export_dataset_id(self, status_url: str) -> str:
        """
        Export data can be fetched as datasets. This method fetches identifier of this dataset.

        Parameters
        ----------
        status_url: str
        """
        export_id_response = wait_for_result_from_status_url(self._client, status_url)
        return json.loads(export_id_response)["datasetId"]

    def get_deployment(self, deployment_id: str) -> dict:
        """
        Fetches deployment metadata (model target name and type etc.)

        Parameters
        ----------
        deployment_id: str
        """
        return self._client.get(f"deployments/{deployment_id}").json()

    def get_model_package(self, model_package_id: str) -> dict:
        """
        Fetches model package info (to get time series info, prediction threshold etc.)

        Parameters
        ----------
        model_package_id: str
        """
        return self._client.get(f"modelPackages/{model_package_id}").json()

    def get_custom_model(self, custom_model_id: str, version_id: str) -> dict:
        """
        Fetches custom model data

        Parameters
        ----------
        custom_model_id: str
        version_id: str
        """
        return self._client.get(
            f"customModels/{custom_model_id}/versions/{version_id}/"
        ).json()

    def get_deployment_settings(self, deployment_id: str) -> dict:
        """
        Fetches deployment settings

        Parameters
        ----------
        deployment_id: str
        """
        return self._client.get(f"deployments/{deployment_id}/settings").json()

    def get_association_id(self, deployment_id: str) -> str:
        """
        Fetches association id for the given deployment, returns None if no association id

        Parameters
        ----------
        deployment_id: str
        """
        deployment_settings = self.get_deployment_settings(deployment_id)
        column_names = deployment_settings["associationId"]["columnNames"]
        association_id = column_names[0] if column_names else None
        return association_id

    def get_champion_model_package(self, deployment_id: str) -> dict:
        """
        Fetches champion model package data

        Parameters
        ----------
        deployment_id: str
        """
        return self._client.get(
            f"deployments/{deployment_id}/championModelPackage"
        ).json()

    @staticmethod
    def fetch_dataset_sync(dataset_id: str, max_wait_sec: int = 600) -> dr.Dataset:
        """
        Fetches dataset synchronously.

        Parameters
        ----------
        dataset_id: str
        max_wait_sec: int
            Maximum await time in seconds. Throws if waiting time exceeds this threshold.
        """
        start = time.time()
        while start + max_wait_sec > time.time():
            dataset = dr.Dataset.get(dataset_id)
            if dataset.processing_state == "COMPLETED":
                return dataset
            elif dataset.processing_state == "ERROR":
                raise ValueError(
                    "Dataset creation failed, most likely you requested range with no predictions"
                )
            time.sleep(5)
        raise TimeoutError(f"Failed to fetch dataset within {max_wait_sec} seconds")

    def remove_dataset_with_exported_data(self, dataset_id: str) -> None:
        """
        Removes a catalog item from AI catalog.

        Parameters
        ----------
        dataset_id: str
        """
        self._client.delete(f"datasets/{dataset_id}")

    def get_custom_metric(self, deployment_id: str, custom_metric_id: str) -> dict:
        """
        Fetches custom metric metadata
        """
        return self._client.get(
            f"deployments/{deployment_id}/customMetrics/{custom_metric_id}/"
        ).json()

    def list_custom_metric(self, deployment_id: str) -> dict:
        """
        Retrieve a list of custom metrics
        """
        return self._client.get(f"deployments/{deployment_id}/customMetrics/").json()

    def create_custom_metric(
        self,
        deployment_id: str,
        name: str,
        aggregation_type: str,
        directionality: str,
        units: str,
        baseline_value: float,
        is_model_specific: bool,
        time_step: str = "hour",
        description: Optional[str] = None,
    ) -> str:
        """
        Create custom metric definition
        """
        payload = {
            "name": name,
            "directionality": directionality,
            "units": units,
            "type": aggregation_type,
            "timeStep": time_step,
            "baselineValues": [{"value": baseline_value}],
            "isModelSpecific": is_model_specific,
        }
        if description:
            payload["description"] = description
        response = self._client.post(
            f"deployments/{deployment_id}/customMetrics/",
            data=payload,
        )
        if response.status_code != 201:
            error_msg = response.json()["message"]
            if error_msg.startswith("Maximum number of custom metrics reached"):
                raise CustomMetricLimitExceeded(error_msg)
            elif error_msg.startswith("Custom metric name"):
                raise DuplicateCustomMetricName(error_msg)
            else:
                raise DataRobotAPIError(f"Error creating custom metric {error_msg}")

        custom_metric_id = response.json()["id"]
        return custom_metric_id

    def submit_custom_metric_values(
        self,
        deployment_id: str,
        custom_metric_id: str,
        buckets: List[dict],
        model_id: str = None,
        model_package_id: str = None,
        dry_run: bool = False,
    ) -> requests.Response:
        """
        Upload custom metric values
        """
        data = {"buckets": buckets, "dryRun": dry_run}
        if model_id:
            data["modelId"] = model_id
        if model_package_id:
            data["model_package_id"] = model_package_id
        return self._client.post(
            f"deployments/{deployment_id}/customMetrics/{custom_metric_id}/fromJSON/",
            data=data,
        )

    def submit_custom_llm_metric_value(
        self,
        prompt_id: str,
        metric_id: str,
        name: str,
        value: float | int | str,
    ) -> requests.Response:
        payload = {"custom_metrics": [{"id": metric_id, "name": name, "value": value}]}
        return self._client.patch(f"chatPrompts/{prompt_id}/", data=payload)

    def find_data_export(
        self,
        deployment_id: str,
        model_id: str,
        start: datetime.datetime,
        end: datetime.datetime,
        export_type: ExportType,
        actuals_with_matched_predictions: bool,
    ) -> Optional[str]:
        """
        Fetches data export by deployment_id, model_id and export range
        """
        compare_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        export_id = None

        if export_type == ExportType.PREDICTIONS:
            url = f"deployments/{deployment_id}/predictionDataExports/"
        elif export_type == ExportType.ACTUALS:
            url = f"deployments/{deployment_id}/actualsDataExports/"
        else:
            return export_id

        start = start.strftime(compare_format)
        end = end.strftime(compare_format)
        while url:
            response = self._client.get(url).json()
            url = response["next"]
            for export in response["data"]:
                if (
                    export_type == ExportType.ACTUALS
                    and export["onlyMatchedPredictions"]
                    != actuals_with_matched_predictions
                ):
                    continue

                if (
                    parse(export["period"]["start"]).strftime(compare_format) <= start
                    and parse(export["period"]["end"]).strftime(compare_format) >= end
                    and export["status"] == "SUCCEEDED"
                    and export["modelId"] == str(model_id)
                ):
                    return export["id"]
        return export_id

    def report_deployment_event(
        self, deployment_id: str, title: str, message: str
    ) -> requests.Response:
        event_payload = {
            "eventType": "deploymentInfo",
            "deploymentId": deployment_id,
            "title": title,
            "message": message,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        return self._client.post(
            "remoteEvents/",
            data=event_payload,
        )
