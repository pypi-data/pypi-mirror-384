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
from datetime import datetime, timedelta
from typing import List, Tuple, Union

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from dmm.constants import ColumnName, TimeBucket


def timedelta_for_bucket(time_bucket: TimeBucket) -> Union[timedelta, relativedelta]:
    if time_bucket == TimeBucket.SECOND:
        return timedelta(seconds=1)
    elif time_bucket == TimeBucket.MINUTE:
        return timedelta(minutes=1)
    elif time_bucket == TimeBucket.HOUR:
        return timedelta(hours=1)
    elif time_bucket == TimeBucket.DAY:
        return timedelta(days=1)
    elif time_bucket == TimeBucket.WEEK:
        return timedelta(weeks=1)
    elif time_bucket == TimeBucket.MONTH:
        return relativedelta(months=1)
    elif time_bucket == TimeBucket.ALL:
        return timedelta(seconds=0)
    else:
        raise Exception(f"Time Bucket {time_bucket} is not supported")


def gen_timestamps_list(
    nr_rows: int, time_bucket: TimeBucket, rows_per_time_bucket: int
) -> List[Tuple[str]]:
    timedelta_obj = timedelta_for_bucket(time_bucket)
    datetime_object = datetime.strptime("Jun 1 2005  1:00:00PM", "%b %d %Y %I:%M:%S%p")
    timestamps = []
    for row in range(nr_rows):
        if row % rows_per_time_bucket == 0 and row != 0:
            datetime_object += timedelta_obj
        timestamp_str = (datetime_object.strftime("%d/%m/%Y %H:%M:%S.%f"),)
        timestamps.append(timestamp_str)
    return timestamps


def gen_dataframe_for_accuracy_metric(
    nr_rows: int = 1000,
    timestamp_col: ColumnName = ColumnName.TIMESTAMP,
    with_predictions: bool = True,
    prediction_col: ColumnName = ColumnName.PREDICTIONS,
    with_actuals: bool = True,
    actuals_col: ColumnName = ColumnName.ACTUALS,
    with_dr_timestamp_column: bool = False,
    dr_timestamp_column: ColumnName = ColumnName.DR_TIMESTAMP_COLUMN,
    with_association_id: bool = False,
    association_id_col: ColumnName = ColumnName.ASSOCIATION_ID_COLUMN,
    positive_label: str = None,
    label_column: ColumnName = ColumnName.LABEL,
    prediction_value: int = None,
    random_predictions: bool = False,
    time_bucket: TimeBucket = TimeBucket.MINUTE,
    rows_per_time_bucket: int = 100,
    prediction_actual_diff: float = 0.001,
) -> pd.DataFrame:
    """
    Generate a dataframe for testing
    :param nr_rows: Number of rows to generate
    :param with_predictions: Add predictions to the data
    :param prediction_col: Name of prediction column
    :param prediction_value: A fixed value to use for predictions
    :param random_predictions: If True generate random predictions instead of a fixed value
    :param with_actuals: Add actuals column to the data
    :param actuals_col: Name of actuals column
    :param with_association_id: Add association id column to the data
    :param association_id_col: Name of association id column
    :param positive_label: If specified, will add a column with a positive label
    :param label_column: Name of label column
    :param with_dr_timestamp_column: Add predictions timestamp column to the data
    :param dr_timestamp_column: Name of predictions timestamp column
    :param time_bucket: Time bucket to generate predictions for
    :param rows_per_time_bucket: How many rows per time bucket to generate
    :param prediction_actual_diff: diff between predictions and actuals
    :param timestamp_col: Name of timestamp column
    :return: Dataframe with the generated data
    """

    timestamps = gen_timestamps_list(nr_rows, time_bucket, rows_per_time_bucket)
    df = pd.DataFrame(timestamps, columns=[timestamp_col])

    if prediction_value:
        predictions = np.full(nr_rows, prediction_value)
    elif random_predictions:
        predictions = np.random.randint(1, 10, size=nr_rows)
    else:
        predictions = [x for x in range(nr_rows)]

    if with_predictions:
        df[prediction_col] = np.array(predictions)
    if with_actuals:
        df[actuals_col] = [x - prediction_actual_diff for x in predictions]
    if with_association_id:
        df[association_id_col] = [x for x in range(nr_rows)]
    if with_dr_timestamp_column:
        df[dr_timestamp_column] = df[timestamp_col]
    if positive_label:
        df[label_column] = [positive_label for _ in range(nr_rows)]

    return df


def gen_dataframe_for_batch_tests(
    nr_rows: int = 1000,
    batch_id_col: ColumnName = ColumnName.DR_BATCH_ID_COLUMN,
    timestamp_col: ColumnName = ColumnName.TIMESTAMP,
    with_predictions: bool = True,
    prediction_col: ColumnName = ColumnName.PREDICTIONS,
    with_dr_timestamp_column: bool = False,
    dr_timestamp_column: ColumnName = ColumnName.DR_TIMESTAMP_COLUMN,
    prediction_value: int = None,
    random_predictions: bool = False,
    rows_per_batch: int = 100,
) -> (pd.DataFrame, List[str]):
    """
    Generate a dataframe for testing
    :param nr_rows: Number of rows to generate
    :param batch_id_col: Name of batch ID column
    :param with_predictions: Add predictions to the data
    :param prediction_col: Name of prediction column
    :param prediction_value: A fixed value to use for predictions
    :param random_predictions: If True generate random predictions instead of a fixed value
    :param with_dr_timestamp_column: Add predictions timestamp column to the data
    :param dr_timestamp_column: Name of predictions timestamp column
    :param rows_per_batch: How many rows per batch to generate
    :param timestamp_col: Name of timestamp column
    :return: (Dataframe with the generated data, List of batch ids)
    """
    batch_ids = [f"batch {i // rows_per_batch + 1}" for i in range(nr_rows)]
    df = pd.DataFrame(
        ["01/06/2005 13:00:00.000000"] * nr_rows,
        columns=[timestamp_col],
    )
    df[batch_id_col] = batch_ids

    if prediction_value:
        predictions = np.full(nr_rows, prediction_value)
    elif random_predictions:
        predictions = np.random.randint(1, 10, size=nr_rows)
    else:
        predictions = [x for x in range(nr_rows)]

    if with_predictions:
        df[prediction_col] = np.array(predictions)
    if with_dr_timestamp_column:
        df[dr_timestamp_column] = df[timestamp_col]

    return df, list(set(batch_ids))


def gen_dataframe_for_data_metrics(
    nr_rows: int = 1000,
    time_bucket: TimeBucket = TimeBucket.MINUTE,
    rows_per_time_bucket: int = 100,
    columns: Tuple = ("A", "B"),
    add_missing_values: int = 0,
) -> pd.DataFrame:
    if add_missing_values > nr_rows:
        raise Exception(
            f"Number of missing values requested {add_missing_values} > number of rows {rows_per_time_bucket}"
        )

    timestamps = gen_timestamps_list(
        nr_rows=nr_rows,
        time_bucket=time_bucket,
        rows_per_time_bucket=rows_per_time_bucket,
    )
    df = pd.DataFrame(timestamps, columns=[ColumnName.TIMESTAMP])

    for col_name in columns:
        df[col_name] = range(nr_rows)

    return df
