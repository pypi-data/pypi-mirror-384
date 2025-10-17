# Copyright 2024 DataRobot, Inc. and its affiliates.
#
# All rights reserved.
#
# This is proprietary source code of DataRobot, Inc. and its affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.
import logging
import re
from typing import Dict, List, Optional, Union

LEVEL_MAP = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}

DR_PREFIXES = ["dmm", "datarobot"]

log = logging.getLogger(__name__)


def find_level_value(name: str) -> Optional[int]:
    """Maps log-level name to a numeric value."""
    return LEVEL_MAP.get(name.upper(), None)


def find_level_name(value: int) -> Optional[str]:
    """Maps log-level value to name."""
    for level_name, level_value in LEVEL_MAP.items():
        if value == level_value:
            return level_name

    return None


def get_log_levels() -> Dict[str, str]:
    """Get a dictionary of logger names to the log level names."""
    result = {}
    for log_name, logger in logging.root.manager.loggerDict.items():
        if not hasattr(logger, "getEffectiveLevel"):
            # some items are place-holders due to subclass loggers without one for this class
            continue

        level_value = logger.getEffectiveLevel()
        level_name = find_level_name(level_value)
        if level_name:
            result[log_name] = level_name

    return result


def set_logger_level(name: str, level: int, propagate: bool = True) -> List[str]:
    """Set the log level of the specified name, and sub-loggers if propagate is True."""
    changed = []

    for log_name, logger in logging.root.manager.loggerDict.items():
        # ignore items not matching the pattern
        if log_name != name and not (propagate and log_name.startswith(name)):
            continue

        if not hasattr(logger, "setLevel"):
            # some items are place-holders due to subclass loggers without one for this class
            continue

        logger.setLevel(level)
        changed.append(log_name)

    return changed


def initialize_loggers(
    log_levels: Union[List[str], str, None] = None,
    log_format: Optional[str] = None,
) -> None:
    """
    Initialize logging based on provided on specified info.
    """
    # always set the logging format
    fmt = log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=fmt, datefmt="%Y-%m-%d %I:%M:%S %p")

    # if no log levels specified, there's nothing to be done
    if not log_levels:
        return

    if isinstance(log_levels, str):
        items = re.split(r"[\s,]+", log_levels)
    else:
        items = [_.strip() for _ in log_levels if _]

    for item in items:
        # item may be of the form NAME:LEVEL, or just LEVEL
        parts = item.split(":")
        if len(parts) == 2:
            level = find_level_value(parts[1])
            log_names = [parts[0]]
        elif len(parts) == 1:
            level = find_level_value(parts[0])
            log_names = DR_PREFIXES
        else:
            log.error(
                f"Invalid log format specified '{item}' -- please use LEVEL or NAME:LEVEL."
            )
            continue

        if level is None:
            log.error(f"Invalid log level specified in {item}")
            continue

        changes = []
        for name in log_names:
            changes.extend(set_logger_level(name, level, propagate=True))
        if not changes:
            log.warning(f"No changes detected for {item}")
        else:
            log.debug(f"Set {len(changes)} loggers for '{item}': {', '.join(changes)}")

    return
