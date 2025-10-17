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

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Union

import dateutil
import pandas as pd
import requests
from dateutil.parser import parse

from dmm.constants import CustomMetricAggregationType, CustomMetricDirectionality
from dmm.datarobot_api_client import DataRobotClient, api_client_factory
from dmm.utils import chunk_list

logger = logging.getLogger(__name__)

MAX_BUCKETS_NUMBER_PER_REQUEST = 10000


@dataclass
class SingleMetricResult:
    """
    Helper data class that contains fields required for individual metric results.
    Used to report metric values per prediction row.
    """

    value: float
    timestamp: Optional[Union[datetime, str]] = None
    batch_id: Optional[str] = None
    association_id: Optional[str] = None
    metadata: Optional[str] = None


class CustomMetric:
    def __init__(
        self,
        custom_metric_id: str,
        deployment_id: str,
        model_id: str,
        name: str,
        directionality: CustomMetricDirectionality,
        units: str,
        aggregation_type: CustomMetricAggregationType,
        baseline_value: float,
        is_model_specific: bool,
        is_batch: bool,
        description: str = None,
        value: str = None,
        sample_count: str = None,
        timestamp: str = None,
        time_format: str = None,
        batch: str = None,
        geospatial: Optional[str] = None,
        client: Optional[DataRobotClient] = None,
    ):
        self.custom_metric_id = custom_metric_id
        self.name = name
        self.directionality = directionality
        self.units = units
        self.aggregation_type = aggregation_type
        self.baseline_value = baseline_value
        self.is_model_specific = is_model_specific

        self.description = description
        self.timestamp = timestamp
        self.time_format = time_format
        self.value = value
        self.sample_count = sample_count
        self.batch = batch
        self.geospatial = geospatial

        self.deployment_id = deployment_id
        self.model_id = model_id
        self.is_batch = is_batch
        self._api = api_client_factory(client=client)

    @classmethod
    def from_id(
        cls,
        metric_id: str = None,
        deployment_id: str = None,
        model_id: str = None,
        client: Optional[DataRobotClient] = None,
        is_batch: bool = False,
    ) -> CustomMetric:
        deployment_id = deployment_id or os.environ.get("DEPLOYMENT_ID")
        metric_id = metric_id or os.environ.get("CUSTOM_METRIC_ID")

        api = api_client_factory(client=client)
        cm_metadata = api.get_custom_metric(deployment_id, metric_id)

        # get champion model if metric is model specific and user does not explicitly pass the model_id
        if cm_metadata["isModelSpecific"] and not model_id:
            model_id = api.get_deployment(deployment_id)["model"]["id"]

        # set model_id to None if metric is deployment specific
        if not cm_metadata["isModelSpecific"]:
            model_id = None

        baseline_value = (
            cm_metadata["baselineValues"][0]["value"]
            if cm_metadata["baselineValues"]
            else None
        )

        custom_metric = cls(
            custom_metric_id=metric_id,
            deployment_id=deployment_id,
            model_id=model_id,
            name=cm_metadata["name"],
            directionality=cm_metadata["directionality"],
            units=cm_metadata["units"],
            aggregation_type=cm_metadata["type"],
            baseline_value=baseline_value,
            description=cm_metadata["description"],
            is_model_specific=cm_metadata["isModelSpecific"],
            value=cm_metadata["value"]["columnName"],
            sample_count=cm_metadata["sampleCount"]["columnName"],
            batch=cm_metadata["batch"]["columnName"],
            timestamp=cm_metadata["timestamp"]["columnName"],
            time_format=cm_metadata["timestamp"]["timeFormat"],
            geospatial=cm_metadata.get("geospatialSegmentAttribute"),
            client=client,
            is_batch=is_batch,
        )
        return custom_metric

    def report(self, df: pd.DataFrame, dry_run: bool = False) -> requests.Response:
        """
        Method used to report aggregated custom metrics values in form of pandas DataFrame.
        This is motivated by the fact that the MetricEvaluator returns such a data format at the output.
        """
        buckets = []
        for _, row in df.iterrows():
            bucket = {"sampleSize": row["samples"]}

            # if the metric aggregation type is sum and values aggregated over time are passed,
            # the reverse operation is performed before the values are sent to DR to avoid double aggregation
            if self.aggregation_type == CustomMetricAggregationType.SUM:
                bucket["value"] = row[self.name] / int(row["samples"])
            else:
                bucket["value"] = row[self.name]

            if self.is_batch:
                bucket["batch"] = row["batch_id"]
            else:
                if isinstance(row["timestamp"], datetime):
                    bucket["timestamp"] = row["timestamp"].isoformat()
                else:
                    bucket["timestamp"] = parse(row["timestamp"]).isoformat()
            self._add_geospatial(row, bucket)
            buckets.append(bucket)

        response = self._api.submit_custom_metric_values(
            deployment_id=self.deployment_id,
            custom_metric_id=self.custom_metric_id,
            model_id=self.model_id,
            buckets=buckets,
            dry_run=dry_run,
        )
        return response

    def report_single_value(
        self,
        value: float | int,
        timestamp: datetime | str = None,
        association_id: str = None,
        dry_run: bool = False,
        metadata: Optional[str] = None,
    ) -> requests.Response:
        """Report a single custom metric value. If no timestamp is specified, use the current UTC timestamp"""
        if not timestamp:
            ts = datetime.utcnow()
        else:
            ts = timestamp if isinstance(timestamp, datetime) else parse(timestamp)

        bucket = {
            "timestamp": ts.isoformat(),
            "value": value,
            "sampleSize": 1,
        }
        if association_id:
            bucket["associationId"] = association_id
        if metadata:
            bucket["metadata"] = metadata

        response = self._api.submit_custom_metric_values(
            deployment_id=self.deployment_id,
            custom_metric_id=self.custom_metric_id,
            model_id=self.model_id,
            buckets=[bucket],
            dry_run=dry_run,
        )
        return response

    def report_single_results(
        self, results: List[SingleMetricResult], dry_run: bool = False
    ) -> requests.Response:
        """
        Method that is used to report non-aggregated custom metric values.
        In this case, each bucket corresponds to one custom metric result.
        """
        buckets = []
        for result in results:
            bucket = {"sampleSize": 1, "value": result.value}

            if not result.timestamp and not result.batch_id:
                raise ValueError(
                    "Each metric result must have either timestamp or batch defined."
                )

            if result.timestamp and self.is_batch:
                raise ValueError(
                    f"Custom metric: {self.name} values should contain only batch IDs"
                )

            if result.batch_id and not self.is_batch:
                raise ValueError(
                    f"Custom metric: {self.name} values should contain only timestamps"
                )

            if result.timestamp:
                if isinstance(result.timestamp, datetime):
                    bucket["timestamp"] = result.timestamp.isoformat()
                else:
                    bucket["timestamp"] = dateutil.parser.parse(
                        result.timestamp
                    ).isoformat()

            if result.batch_id:
                bucket["batch"] = str(result.batch_id)

            if result.association_id:
                bucket["associationId"] = str(result.association_id)

            if result.metadata:
                bucket["metadata"] = result.metadata

            buckets.append(bucket)

        if len(buckets) > MAX_BUCKETS_NUMBER_PER_REQUEST:
            chunks = chunk_list(buckets, MAX_BUCKETS_NUMBER_PER_REQUEST)
        else:
            chunks = [buckets]

        response = None
        for index, chunk in enumerate(chunks):
            logger.debug(
                f"Uploading chunk {index + 1}/{len(chunks)} with {len(chunk)} items"
            )
            response = self._api.submit_custom_metric_values(
                deployment_id=self.deployment_id,
                custom_metric_id=self.custom_metric_id,
                model_id=self.model_id,
                buckets=chunk,
                dry_run=dry_run,
            )
            if not response.ok:
                break

        return response

    def _add_geospatial(self, row: pd.Series, bucket: dict) -> None:
        """
        Add bucket['geospatialCoordinate'] when this metric is geospatial.
        No-op for non-geo metrics. Helper is created and cached on self.
        """
        geo_attr = getattr(self, "geospatial", None)
        if not geo_attr:
            return

        helper = getattr(self, "_geo_helper", None)
        if helper is None or getattr(helper, "geo_attr", None) != geo_attr:
            from dmm.metric.geo_metrics import GeospatialSupport

            helper = GeospatialSupport(geo_attr=geo_attr)
            self._geo_helper = helper

        helper.attach(bucket, row)


class CustomLLMMetric:
    """Used for custom metrics that are generated for a single prompt-response pair from
    the LLM Playground.  Custom LLM metrics that are associated with a deployed LLM will
    use CustomMetric to report results."""

    def __init__(
        self,
        custom_metric_id: str,
        prompt_id: str,
        name: str,
        value: str = None,
        client: Optional[DataRobotClient] = None,
    ):
        self.custom_metric_id = custom_metric_id
        self.name = name
        self.prompt_id = prompt_id

        self.value = value
        self._api = api_client_factory(client)

    @classmethod
    def from_id(
        cls,
        metric_id: str = None,
        name: str = None,
        prompt_id: str = None,
        client: Optional[DataRobotClient] = None,
    ):
        # TODO when the get endpoint is implemented this should use it.
        metric_id = metric_id or os.environ.get("CUSTOM_METRIC_ID")
        prompt_id = prompt_id or os.environ.get("PROMPT_ID")
        name = name or os.environ.get("CUSTOM_METRIC_NAME")

        if not metric_id:
            raise ValueError("metric_id must be provided")

        if not prompt_id:
            raise ValueError("prompt_id must be provided")

        custom_metric = cls(
            custom_metric_id=metric_id,
            prompt_id=prompt_id,
            name=name,
            client=client,
        )
        return custom_metric

    def report(self, value: float | int | str) -> requests.Response:
        response = self._api.submit_custom_llm_metric_value(
            metric_id=self.custom_metric_id,
            prompt_id=self.prompt_id,
            name=self.name,
            value=value,
        )
        return response
