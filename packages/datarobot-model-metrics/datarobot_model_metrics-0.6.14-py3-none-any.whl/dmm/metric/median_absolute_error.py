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
from dmm.metric.sklearn_metric import SklearnMetric


class MedianAbsoluteError(SklearnMetric):
    """
    Metric that calculates the median absolute error of the difference between predictions and actuals
    """

    def __init__(self):
        super().__init__(
            metric="median_absolute_error",
        )
