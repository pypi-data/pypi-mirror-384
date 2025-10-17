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

from dmm import TimeBucket

SECONDS = 60
SECONDS_IN_HOUR = SECONDS * SECONDS
SECONDS_IN_DAY = 24 * SECONDS_IN_HOUR
SECONDS_IN_WEEK = SECONDS_IN_DAY * 7


def check_if_in_same_time_bucket(
    date1: datetime, date2: datetime, time_bucket: TimeBucket
) -> bool:
    """
    Check if 2 date objects are in the same time bucket
    :param date1:
    :param date2:
    :param time_bucket:
    :return: True if in same time bucket, False otherwise.
    """

    timedelta_obj = date2 - date1
    total_seconds = abs(timedelta_obj.total_seconds())
    if time_bucket == TimeBucket.MINUTE:
        if total_seconds >= SECONDS:
            return False
        if date1.minute != date2.minute:
            return False
        return True
    if time_bucket == TimeBucket.HOUR:
        if total_seconds >= SECONDS_IN_HOUR:
            return False
        if date1.hour != date2.hour:
            return False
        return True
    if time_bucket == TimeBucket.DAY:
        if total_seconds >= SECONDS_IN_DAY:
            return False
        if date1.day != date2.day:
            return False
        if date1.month != date2.month:
            return False
        return True
    if time_bucket == TimeBucket.WEEK:
        if total_seconds >= SECONDS_IN_WEEK:
            return False
        if date1.isocalendar()[1] != date2.isocalendar()[1]:
            return False
        return True
    if time_bucket == TimeBucket.MONTH:
        if date1.month != date2.month:
            return False
        return True
    if time_bucket == TimeBucket.QUARTER:
        if pd.Timestamp(date1).quarter != pd.Timestamp(date2).quarter:
            return False
        return True
    if time_bucket == TimeBucket.SECOND:
        if total_seconds >= 1:
            return False
        return True

    if time_bucket == TimeBucket.ALL:
        return True

    raise Exception(f"Time bucket {time_bucket} is not supported")


def check_if_in_same_time_bucket_vectorized(
    date1: pd.Series, date2: datetime, time_bucket: TimeBucket
) -> pd.Series:
    """
    For each date in date1, check if it is in the same time bucket as date2
    :param date1:
    :param date2:
    :param time_bucket:
    :return: True if in same time bucket, False otherwise.
    """

    if time_bucket == TimeBucket.ALL:
        return pd.Series(True, index=date1.index)

    if time_bucket == TimeBucket.MONTH:
        return date1.dt.month == date2.month

    if time_bucket == TimeBucket.QUARTER:
        return date1.dt.quarter == pd.Timestamp(date2).quarter

    timedelta_obj = (date2 - date1).dt
    total_seconds = abs(timedelta_obj.total_seconds())
    if time_bucket == TimeBucket.SECOND:
        return total_seconds < 1
    if time_bucket == TimeBucket.MINUTE:
        return (total_seconds < SECONDS) & (date1.dt.minute == date2.minute)
    if time_bucket == TimeBucket.HOUR:
        return (total_seconds < SECONDS_IN_HOUR) & (date1.dt.hour == date2.hour)
    if time_bucket == TimeBucket.DAY:
        return (
            (total_seconds < SECONDS_IN_DAY)
            & (date1.dt.day == date2.day)
            & (date1.dt.month == date2.month)
        )
    if time_bucket == TimeBucket.WEEK:
        return (total_seconds < SECONDS_IN_WEEK) & (
            date1.dt.isocalendar()["week"] == date2.isocalendar()[1]
        )

    raise Exception(f"Time bucket {time_bucket} is not supported")
