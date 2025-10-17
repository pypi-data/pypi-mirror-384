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

from dmm import TimeBucket


class DataSourceBase(object):
    """
    A Data Source is an abstraction that allows implementing multiple data provides for metric evaluation.
    To evaluate a metric the data is required to be chunked in the following way:
      1. Respect time bucket boundaries
      2. Respect max_rows boundaries.

    The data source object should fetch the data and provide chunks with the above rules respected.
    For example if the data source is configured to work in Minute bases buckets and 2 max rows, then
    given the following data
    Row  Time:      value
    0    16:00:01      5
    1    16:00:15      6
    2    16:00:30      4.5
    3    16:01:05      3.2

    Then we should get 3 chunks:
    1. rows 0,1  (2 lines in the same minute bucket)
    2. row 2 (1 line in the previous minute bucket)
    3. row 3 (1 line in a new minute bucket)

    """

    def __init__(self, max_rows: int):
        self._time_bucket = TimeBucket.ALL
        self._max_rows = max_rows

    def init(self, time_bucket: TimeBucket):
        """
        Init function will be called prior to calling getting data by the Metric Evaluator runner.
        The idea is that the metric evaluator is driving the time bucket definition.
        """
        raise NotImplemented

    @property
    def time_bucket(self) -> TimeBucket:
        return self._time_bucket

    @property
    def max_rows(self) -> int:
        return self._max_rows

    def reset(self):
        """
        If supported, reset the data source to the beginning of the data
        """
        raise NotImplemented

    def get_data(self) -> (pd.DataFrame, int):
        """
        Return a chunk of data that can be sent to a metric object to be transformed.
        Following conditions should be respected:
            1. The chunk of data is in the same time bucket
            2. The chunk of data does not contain more than max_rows
        :return: a DataFrame if there is more data to process, or None. And also the id of the time bucket
        """
        raise NotImplemented
