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

from dmm.constants import ColumnName
from dmm.data_source.data_source_base import DataSourceBase
from dmm.time_bucket import check_if_in_same_time_bucket


class DataFrameSource(DataSourceBase):
    """DataSource that fetches data from a DataFrame.

    Args:
        df: Pandas Dataframe.
        max_rows: Maximum number of rows to process at once.
        timestamp_col: Column in DataFrame which contains timestamps.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        max_rows: int = 10000,
        timestamp_col: ColumnName = ColumnName.TIMESTAMP,
    ) -> None:
        super().__init__(max_rows)
        if max_rows <= 0:
            raise ValueError(f"max_rows must be > 0, got {max_rows}")

        self._df = self._preprocess_df(df.copy(), timestamp_col)
        self._max_rows = max_rows
        self._timestamp_col = timestamp_col
        self._prev_chunk_datetime = None
        self.reset()

    @staticmethod
    def _preprocess_df(df: pd.DataFrame, timestamp_col: str) -> pd.DataFrame:
        if not isinstance(df[timestamp_col].iloc[0], pd.Timestamp):
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])

        if not df[timestamp_col].is_monotonic_increasing:
            df.sort_values(by=timestamp_col, inplace=True, ignore_index=True)

        return df

    def init(self, time_bucket):
        self._time_bucket = time_bucket
        self.reset()
        return self

    def reset(self) -> None:
        self._current_row = 0
        self._current_chunk_id = 0

    def get_data(self) -> (pd.DataFrame, int):
        if self._current_row >= len(self._df):
            return None, -1

        rows_list = [self._df.iloc[self._current_row].to_dict()]
        self._current_row += 1
        chunk_start_datetime = self._df.at[self._current_row - 1, self._timestamp_col]

        if self._prev_chunk_datetime:
            # This is for the case where the boundaries of chunks are aligned with the max rows
            if not check_if_in_same_time_bucket(
                self._prev_chunk_datetime, chunk_start_datetime, self._time_bucket
            ):
                self._current_chunk_id += 1

        self._prev_chunk_datetime = chunk_start_datetime

        if self._current_row >= self._df.shape[0]:
            return pd.DataFrame(rows_list), self._current_chunk_id

        search_end_row = min(self._current_row + self._max_rows - 1, self._df.shape[0])
        for loc in range(self._current_row, search_end_row):
            loc_datetime = self._df.at[loc, self._timestamp_col]

            if check_if_in_same_time_bucket(
                chunk_start_datetime, loc_datetime, self._time_bucket
            ):
                rows_list.append(self._df.iloc[loc].to_dict())
                self._current_row += 1
            else:
                break

        return pd.DataFrame(rows_list), self._current_chunk_id

    def get_all_data(self) -> pd.DataFrame:
        result, chunk_id = self.get_data()
        while chunk_id != -1:
            df, chunk_id = self.get_data()
            if df is not None:
                result = pd.concat([result, df])
        return result
