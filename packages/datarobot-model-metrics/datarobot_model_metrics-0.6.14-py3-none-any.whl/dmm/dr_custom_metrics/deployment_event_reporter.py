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
from typing import Optional

from requests.exceptions import ConnectionError, HTTPError
from urllib3.exceptions import MaxRetryError

from dmm.datarobot_api_client import DataRobotClient, api_client_factory


class DeploymentEventReporter:
    def __init__(
        self,
        deployment_id: str,
        dr_client: Optional[DataRobotClient] = None,
        dr_url: Optional[str] = None,
        dr_api_key: Optional[str] = None,
    ):
        """
        :param deployment_id: Deployment ID to report custom metrics for
        :param dr_client: DataRobot client to use (has token/base_url)
        :param dr_url: DataRobot app url
        :param dr_api_key: API Key to access public API
        """
        self._logger = logging.getLogger(__name__)

        self._api = api_client_factory(client=dr_client, url=dr_url, token=dr_api_key)
        self._deployment_id = deployment_id

    def report_deployment(self, title: str, message: str) -> None:
        """
        Report deployment event
        :param title: str
        :param message: str
        """

        try:
            response = self._api.report_deployment_event(
                deployment_id=self._deployment_id, title=title, message=message
            )
            response.raise_for_status()
        except (ConnectionError, HTTPError, MaxRetryError) as e:
            raise Exception(f"Deployment event can not be reported to MLOPS: {str(e)}")
