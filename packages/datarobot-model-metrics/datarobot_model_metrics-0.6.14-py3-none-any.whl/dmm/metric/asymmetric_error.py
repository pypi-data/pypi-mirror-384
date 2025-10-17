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
import numpy as np
from sklearn.metrics import mean_absolute_error

from dmm.metric.metric_base import ModelMetricBase


class AsymmetricError(ModelMetricBase):
    """
    Metric that calculates the asymmetric error based on the mean absolute error between predictions and actuals
    """

    def __init__(self, above_weight=2, below_weight=1):
        super().__init__(
            name="Asymmetric Error",
            description="Asymmetric error between predictions and actuals",
            need_training_data=False,
        )
        self.above_weight = above_weight
        self.below_weight = below_weight

    def score(self, predictions: np.ndarray, actuals: np.ndarray, **kwargs) -> float:
        # Edge cases are all actuals above predictions or all actuals below predictions
        above_mask = predictions > actuals
        true_count = above_mask.sum()

        if true_count == 0:
            above_point = 0
            n_above = 0
        else:
            above_point, n_above = (
                mean_absolute_error(actuals[above_mask], predictions[above_mask]),
                above_mask.sum(),
            )

        if true_count == len(predictions):
            below_point = 0
            n_below = 0
        else:
            below_point, n_below = (
                mean_absolute_error(actuals[~above_mask], predictions[~above_mask]),
                len(predictions) - n_above,
            )

        weighted_error = np.average(
            [above_point, below_point],
            weights=[self.above_weight * n_above, self.below_weight * n_below],
        )

        return weighted_error
