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
from enum import Enum


class ColumnName:
    PREDICTIONS = "predictions"
    TARGET_VALUE = "target_value"
    ACTUALS = "actuals"
    TIMESTAMP = "timestamp"
    NR_SAMPLES = "samples"
    METRIC_VALUE = "value"
    DR_TIMESTAMP_COLUMN = "DR_RESERVED_PREDICTION_TIMESTAMP"
    DR_PREDICTION_COLUMN = "DR_RESERVED_PREDICTION_VALUE"
    DR_BATCH_ID_COLUMN = "DR_RESERVED_BATCH_ID"
    DMM_RESERVED_TS = "DMM_RESERVED_TS"
    ASSOCIATION_ID_COLUMN = "association_id"
    INTERNAL_ASSOCIATION_ID_COLUMN_NAME = "__DataRobot_Internal_Association_ID__"
    BATCH_ID_COLUMN = "batch_id"
    LABEL = "label"
    PREDICTED_CLASS = "predicted_class"
    PROMPT = "prompt"
    PROMPT_TEXT = "promptText"
    RESPONSE = "response"
    CITATIONS = "citations"
    CHAT_HISTORY_PROMPTS = "chat_history_prompts"
    BASELINE_RESPONSE = "baseline_response"

    @classmethod
    def llm_column_names(cls):
        return [
            cls.PROMPT,
            cls.RESPONSE,
            cls.CITATIONS,
            cls.CHAT_HISTORY_PROMPTS,
            cls.BASELINE_RESPONSE,
        ]


class TimeBucket(Enum):
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    ALL = "all"

    def __str__(self):
        return self.value

    @staticmethod
    def from_str(value: str):
        try:
            return TimeBucket[value.upper()]
        except KeyError:
            raise ValueError(f"'{value}' is not a valid time bucket")


class DataGroups:
    SCORING = "scoring"
    PREDICTIONS = "predictions"
    ACTUALS = "actuals"


class CustomMetricDirectionality:
    HIGHER_IS_BETTER = "higherIsBetter"
    LOWER_IS_BETTER = "lowerIsBetter"

    @classmethod
    def all(cls):
        return [cls.HIGHER_IS_BETTER, cls.LOWER_IS_BETTER]


class CustomMetricAggregationType:
    SUM = "sum"
    AVERAGE = "average"
    GAUGE = "gauge"

    @classmethod
    def all(cls):
        return [cls.SUM, cls.AVERAGE, cls.GAUGE]


class ExportType:
    PREDICTIONS = "predictions"
    ACTUALS = "actuals"

    @classmethod
    def all(cls):
        return [cls.PREDICTIONS, cls.ACTUALS]
