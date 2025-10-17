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
import datetime
import logging
from enum import Enum
from typing import Dict, List, Optional

from datarobot.errors import ClientError
from dateutil.parser import parse

from dmm.datarobot_api_client import DataRobotApiClient, api_client_factory
from dmm.exceptions import ConflictError, DRSourceNotSupported

logger = logging.getLogger(__name__)


class DeploymentType(Enum):
    """
    Supported deployment types (based on deployment.model.targetType)
    """

    REGRESSION = 0
    BINARY_CLASSIFICATION = 1
    MULTICLASS = 2
    TEXT_GENERATION = 3


class Deployment:
    """
    Provides access to relevant deployment properties.
    """

    def __init__(self, deployment_id: str, api: Optional[DataRobotApiClient] = None):
        logger.debug(f"Fetching deployment with deployment_id: {deployment_id}")
        self._api = api or api_client_factory()
        self._deployment = self._api.get_deployment(deployment_id)

        self._model_package = self._get_champion_model_package(deployment_id)
        if self._model_package is None:
            if "modelPackage" not in self._deployment:
                raise DRSourceNotSupported(
                    "We do not support deployments without model packages!"
                )
            model_package_id = self._deployment["modelPackage"]["id"]
            self._model_package = self._api.get_model_package(model_package_id)

        if self._model_package["modelKind"]["isTimeSeries"]:
            raise DRSourceNotSupported("Time series models are not yet supported")

    @property
    def name(self) -> str:
        return self._deployment.get("label", "Unnamed")

    @property
    def target_column(self) -> str:
        return self._deployment["model"]["targetName"]

    @property
    def type(self) -> DeploymentType:
        target_type = self._deployment["model"]["targetType"]
        if target_type == "Binary":
            return DeploymentType.BINARY_CLASSIFICATION
        elif target_type == "Regression":
            return DeploymentType.REGRESSION
        elif target_type == "Multiclass":
            return DeploymentType.MULTICLASS
        elif target_type == "TextGeneration":
            return DeploymentType.TEXT_GENERATION
        else:
            raise DRSourceNotSupported(f"Unsupported model target type {target_type}")

    @property
    def positive_class_label(self) -> str:
        if self.type != DeploymentType.BINARY_CLASSIFICATION:
            raise ConflictError(
                "Positive class label can only be retrieved for binary classification deployments"
            )
        # according to API spec - positive class comes first
        return self._model_package["target"]["classNames"][0]

    @property
    def negative_class_label(self) -> str:
        if self.type != DeploymentType.BINARY_CLASSIFICATION:
            raise ConflictError(
                "Negative class label can only be retrieved for binary classification deployments"
            )
        # according to API spec - negative class is second
        return self._model_package["target"]["classNames"][1]

    @property
    def class_labels(self) -> List[str]:
        if self.type != DeploymentType.MULTICLASS:
            raise ConflictError(
                "This method returns class names for multiclass deployment"
            )
        return self._model_package["target"]["classNames"]

    @property
    def prediction_threshold(self) -> float:
        if self.type != DeploymentType.BINARY_CLASSIFICATION:
            raise ConflictError(
                "Prediction threshold can only be retrieved for binary classification deployments"
            )
        return self._model_package["target"]["predictionThreshold"]

    @property
    def created_at(self) -> datetime:
        return parse(self._deployment["createdAt"])

    @property
    def llm_custom_model_prompt_column_name(self) -> Optional[str]:
        if self.type != DeploymentType.TEXT_GENERATION:
            raise ConflictError(
                "Prompt column name can only be retrieved for text generation deployments"
            )
        prompt_column_name = None
        custom_model = self._get_custom_model()
        # if ENABLE_CUSTOM_MODEL_RUNTIME_PARAMETERS is not enabled, there is no runtimeParameters in the response
        if not custom_model or "runtimeParameters" not in custom_model:
            return prompt_column_name
        runtime_parameters = custom_model["runtimeParameters"]
        for param in runtime_parameters:
            if param["fieldName"] == "PROMPT_COLUMN_NAME":
                prompt_column_name = param["defaultValue"]

        return prompt_column_name

    def _get_champion_model_package(self, deployment_id: str) -> Optional[dict]:
        try:
            return self._api.get_champion_model_package(deployment_id)
        except ClientError:
            return None

    def _get_custom_model(self) -> Optional[dict]:
        _model = self._deployment["model"]
        if "customModelImage" in _model:
            custom_model_id = _model["customModelImage"]["customModelId"]
            version_id = _model["customModelImage"]["customModelVersionId"]
        else:
            return None
        try:
            return self._api.get_custom_model(custom_model_id, version_id)
        except ClientError as e:
            logger.info(f"Failed to retrieve custom model details: {e}")
            return None


deployment_cache: Dict[str, Deployment] = {}


def get_cached_deployment(deployment_id: str) -> Optional[Deployment]:
    global deployment_cache
    return deployment_cache.get(deployment_id)


def set_cached_deployment(deployment_id: str, deployment: Optional[Deployment]) -> None:
    global deployment_cache
    if not deployment:
        deployment_cache.pop(deployment_id, None)
    else:
        deployment_cache[deployment_id] = deployment


def deployment_factory(
    deployment_id: str,
    api: Optional[DataRobotApiClient] = None,
) -> Deployment:
    deployment = get_cached_deployment(deployment_id)
    if deployment:
        logger.debug(f"Using cached deployment {deployment.name} ({deployment_id})")
        return deployment

    deployment = Deployment(deployment_id=deployment_id, api=api)
    set_cached_deployment(deployment_id, deployment)
    logger.debug(f"Updating cached deployment {deployment.name} ({deployment_id})")
    return deployment
