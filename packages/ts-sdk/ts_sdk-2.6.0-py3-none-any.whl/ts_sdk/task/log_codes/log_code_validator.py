import re
from typing import List

from ts_sdk.task.log_codes.log_code import LogCode


class LogCodeValidator:
    """Validator for Log Codes

    Checks code is in valid range, message is alphanumeric and in PascalCase, and message is
    correct length"""

    #: The maximum number of characters a Log Code message can have.
    MAX_CODE_MESSAGE_LENGTH = 32
    #: Regular expression that the Log Code message must match (PascalCase).
    CODE_MESSAGE_REGEX = re.compile(r"^[A-Z\d][a-z\d]+(?:[A-Z\d][a-z\d]+)*$")

    @classmethod
    def get_validation_errors(cls, log_code: LogCode) -> List[str]:
        """
        Return validation errors for given Log Code.

        :param log_code:
            The TetraScience log code to validate. A TetraScience log code is a log code whose
            ID is >= 1000 and < 10000. Log codes > 0 and < 1000 are still valid, but for internal
            use only.
        :return:
            List of reasons why the code is invalid, or empty list if code is valid.
        """
        errors = []
        if log_code.code < 1 or log_code.code > 9999:
            errors.append(
                f"Log Code outside of valid range [0, 9999]. Code: {log_code.code}"
            )
        if log_code.code_message.isalnum():
            if (
                0 < log_code.code < 5000
                and cls.CODE_MESSAGE_REGEX.match(log_code.code_message) is None
            ):
                errors.append(
                    f'Log Code message is not PascalCase. Message: "{log_code.code_message}"'
                )
        else:
            errors.append(
                f"Log Code message contains non-alphanumeric characters. Message: "
                f'"{log_code.code_message}"'
            )
        if len(log_code.code_message) > cls.MAX_CODE_MESSAGE_LENGTH:
            errors.append(
                f"Log Code message longer than {cls.MAX_CODE_MESSAGE_LENGTH} characters"
            )
        return errors
