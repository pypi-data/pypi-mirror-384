import datetime
import os
import traceback
from enum import Enum
from os.path import relpath
from typing import Any, Dict, Mapping, Optional

import simplejson as json

from ts_sdk.task.log_codes.log_code import LogCode
from ts_sdk.task.log_codes.log_code_collection import LogCodeCollection
from ts_sdk.task.log_codes.log_code_validator import LogCodeValidator
from ts_sdk import __version__

TIMESTAMP_KEY = "timestamp"
ORG_SLUG_KEY = "orgSlug"
MESSAGE_KEY = "message"
FILE_ID_KEY = "fileId"
MASTER_SCRIPT_KEY = "masterScript"
TASK_SCRIPT_KEY = "taskScript"
TRACE_ID_KEY = "traceId"
TASK_ID_KEY = "taskId"
WORKFLOW_ID_KEY = "workflowId"
CONTAINER_ID_KEY = "containerId"
LEVEL_KEY = "level"
ERROR_TYPE_KEY = "errorType"
EXCEPTION_KEY = "exception"
TS_SDK_VERSION_KEY = "tsSdkVersion"


class LogLevel(str, Enum):
    """Log Level strings"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Log:
    """Logging class for ts-sdk-python"""

    def __init__(self, context):
        self._context = context

    def log(self, *args, sep=" "):
        """Logs a JSON object created from function arguments"""
        try:
            # Perform actual logging, that will be transported to Cloudwatch.
            __builtins__["default_print"](
                json.dumps(self.create_json_log_entry(args, sep=sep))
            )
        except TypeError as ex:
            __builtins__["default_print"](json.dumps(self.create_json_log_entry(ex)))
            for arg in args:
                __builtins__["default_print"](arg)

    def create_json_log_entry(self, input_, sep=" "):
        """Create JSON object for logging"""
        log_entry = self.generate_default()

        if isinstance(input_, tuple):
            if len(input_) > 1:
                log_entry = {
                    **log_entry,
                    MESSAGE_KEY: sep.join(str(item) for item in input_),
                    LEVEL_KEY: LogLevel.INFO,
                }
                return log_entry
            if len(input_) == 1:
                input_ = input_[0]

        if isinstance(input_, str):
            log_entry = {**log_entry, MESSAGE_KEY: input_, LEVEL_KEY: LogLevel.INFO}
        elif isinstance(input_, Exception):
            log_entry = {**log_entry, **self.generate_error(input_)}
        elif isinstance(input_, Mapping):
            log_entry = {**log_entry, **input_}
        else:
            log_entry = {
                **log_entry,
                MESSAGE_KEY: str(input_),
                LEVEL_KEY: LogLevel.INFO,
            }
        if LEVEL_KEY not in log_entry:
            log_entry[LEVEL_KEY] = LogLevel.INFO

        return log_entry

    def generate_default(self):
        """Generate default log fields"""
        try:
            default_log = {
                TIMESTAMP_KEY: datetime.datetime.now().isoformat(),
                TS_SDK_VERSION_KEY: __version__,
            }

            if "CONTAINER_ID" in os.environ:
                default_log[CONTAINER_ID_KEY] = os.environ.get("CONTAINER_ID")

            if "traceId" in self._context.get("inputFile", {}).get("meta", {}):
                default_log[TRACE_ID_KEY] = self._context["inputFile"]["meta"][
                    "traceId"
                ]

            if "taskId" in self._context:
                default_log[TASK_ID_KEY] = self._context.get("taskId")

            if "workflowId" in self._context:
                default_log[WORKFLOW_ID_KEY] = self._context.get("workflowId")
        except (AttributeError, KeyError) as exc:
            __builtins__["default_print"]("Error in default log")
            __builtins__["default_print"](exc)
            default_log = {}

        return default_log

    def generate_error(self, err):
        """Generate default error message"""
        tb_lines = traceback.format_exception(err.__class__, err, err.__traceback__)
        tb_text = "".join(tb_lines)
        error = {
            LEVEL_KEY: LogLevel.ERROR,
            ERROR_TYPE_KEY: str(type(err)),
            EXCEPTION_KEY: tb_text,
        }
        if hasattr(err, "message"):
            error[MESSAGE_KEY] = err.message
        else:
            error[MESSAGE_KEY] = str(err)

        return error

    def _log_with_level(
        self,
        message: str,
        log_level: LogLevel,
        code: Optional[LogCode] = None,
        *,
        extra: Optional[Mapping[str, Any]] = None,
    ):
        """Log a message with chosen log level

        Logs an error in addition to given message if:
          * LogCode is invalid
          * Log level is ERROR, WARNING but LogCode is None
          * Message passed is not a <str>
        """
        errors = []
        original_log = {}
        fields = {"level": log_level}

        if not isinstance(message, str):
            errors.append(
                f"Expected message to be 'str', received {type(message)} instead"
            )
            message = str(message)
            original_log["message"] = message
        fields["message"] = message

        if code is not None:
            if not isinstance(code, LogCode):
                errors.append(f"Expected {type(LogCode)}, got {type(code)} instead")
                code = LogCodeCollection.generic
                original_log["code"] = code
            else:
                validator_errors = LogCodeValidator.get_validation_errors(code)
                if validator_errors:
                    errors.extend(validator_errors)
                    original_log["code"] = code.code
                    code = LogCodeCollection.generic
            fields["code"] = code.code
            fields["codeMessage"] = code.code_message
        else:
            if log_level in [LogLevel.ERROR, LogLevel.WARNING]:
                errors.append("Missing LogCode")
                code = LogCodeCollection.generic
                fields["code"] = code.code
                fields["codeMessage"] = code.code_message

        if extra is None:
            fields["extra"] = {}
        elif isinstance(extra, Dict):
            fields["extra"] = extra
        else:
            fields["extra"] = {"data": extra}

        self.log(fields)
        if errors:
            msg = ", ".join(errors)
            traceback_print = ["Traceback (most recent call last):"]
            traceback_print.extend(
                [
                    f'  File "{relpath(frame.filename)}", line {frame.lineno}, in {frame.name}\n'
                    f"    {frame.line}"
                    for frame in traceback.extract_stack()[1:-1]
                ]
            )
            error_fields = {
                "level": LogLevel.ERROR,
                "original": original_log,
                "exception": {
                    "type": "InvalidLogInput",
                    "stack": "\n".join(traceback_print),
                },
                "message": f"Invalid input to logging method.\n{msg}",
                "code": LogCodeCollection.invalid_raw_input_data.code,
                "codeMessage": LogCodeCollection.invalid_raw_input_data.code_message,
            }
            self.log(error_fields)

    def debug(
        self,
        message: str,
        code: Optional[LogCode] = None,
        *,
        extra: Optional[Mapping[str, Any]] = None,
    ):
        """Log a message with DEBUG level"""
        self._log_with_level(message, LogLevel.DEBUG, code, extra=extra)

    def info(
        self,
        message: str,
        code: Optional[LogCode] = None,
        *,
        extra: Optional[Mapping[str, Any]] = None,
    ):
        """Log a message with INFO level"""
        self._log_with_level(message, LogLevel.INFO, code, extra=extra)

    def warning(
        self,
        message: str,
        code: LogCode,
        *,
        extra: Optional[Mapping[str, Any]] = None,
    ):
        """Log a message with WARNING level"""
        self._log_with_level(message, LogLevel.WARNING, code, extra=extra)

    def warn(
        self,
        message: str,
        code: LogCode,
        *,
        extra: Optional[Mapping[str, Any]] = None,
    ):
        """Log a message with WARNING level"""
        self.warning(message, code, extra=extra)

    def error(
        self,
        message: str,
        code: LogCode,
        *,
        extra: Optional[Mapping[str, Any]] = None,
    ):
        """Log a message with ERROR level"""
        self._log_with_level(message, LogLevel.ERROR, code, extra=extra)
