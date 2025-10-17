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
from datetime import datetime
from typing import List, Optional, Union

import yaml
from schema import Or, Schema, SchemaError

from dmm.constants import CustomMetricAggregationType, CustomMetricDirectionality
from dmm.datarobot_api_client import DataRobotClient, api_client_factory
from dmm.exceptions import CustomMetricNotFound, DRCustomMetricConfigError


class DRCustomMetric:
    """
    A class to manage custom metrics definitions on the DR side
    """

    config_schema = Schema(
        {
            "customMetrics": [
                {
                    "name": str,
                    "description": str,
                    "isModelSpecific": bool,
                    "directionality": Or(*CustomMetricDirectionality.all()),
                    "type": Or(*CustomMetricAggregationType.all()),
                    "units": str,
                    "timeStep": str,
                    "baselineValue": Or(int, float),
                }
            ]
        }
    )

    def __init__(
        self,
        deployment_id: str,
        model_package_id: str = None,
        dr_client: Optional[DataRobotClient] = None,
        dr_url: Optional[str] = None,
        dr_api_key: Optional[str] = None,
    ):
        """
        :param dr_url: DataRobot app url
        :param dr_api_key: API Key to access public API
        :param deployment_id: Deployment ID to report custom metrics for
        :param model_package_id: Model package ID is required in case of reporting model specific metrics
        """
        self._logger = logging.getLogger(__name__)

        self._api = api_client_factory(client=dr_client, token=dr_api_key, url=dr_url)
        self._deployment_id = deployment_id
        self._model_package_id = model_package_id
        self._metrics_config = None

    def set_config(
        self, config_yaml: str = None, config_dict: dict = None, config_path: str = None
    ) -> None:
        """
        Get definition of custom metrics from a config
        Supported ways to get definitions: YAML, dict, YAML file, JSON file
        :param config_yaml:
        :param config_path:
        :param config_dict:
        :return:
        """

        # Read the config in multiple formats
        if config_yaml:
            parsed_dict = yaml.safe_load(config_yaml)
            self._metrics_config = parsed_dict
        elif config_dict:
            self._metrics_config = config_dict
        elif config_path:
            with open(config_path, "r") as file:
                parsed_dict = yaml.safe_load(file)
            self._metrics_config = parsed_dict
        else:
            raise ValueError(
                "Selected unsupported method, available config settings from: YAML, dict, file"
            )

        try:
            self.config_schema.validate(self._metrics_config)
        except SchemaError as se:
            self._logger.error("Configuration is not valid")
            raise se
        # Removing the section and pointing directly to the list
        self._metrics_config = self._metrics_config["customMetrics"]

        # Validating that names are unique
        if not self._has_unique_values(self._metrics_config, "name"):
            raise DRCustomMetricConfigError(
                f"Found a non unique name field in custom metrics from config"
            )

    def sync(self) -> None:
        """
        Sync DR deployment custom metrics from a definition of custom metrics
        :return:
        """
        self._has_config()
        dr_custom_metrics = self.get_dr_custom_metrics()
        self._build_unified_list_of_cm(dr_custom_metrics)
        missing_dr_cm_names = self._get_missing_dr_custom_metrics(dr_custom_metrics)
        self._create_missing_dr_custom_metrics(missing_dr_cm_names)

    def get_dr_custom_metrics(self) -> List[dict]:
        """
        Get list of custom metrics from the DR side
        :return:
        """
        cm_dict = self._api.list_custom_metric(self._deployment_id)

        cm_list = cm_dict["data"]
        return cm_list

    def report_value(
        self,
        custom_metric_name: str,
        value: Union[int, float],
        association_id: str = None,
    ) -> None:
        """
        Report a value for a custom metric given the custom metric name. Avoid using the ID
        :param custom_metric_name:
        :param value:
        :param association_id:
        :return:
        """
        self._has_config()

        metric = self._find_metric_by_name(custom_metric_name)
        if metric is None:
            raise CustomMetricNotFound(
                f"Custom Metric named: '{custom_metric_name}' not found"
            )

        if "id" not in metric:
            raise DRCustomMetricConfigError(
                f"Custom Metric {custom_metric_name} ID not found, "
                f"make sure the 'sync()' method has been called."
            )

        ts = datetime.utcnow()
        bucket = {
            "timestamp": ts.isoformat(),
            "value": value,
            "sampleSize": 1,
        }

        if association_id:
            bucket["associationId"] = association_id
        buckets = [bucket]

        response = self._api.submit_custom_metric_values(
            deployment_id=self._deployment_id,
            custom_metric_id=metric["id"],
            model_package_id=(
                self._model_package_id if metric["isModelSpecific"] else None
            ),
            buckets=buckets,
        )
        response.raise_for_status()
        self._logger.info(
            f"Submitted custom metrics value: {buckets} for {custom_metric_name}"
        )

    def name2id(self, name: str) -> str:
        """
        Translate custom metric name to a metric ID
        :param name:
        :return: str
        """
        self._has_config()
        metric = self._find_metric_by_name(name)
        if not metric:
            raise CustomMetricNotFound(
                f"Failed to translate custom metric name: {name} to metric ID"
            )
        return metric["id"]

    def _has_config(self) -> None:
        """
        Check if DRCustomMetric has set the config
        """
        if self._metrics_config is None:
            raise DRCustomMetricConfigError(
                "Must provide custom metrics configuration first, use 'set_config' method"
            )

    def _get_missing_dr_custom_metrics(
        self, dr_custom_metrics: List[dict]
    ) -> List[str]:
        local_cm_names = {item["name"]: item for item in self._metrics_config}
        dr_cm_names = {item["name"]: item for item in dr_custom_metrics}
        missing_dr_cm_names = list(set(local_cm_names) - set(dr_cm_names))
        return missing_dr_cm_names

    def _create_missing_dr_custom_metrics(self, missing_dr_cm_names: List[str]) -> None:
        for name in missing_dr_cm_names:
            metric = self._find_metric_by_name(cm_name=name)
            metric_id = self._api.create_custom_metric(
                deployment_id=self._deployment_id,
                name=metric["name"],
                directionality=metric["directionality"],
                aggregation_type=metric["type"],
                time_step=metric["timeStep"],
                units=metric["units"],
                baseline_value=metric["baselineValue"],
                is_model_specific=metric["isModelSpecific"],
            )
            self._logger.info(f"Created a custom metric: {name} with ID {metric_id}")
            # update metric with id
            metric["id"] = metric_id

    def _build_unified_list_of_cm(self, dr_custom_metrics: List[dict]) -> None:
        for dr_cm in dr_custom_metrics:
            local_metric = self._find_metric_by_name(dr_cm["name"])
            if local_metric:
                local_metric["id"] = dr_cm["id"]
            else:
                self._metrics_config.append(dr_cm)

    def _find_metric_by_name(self, cm_name: str) -> Optional[dict]:
        return next(filter(lambda x: x["name"] == cm_name, self._metrics_config), None)

    @staticmethod
    def _has_unique_values(input_list: List[dict], key: str) -> bool:
        _values = [item.get(key) for item in input_list]
        return len(set(_values)) == len(_values)
