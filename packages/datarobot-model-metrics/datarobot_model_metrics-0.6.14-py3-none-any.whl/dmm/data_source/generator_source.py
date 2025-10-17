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
from datetime import datetime

import pandas as pd

from dmm.constants import ColumnName, TimeBucket
from dmm.data_source.data_source_base import DataSourceBase
from dmm.example_data_helper import timedelta_for_bucket


class GeneratorSource(DataSourceBase):
    """
    GeneratorSource is providing a way to generate endless data from a single dataframe
    """

    def __init__(
        self,
        df: pd.DataFrame,
        nr_buckets: int = 10,
        nr_chunks_per_bucket: int = 1,
        timestamp_col: ColumnName = ColumnName.TIMESTAMP,
    ):
        self._nr_rows_per_chunk = len(df)
        super().__init__(self._nr_rows_per_chunk)
        if len(df) <= 0:
            raise Exception(
                "df must contain rows, got {} rows".format(self._nr_rows_per_chunk)
            )

        self._nr_buckets = nr_buckets
        self._nr_chunks_per_bucket = nr_chunks_per_bucket
        self._timestamp_col = timestamp_col
        self._time_bucket = None
        self.reset()
        self._current_chunk_id = 0
        self._prev_chunk_datetime = None

        self._total_rows = (
            self._nr_buckets * self._nr_chunks_per_bucket * self._nr_rows_per_chunk
        )
        self._current_bucket = 0
        self._prev_bucket = 0
        self._current_chunk_in_bucket = 0
        self._df = df.drop(columns=[self._timestamp_col])
        self._datetime_object = datetime.strptime(
            "Jun 1 2022  1:00:00PM", "%b %d %Y %I:%M:%S%p"
        )

    def init(self, time_bucket: TimeBucket):
        self._time_bucket = time_bucket
        self.reset()
        return self

    def reset(self) -> None:
        self._current_row = 0
        self._current_chunk_id = 0
        self._current_bucket = 0
        self._prev_bucket = 0
        self._current_chunk_in_bucket = 0

    def get_data(self) -> (pd.DataFrame, int):
        if self._time_bucket is None:
            raise Exception("init() should be called before calling get_data()")

        # In case we are already done with this DF
        if self._current_bucket >= self._nr_buckets:
            return None, -1

        bucket_id_to_return = self._current_bucket
        df = self._generate_chunk_data()

        # Preparing for next get data
        self._current_chunk_in_bucket += 1
        self._prev_bucket = self._current_bucket
        if self._current_chunk_in_bucket >= self._nr_chunks_per_bucket:
            self._current_chunk_in_bucket = 0
            self._current_bucket += 1

        self._current_row += self._nr_rows_per_chunk
        return df, bucket_id_to_return

    def _generate_chunk_data(self) -> pd.DataFrame:
        # Generating data for the current bucket and chunk in bucket
        if self._prev_bucket != self._current_bucket:
            timedelta_obj = timedelta_for_bucket(self._time_bucket)
            self._datetime_object += timedelta_obj

        df = self._df
        df[self._timestamp_col] = self._datetime_object.strftime("%d/%m/%Y %H:%M:%S.%f")
        return df
