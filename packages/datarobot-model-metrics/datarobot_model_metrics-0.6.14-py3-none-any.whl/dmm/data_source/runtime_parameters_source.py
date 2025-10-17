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

from dmm import ColumnName
from dmm.data_source.data_source_base import DataSourceBase
from dmm.utils import RunTimeParameterHandler


class RuntimeParametersDataSource(DataSourceBase):
    """This is a special case datasource that constructs a dataframe from
    the data passed in the runtime parameters. This is specifically for the custom llm
    assessment case where only a single prompt response is being scored outside a deployment
    """

    def __init__(self, parameters: RunTimeParameterHandler):
        super().__init__(max_rows=1)
        self._parameters = parameters
        self.reset()

    def init(self, time_bucket):
        self._time_bucket = time_bucket
        self.reset()
        return self

    def reset(self) -> None:
        self._current_row = 0

    def get_data(self) -> (pd.DataFrame, int):
        if self._current_row >= 1:
            return None, -1

        df = pd.DataFrame()
        for possible_column in ColumnName.llm_column_names():
            value = getattr(self._parameters, possible_column)
            if value:
                df[possible_column] = [value]
        df[ColumnName.TIMESTAMP] = 0  # dummy timestamp needed by evaluator
        self._current_row += 1
        return df, 0
