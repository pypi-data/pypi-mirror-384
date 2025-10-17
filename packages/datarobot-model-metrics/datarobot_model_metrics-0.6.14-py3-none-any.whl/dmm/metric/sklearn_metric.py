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

from dmm.metric.metric_base import MetricBase


class SklearnMetric(MetricBase):
    """If passed a string, will look it up in sklearn.metrics and build a metric based on that."""

    def __init__(self, metric: str, name: str = None):
        super().__init__(
            name=name if name else metric,
            description=f"A metric based on sklearn.metrics.{metric}.",
            # all sklearn metrics are what we would call model quality metrics and take only actuals and predictions
            need_predictions=True,
            need_actuals=True,
            need_scoring_data=False,
            need_training_data=False,
        )

        try:
            from sklearn import metrics

            self._metric = getattr(metrics, metric)
        except (ImportError, AttributeError) as e:
            if isinstance(e, ImportError):
                error_msg = (
                    f"cannot shortcut metric {metric} because scikit-learn cannot be found. "
                    f"Install it to use sklearn metrics."
                )
            elif isinstance(e, AttributeError):
                error_msg = (
                    f"cannot shortcut metric {metric} because it is not a valid sklearn metric. "
                    f'Valid sklearn metrics in your version include: {", ".join(metrics.__all__)}'
                )
            else:
                error_msg = str(e)
            raise ValueError("Tried to build a scikit-learn metric, but " + error_msg)

    def score(
        self,
        predictions: np.ndarray,
        actuals: np.ndarray,
        **kwargs,
    ) -> float:
        try:
            return self._metric(
                np.array(actuals).astype(float).flatten(),
                np.array(predictions).astype(float).flatten(),
            )
        except Exception as e:
            raise ValueError(
                f"Could not apply metric {self.name}, make sure you are passing the right data (see the sklearn docs). "
                f"The error message was: {str(e)}"
            )
