#
# Copyright 2024 DataRobot, Inc. and its affiliates.
#
# All rights reserved.
#
# DataRobot, Inc.
#
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
#
# Released under the terms of DataRobot Tool and Utility Agreement.
import json
import logging
from itertools import zip_longest
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from dmm.custom_metric import SingleMetricResult
from dmm.metric.metric_base import MetricBase

logger = logging.getLogger(__name__)

MISSING_COLUMN = (
    "Did not find {} column(s) in scoring data. This may be because the model does not produce the data, or "
    "all prompts for the given period not having this column (e.g. no response generated, no VDB attached)."
)


class PromptSimilarityMetricBase(MetricBase):
    """This is a base class for calculating distance between LLM prompt and context vectors.

    This class pulls the data out of the `prompt_column`, and an array from the contexts in the `context_column`. It
    leaves the `calculate_distance()` to be implemented by the derived class.

     A simple example class could look like this:
     .. code-block:: python

    class EuclideanMinMetric(PromptSimilarityMetricBase):
        def calculate_distance(self, prompt_vector: np.ndarray, context_vectors: List[np.ndarray]) -> np.float64:
            distances = [
                np.linalg.norm(prompt_vector - context_vector)
                for context_vector in context_vectors
            ]
            return min(distances)
    """

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt_column: str = "_LLM_PROMPT_VECTOR",
        context_column: str = "_LLM_CONTEXT",
        vector_field: str = "vector",
        metadata_field: str = "link",
        with_meta: bool = False,
    ):
        super().__init__(
            name=name,
            description=description,
            need_scoring_data=True,
            need_predictions=False,
            need_actuals=False,
            need_training_data=False,
        )
        self.prompt_column = prompt_column
        self.context_column = context_column
        self.vector_field = vector_field
        self.metadata_field = metadata_field
        self.with_meta = with_meta

    def calculate_distance(
        self,
        prompt_vector: np.ndarray,
        context_vectors: List[np.ndarray],
    ) -> np.float64:
        """
        Calculate the distance to be reported in the custom metrics for a single prompt-vector, and an array of
        context-vectors.

        Args:
            prompt_vector: a list of floats representing the prompt vector
            context_vectors: a list of lists of floats representing the `vector` fields of each larger context.

        Returns:
            A single float representing the distance between the prompt vector and the context vectors
        """
        raise NotImplementedError

    def calculate_distance_with_meta(
        self,
        prompt_vector: np.ndarray,
        context_vectors: List[np.ndarray],
        context_metadata: List[str],
    ) -> Tuple[np.float64, Optional[str]]:
        """
        Calculate the distance to be reported in the custom metrics for a single prompt-vector, and arrays of
        context-vectors and metadata.

        Args:
            prompt_vector: a list of floats representing the prompt vector
            context_vectors: a list of lists of floats representing the `vector` fields of each larger context.
            context_metadata: a list of strings representing the metadata field of each context.

        Returns:
            A float representing the distance between the prompt vector and the context vectors,
            and the corresponding metadata string (corresponding to the chosen context vector).
        """
        raise NotImplementedError

    def score(
        self,
        scoring_data: pd.DataFrame,
        timestamps: np.ndarray,
        association_ids: np.ndarray,
        **kwargs,
    ) -> List[SingleMetricResult]:
        """This calculates the distance between the prompt vector and the context vectors for each prediction."""
        missing = [
            column
            for column in (self.prompt_column, self.context_column)
            if column not in scoring_data.columns
        ]
        if missing:
            logger.error(MISSING_COLUMN.format(" and ".join(missing)))
            return []

        metric_results = []
        for p_str, c_str, ts, a_id in zip_longest(
            scoring_data[self.prompt_column],
            scoring_data[self.context_column],
            timestamps,
            association_ids,
        ):
            try:
                prompt = json.loads(p_str)
                context = json.loads(c_str)
            except (json.JSONDecodeError, TypeError):
                logger.debug(f"Decode failure for id={a_id}, timestamp={ts}")
                continue

            if not isinstance(prompt, list) or not isinstance(context, list):
                logger.debug(f"Invalid data for id={a_id}, timestamp={ts}")
                continue

            prompt_vector = np.array(prompt)

            context_vectors = []
            context_metadata = []
            for ctx_item in context:
                vector = ctx_item.get(self.vector_field)
                metatdata = ctx_item.get(self.metadata_field)
                if vector:
                    context_vectors.append(np.array(vector))
                    context_metadata.append(metatdata)

            # this calls into the derived class implementation for the calculation
            if self.with_meta:
                distance, metadata = self.calculate_distance_with_meta(
                    prompt_vector, context_vectors, context_metadata
                )
            else:
                distance = self.calculate_distance(prompt_vector, context_vectors)
                metadata = None
            metric_results.append(
                SingleMetricResult(
                    value=distance,
                    timestamp=ts,
                    association_id=a_id,
                    metadata=metadata,
                )
            )

        return metric_results
