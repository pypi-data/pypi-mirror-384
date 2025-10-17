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


class DataRobotAPIError(Exception):
    pass


class CustomMetricLimitExceeded(DataRobotAPIError):
    pass


class DuplicateCustomMetricName(DataRobotAPIError):
    pass


class DRCustomMetricConfigError(Exception):
    pass


class CustomMetricNotFound(Exception):
    pass


class ConflictError(Exception):
    pass


class DRSourceNotSupported(Exception):
    pass


class DataExportJobError(Exception):
    pass
