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
import csv
import os
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import datetime, timedelta, timezone
from itertools import islice
from typing import Iterator, List, Optional

from datarobot.utils.waiters import wait_for_async_resolution
from dateutil.parser import parse
from requests import Response

from .datarobot_api_client import DataRobotClient


def wait_for_result_raw(client: DataRobotClient, response: Response) -> bytes:
    assert response.status_code in (200, 201, 202, 204), response.content

    if response.status_code == 200 or response.status_code == 204:
        data = response.content

    elif response.status_code == 201:
        status_url = response.headers["Location"]
        resp = client.get(status_url)
        if resp.status_code != 200:
            raise Exception(f"Couldn't fetch export data response={resp.content}")
        data = resp.content

    elif response.status_code == 202:
        status_url = response.headers["Location"]
        result = wait_for_async_resolution(client, status_url)
        resp = client.get(result)
        if resp.status_code != 200:
            raise Exception(f"Couldn't fetch export data response={resp.content}")
        data = resp.content
    return data


def wait_for_result_from_status_url(client: DataRobotClient, status_url: str) -> bytes:
    result = wait_for_async_resolution(client, status_url)
    resp = client.get(result)
    if resp.status_code != 200:
        raise Exception(f"Couldn't fetch export data response={resp.content}")
    data = resp.content
    return data


def hour_rounder_up(datetime_to_round: datetime) -> datetime:
    datetime_to_round = datetime_to_round + timedelta(hours=1)
    return datetime_to_round.replace(second=0, microsecond=0, minute=0)


def hour_rounder_down(datetime_to_round: datetime) -> datetime:
    return datetime_to_round.replace(microsecond=0, second=0, minute=0)


def chunk_list(it: List, size: int) -> Iterator:
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def save_to_csv(
    filename: str, items: List[dataclass], fieldnames: Optional[List[str]] = None
) -> None:
    """Saves a list of dataclass derived objects (e.g. SingleMetricResult) to the specified CSV file.

    The `items` is a list of items derived from `dataclasses.dataclass`. This function uses standard `dataclasses`
    methods to determine the fields (if `fieldnames` not provided), and write the data to the CSV file.

    The `fieldnames` is an optional list of fieldnames to write to the CSV file. The primary use for this argument is
    to provide a means for writing a subset of fields to the CSV (or fields in a different order).
    """
    if not isinstance(items, list) or not items or not is_dataclass(items[0]):
        raise TypeError("Items must be a list of dataclass objects")

    properties = fieldnames or [_.name for _ in fields(items[0])]
    with open(filename, "w") as fp:
        w = csv.DictWriter(fp, fieldnames=properties)
        w.writeheader()
        for item in items:
            # only copy "allowed" properties -- the writer fails if extra properties are present
            trimmed = {k: v for k, v in asdict(item).items() if k in properties}
            w.writerow(trimmed)

    return


class RunTimeParameterHandler:
    """"""

    def __init__(self):
        self.deployment_id = os.environ.get("DEPLOYMENT_ID")
        self.playground_id = os.environ.get("PLAYGROUND_ID")
        if self.deployment_id and self.playground_id:
            raise Exception("Playground and deployment IDs are mutually exclusive")
        self.custom_metric_id = os.environ["CUSTOM_METRIC_ID"]

        if self.is_deployment:
            self.dry_run = os.environ.get("DRY_RUN") == "1"
            self.start_ts = os.environ.get("START_TS") or os.environ.get(
                "LAST_SUCCESSFUL_RUN_TS"
            )
            self.end_ts = os.environ.get("END_TS") or os.environ.get("CURRENT_RUN_TS")

            self.set_time_window_params()

        else:
            # Playground specific information
            # TODO - remove once endpoint is added for getting custom llm metric (BUZOK-1602)
            self.name = os.environ.get("CUSTOM_METRIC_NAME")
            # input data for playground
            self.prompt_id = os.environ.get("PROMPT_ID")
            self.prompt = os.environ.get("PROMPT")
            self.citations = os.environ.get("CITATIONS")
            self.response = os.environ.get("RESPONSE")
            self.chat_history_prompts = os.environ.get("CHAT_HISTORY_PROMPTS")
            self.baseline_response = os.environ.get("BASELINE_RESPONSE")

    @property
    def is_deployment(self):
        return self.deployment_id is not None

    @property
    def is_playground(self):
        return self.playground_id is not None

    def set_time_window_params(self):
        now = datetime.now(timezone.utc)
        if self.start_ts:
            self.start_of_export_window = hour_rounder_down(parse(self.start_ts))
        else:
            self.start_of_export_window = hour_rounder_down(now - timedelta(hours=24))

        if self.end_ts:
            self.end_of_export_window = hour_rounder_down(parse(self.end_ts))
        else:
            self.end_of_export_window = hour_rounder_down(now)
