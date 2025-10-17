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
import pandas as pd

from dmm.metric.metric_base import DataMetricBase


class MissingValuesFraction(DataMetricBase):
    """
    Metric that calculates the fraction of missing values for a specific feature
    Scoring data is required
    """

    def __init__(self, feature_name):
        super().__init__(
            name="Missing Values Fraction",
            description="Fraction of missing values for a specific feature",
            need_training_data=False,
        )

        self.feature_name = feature_name

    def __str__(self):
        return "Missing Values Fraction: feature_name: {}".format(self.feature_name)

    def score(self, scoring_data: pd.DataFrame, **kwargs) -> float:
        if self.feature_name not in scoring_data.columns:
            raise Exception(
                f"Feature name {self.feature_name} is not in DF columns: {scoring_data.columns}"
            )
        return scoring_data[self.feature_name].isna().mean()
