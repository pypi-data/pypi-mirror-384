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
import logging
import os
import sys
from argparse import Action, ArgumentError, ArgumentParser, ArgumentTypeError, Namespace
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Type, Union

from dateutil.parser import parse as date_parse

from dmm.constants import TimeBucket
from dmm.log_manager import find_level_value

logger = logging.getLogger(__name__)


ENV_API_KEY = "API_KEY"
ENV_BASE_URL = "BASE_URL"
ENV_DEPLOYMENT_ID = "DEPLOYMENT_ID"
ENV_CUSTOM_METRIC_ID = "CUSTOM_METRIC_ID"
ENV_MODEL_ID = "MODEL_ID"
ENV_PROMPT_COLUMN = "PROMPT_COLUMN"
ENV_ENCODING_NAME = "ENCODING_NAME"
ENV_DRY_RUN = "DRY_RUN"
ENV_START_TS = "START_TS"
ENV_END_TS = "END_TS"
ENV_LAST_RUN_TS = "LAST_SUCCESSFUL_RUN_TS"
ENV_CURRENT_RUN_TS = "CURRENT_RUN_TS"
ENV_MAX_ROWS = "MAX_ROWS"
ENV_LOG = "LOG"
ENV_PREVIEW_LENGTH = "PREVIEW_LENGTH"
ENV_MIN_WORDS = "MIN_WORDS"
ENV_TOP_PERCENT = "TOP_PERCENT"
ENV_RESULT_FILE = "RESULT_FILE"
ENV_TIME_BUCKET = "TIME_BUCKET"
ENV_DATAROBOT_ENDPOINT = "DATAROBOT_ENDPOINT"
ENV_DATAROBOT_API_TOKEN = "DATAROBOT_API_TOKEN"

STAGING_URL = "https://staging.datarobot.com/api/v2"
PROD_URL = "https://app.datarobot.com/api/v2"

DEFAULT_LOG_LEVEL = "WARNING"


def ranged_type(value_type: Type, min_value: Any, max_value: Any):
    """This sets can be used as the `type` argument in the ArgumentParser.add_argument() call.

    When invoked, it converts the `arg` string to the specified `type` and checks that
    it is between `min_value` and `max_value`.
    """

    def range_checker(arg: str) -> Any:
        try:
            # the extra conversion works around the job putting "int" values into the environment with trailing '.0'
            value = value_type(float(arg))

            # and this checks for loss of specified digits
            if float(value) != float(arg):
                raise ArgumentTypeError(f"bad conversion {value} != {float(arg)}")
        except ValueError:
            raise ArgumentTypeError(f"'{arg}' is not a valid {value_type.__name__}.")
        if value < min_value or value > max_value:
            raise ArgumentTypeError(
                f"'{arg}' is out of range -- must be between {min_value} and {max_value}."
            )
        return value

    return range_checker


class CustomMetricArgumentParser(ArgumentParser):
    """
    Wrapper around ArgumentParser class to provide some standard custom metrics arguments.

    The intention with this class is to provide consumers with feedback and help about the required fields instead
    of reading from the environment in "random" places. The `--help` option allows users to see the expected
    values.

    Users can add values to an instance of this using standard ArgumentParser.add_argument() calls.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.required_properties = {}

    @staticmethod
    def default_from_env(
        variable_name: str, default_value: Optional[str] = None
    ) -> Optional[str]:
        return os.environ.get(variable_name, default_value)

    @staticmethod
    def default_from_env_list(
        variables: List[str], default_value: Optional[str] = None
    ) -> Optional[str]:
        for variable in variables:
            value = os.environ.get(variable)
            if value is not None:
                return value
        return default_value

    @staticmethod
    def boolean_from_env(variable_name: str, default_bool: bool = False) -> bool:
        text = os.environ.get(variable_name, None)
        if text is None:
            return default_bool
        return text.lower() in ["true", "t", "yes", "y", "1"]

    @staticmethod
    def help_with_variable(
        base_help: Optional[str],
        variable_name: str,
        show_default: bool = False,
        required: bool = False,
    ) -> str:
        if base_help and base_help.strip():
            help_text = base_help.strip()
        else:
            parts = [_.lower() for _ in variable_name.split("_") if _.strip()]
            parts[0] = parts[0].title()
            help_text = " ".join(parts)
        if not help_text.endswith("."):
            help_text += ". "
        help_text += f"Settable via '{variable_name}'"
        if show_default:
            help_text += " (default: %(default)s)"
        if required:
            help_text += ", required"
        return help_text + "."

    def append_required(self, property_name: str, variable_name: str) -> None:
        """The 'required_properties' is a map of properties to environment variables that must NOT be empty.

        This cannot be done using the parser.add_argument(required=True), since that requires
        the user to provide the properties, and in many cases we will pick up the value from the
        environment variable (instead of requiring the user to add it to the arguments).
        """
        self.required_properties.update({property_name: variable_name})

    def required_property_help(self) -> str:
        nl = "\n    "
        return f"Required properties:{nl}{nl.join(self.required_properties.values())}"

    def parse_args(self, args=None, namespace=None) -> Namespace:
        """Overrides the ArgumentParser.parse_args() to provide checking for 'required_properties'."""
        namespace = super().parse_args(args, namespace)
        if hasattr(namespace, "list_required") and namespace.list_required:
            print(self.required_property_help())
            sys.exit(0)

        missing_variables = [
            variable_name
            for property_name, variable_name in self.required_properties.items()
            if not getattr(namespace, property_name)
        ]
        if missing_variables:
            raise ArgumentError(
                argument=None,
                message=f"Missing required environment variables: {', '.join(missing_variables)}",
            )

        return namespace

    @staticmethod
    def variable_to_option(variable_name: str) -> str:
        return "--" + variable_name.lower().replace("_", "-")

    @staticmethod
    def variable_to_dest(variable_name: str) -> str:
        return variable_name.lower().replace("-", "_")

    def add_environment_arg(
        self,
        variable_name: str,
        default_value: Optional[str] = None,
        help_base: Optional[str] = None,
        show_default: bool = True,
        required_property: bool = False,
        **kwargs: Any,
    ) -> Action:
        option = self.variable_to_option(variable_name)

        # adds the destination, if none provided
        dest = kwargs.pop("dest", None)
        if not dest:
            dest = self.variable_to_dest(variable_name)
            kwargs["dest"] = dest
        if kwargs.pop("required", False):
            required_property = True
        if required_property:
            self.append_required(dest, variable_name)
        if "help" not in kwargs:
            help_text = self.help_with_variable(
                help_base, variable_name, show_default, required_property
            )
            kwargs["help"] = help_text
        if "default" not in kwargs:
            kwargs["default"] = self.default_from_env(variable_name, default_value)
        if "metavar" not in kwargs:
            if variable_name.endswith("_ID"):
                kwargs["metavar"] = "ID"
            if variable_name.endswith("_TS"):
                kwargs["metavar"] = "TIMESTAMP"
            if variable_name.endswith("_NAME"):
                kwargs["metavar"] = "NAME"
            if variable_name.endswith("_COLUMN"):
                kwargs["metavar"] = "COLUMN"
            if variable_name.endswith("_COUNT"):
                kwargs["metavar"] = "COUNT"
            if variable_name.endswith("_PERCENT"):
                kwargs["metavar"] = "PERCENT"

        return self.add_argument(option, **kwargs)

    def add_environment_flag(
        self,
        variable_name: str,
        default_value: bool = False,
        help_base: Optional[str] = None,
        show_default: bool = True,
        required_property: bool = False,
        **kwargs: Any,
    ) -> Action:
        if "action" not in kwargs:
            kwargs["action"] = "store_false" if default_value else "store_true"
        if "default" not in kwargs:
            kwargs["default"] = self.boolean_from_env(variable_name, default_value)
        return self.add_environment_arg(
            variable_name,
            help_base=help_base,
            show_default=show_default,
            required_property=required_property,
            **kwargs,
        )

    def add_deployment(self) -> Action:
        return self.add_environment_arg(
            variable_name=ENV_DEPLOYMENT_ID,
            help_base="Deployment ID",
            required_property=True,
        )

    def add_custom_metric(self) -> Action:
        return self.add_environment_arg(
            variable_name=ENV_CUSTOM_METRIC_ID,
            help_base="Custom metric ID",
            required_property=True,
        )

    def add_model(self) -> Action:
        return self.add_environment_arg(
            ENV_MODEL_ID, help_base="Model ID. Uses champion model if not provided"
        )

    def dry_run_value(self) -> bool:
        return self.boolean_from_env(ENV_DRY_RUN)

    def add_dry_run(self) -> Action:
        return self.add_environment_flag(ENV_DRY_RUN, help_base="Dry run")

    def default_start_ts(self, default_delta: timedelta) -> datetime:
        start_ts = self.default_from_env(ENV_START_TS)
        if start_ts:
            return date_parse(start_ts)
        start_ts = self.default_from_env(ENV_LAST_RUN_TS)
        if not self.dry_run_value() and start_ts:
            return date_parse(start_ts)
        return datetime.now(timezone.utc) - default_delta

    def add_start_ts(self, default_delta: timedelta = timedelta(days=1)) -> Action:
        return self.add_argument(
            "--start-ts",
            dest="start_ts",
            metavar="TIMESTAMP",
            default=self.default_start_ts(default_delta),
            type=date_parse,
            help=f"Start timestamp. Settable with '{ENV_START_TS}', or '{ENV_LAST_RUN_TS}' (when not dry run). Default is %(default)s",
        )

    def default_end_ts(self) -> Optional[datetime]:
        end_ts = self.default_from_env(ENV_END_TS) or self.default_from_env(
            ENV_CURRENT_RUN_TS
        )
        if not end_ts:
            return datetime.now(timezone.utc)
        return date_parse(end_ts)

    def add_end_ts(self) -> Action:
        return self.add_argument(
            "--end-ts",
            dest="end_ts",
            metavar="TIMESTAMP",
            default=self.default_end_ts(),
            type=date_parse,
            help=f"End timestamp. Settable with '{ENV_END_TS}' or '{ENV_CURRENT_RUN_TS}'. Default is %(default)s.",
        )

    def add_prompt_column(self, default_prompt: Optional[str] = "prompt") -> Action:
        return self.add_environment_arg(
            variable_name=ENV_PROMPT_COLUMN,
            default_value=default_prompt,
            required_property=True,
        )

    def add_encoding_name(
        self, default_encoding: Optional[str] = "cl100k_base"
    ) -> Action:
        return self.add_environment_arg(
            variable_name=ENV_ENCODING_NAME,
            default_value=default_encoding,
            required_property=True,
        )

    def add_api_key(self) -> Action:
        self.append_required("api_key", ENV_API_KEY)
        return self.add_argument(
            self.variable_to_option(ENV_API_KEY),
            self.variable_to_option(ENV_DATAROBOT_API_TOKEN),
            dest=self.variable_to_dest(ENV_API_KEY),
            metavar="KEY",
            default=self.default_from_env_list([ENV_API_KEY, ENV_DATAROBOT_API_TOKEN]),
            help=f"API key used to authenticate to server. Settable via '{ENV_API_KEY}' or '{ENV_DATAROBOT_API_TOKEN}', required.",
        )

    def add_base_url(self) -> Action:
        self.append_required("base_url", ENV_BASE_URL)
        return self.add_argument(
            self.variable_to_option(ENV_BASE_URL),
            self.variable_to_option(ENV_DATAROBOT_ENDPOINT),
            dest=self.variable_to_dest(ENV_BASE_URL),
            metavar="URL",
            default=self.default_from_env_list(
                [ENV_BASE_URL, ENV_DATAROBOT_ENDPOINT], STAGING_URL
            ),
            help=f"URL for server. Settable via '{ENV_BASE_URL}' or '{ENV_DATAROBOT_ENDPOINT}' (default: %(default)s), required.",
        )

    def add_max_rows(self, default_value: int = 100000) -> Action:
        return self.add_environment_arg(
            variable_name=ENV_MAX_ROWS,
            help_base="Maximum number of rows",
            type=ranged_type(int, 0, 10000000),
            default_value=str(default_value),
            metavar="ROWS",
        )

    def add_time_bucket(self, default_value: str = "hour") -> Action:
        return self.add_environment_arg(
            variable_name=ENV_TIME_BUCKET,
            default_value=str(default_value).lower(),
            type=TimeBucket.from_str,
            help_base="Time bucket used for time series. Options are: %(choices)s",
            choices=list(TimeBucket),
            metavar="BUCKET",
        )

    def add_required_flag(self):
        return self.add_argument(
            "--required",
            dest="list_required",
            action="store_true",
            help="List the required properties and exit.",
        )

    def add_logging(self, default_value: str = DEFAULT_LOG_LEVEL) -> Action:
        return self.add_environment_arg(
            variable_name=ENV_LOG,
            help_base="Logging level list",
            default_value=default_value,
            show_default=True,
            nargs="*",
            metavar="[NAME:]LEVEL",
        )

    def add_preview_length(self, default_value: Union[str, int] = 15) -> Action:
        return self.add_environment_arg(
            variable_name=ENV_PREVIEW_LENGTH,
            help_base="Number of records to show in preview",
            metavar="COUNT",
            default_value=str(default_value),
            type=ranged_type(int, 1, 100),
        )

    def add_result_file(self) -> Action:
        return self.add_environment_arg(
            variable_name=ENV_RESULT_FILE,
            metavar="FILENAME",
            help_base="Local filename for storing results",
        )

    def add_min_words(self, default_value: Union[str, int] = 8) -> Action:
        return self.add_environment_arg(
            variable_name=ENV_MIN_WORDS,
            help_base="Minimum number of words in an LLM prompt for calculation",
            metavar="COUNT",
            default_value=str(default_value),
            type=ranged_type(int, 1, 1000),
        )

    def add_top_percent(
        self, default_value: Union[str, float] = 25, calc_type: str = ""
    ) -> Action:
        return self.add_environment_arg(
            variable_name=ENV_TOP_PERCENT,
            help_base=f"Only consider top X percent for {calc_type + ' ' if calc_type else ''}calculation",
            default_value=str(default_value),
            type=ranged_type(float, 1, 100),
        )

    def add_base_args(self, default_start_delta: timedelta = timedelta(days=1)) -> None:
        self.add_api_key()
        self.add_base_url()
        self.add_deployment()
        self.add_custom_metric()
        self.add_dry_run()
        self.add_start_ts(default_start_delta)
        self.add_end_ts()
        self.add_max_rows()
        self.add_required_flag()
        self.add_preview_length()
        self.add_result_file()
        self.add_logging()


def in_notebook_context() -> bool:
    """Determine whether code is being executed in a Jupyter notebook context."""
    try:
        # NOTE: if NOT running in a Jupyter ecosystem, this will fail with a NameError
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        return False  # consider TerminalInteractiveShell and others as not in notebook
    except NameError:
        return False  # Probably standard Python interpreter


def cli_arguments() -> List[str]:
    """Determines which set of arguments to use inside the argument parser.

    When running inside a Jupyter notebook context, an empty argument list is returned to
    force reading the values from the environment. It causes errors when parsing the arguments
    used to invoke the Jupyter notebook.

    When running outside a Jupyter notebook, use the normal arguments. This allows running the
    script directly from Python."""
    if in_notebook_context():
        return []

    return sys.argv[1:]


def log_parameters(namespace: Namespace, level: str = DEFAULT_LOG_LEVEL) -> None:
    """Logs the parameters in the Namespace at the provided level. Use the default
    log level, so they will be logged by default."""
    _level = find_level_value(level)
    redacted_values = {"api_key"}
    skipped_values = {"list_required"}
    items = []
    for key, value in namespace._get_kwargs():
        if key in skipped_values:
            continue

        if value is None:
            continue

        if key in redacted_values:
            items.append(f"{key}=REDACTED")
        else:
            items.append(f"{key}={value}")

    logger.log(_level, ", ".join(items))
