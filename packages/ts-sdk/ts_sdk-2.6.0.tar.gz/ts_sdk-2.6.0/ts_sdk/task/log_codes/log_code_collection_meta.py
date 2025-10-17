from itertools import chain
from typing import Any, Dict, Iterable, Set, Tuple, Type

from ts_sdk.task.log_codes.log_code import LogCode
from ts_sdk.task.log_codes.log_code_validator import LogCodeValidator


class LogCodeConfigurationError(Exception):
    """Raised when there is an error defining a log code."""


class LogCodeCollectionMeta(type):
    """
    Metaclass for singleton collection of Log Codes.

    This metaclass validates that all Log Code members are valid using a LogCodeValidator and
    provides convenience functions for working with Log Codes. See the Log Code Guide document
    for further information.
    """

    def __new__(
        mcs, name: str, bases: Tuple[Type, ...], namespace: Dict[str, Any], **_kwargs
    ) -> "LogCodeCollectionMeta":
        """
        :param name:
            The name of the class returned by this method.
        :param bases:
            The base classes of the class.
        :param namespace:
            A mapping of the class' member names to their values.
        """
        current_class_log_codes = mcs._get_tetrascience_log_codes(namespace.values())
        base_log_codes: Iterable[LogCode] = chain.from_iterable(
            mcs._get_tetrascience_log_codes(base_class.__dict__.values())
            for base_class in bases
        )

        common_log_codes = mcs.get_common_log_codes(
            current_class_log_codes, base_log_codes
        )
        if len(common_log_codes) > 0:
            raise LogCodeConfigurationError(
                "Cannot override parent members in child classes. "
                f"The base class and the {name} class have the following pairs of log "
                f"codes with common messages or integer codes: "
                f"{', '.join(map(str, common_log_codes))}. Please change the message or "
                f"integer code in the {name} class."
            )

        validator = LogCodeValidator()
        invalid_log_codes = {
            log_code
            for log_code in current_class_log_codes
            if validator.get_validation_errors(log_code)
        }
        if len(invalid_log_codes) > 0:
            raise LogCodeConfigurationError(
                f"The following TetraScience log codes are invalid: "
                f"{', '.join(map(str, sorted(invalid_log_codes)))}. Ensure that "
                f"the log code is in the correct range, the log code message is in PascalCase "
                f"and is less than {validator.MAX_CODE_MESSAGE_LENGTH} characters long."
            )

        return super(LogCodeCollectionMeta, mcs).__new__(
            mcs, name, bases, namespace, **_kwargs
        )

    @staticmethod
    def get_common_log_codes(
        log_codes: Iterable[LogCode], base_log_codes: Iterable[LogCode]
    ) -> Set[Tuple[LogCode, LogCode]]:
        """Return pairs of log codes that have the same message or ID."""
        log_codes = set(log_codes)
        base_log_codes = set(base_log_codes)

        tetrascience_ids = {log_code.code: log_code for log_code in log_codes}
        base_codes = {log_code.code: log_code for log_code in base_log_codes}
        common_codes = set(tetrascience_ids).intersection(base_codes)

        tetrascience_code_messages = {
            log_code.code_message: log_code for log_code in log_codes
        }
        base_code_messages = {
            log_code.code_message: log_code for log_code in base_log_codes
        }
        common_code_messages = set(tetrascience_code_messages).intersection(
            base_code_messages
        )

        return {
            *(
                (tetrascience_ids[log_code], base_codes[log_code])
                for log_code in common_codes
            ),
            *(
                (tetrascience_code_messages[message], base_code_messages[message])
                for message in common_code_messages
            ),
        }

    @staticmethod
    def _get_tetrascience_log_codes(members: Iterable[Any]) -> Set[LogCode]:
        """
        Return all the unique values that are TetraScience log codes. A log code is
        a TetrasScience log code iff its ID is in [0, 5000).
        """
        all_log_codes: Set[LogCode] = {
            member for member in members if isinstance(member, LogCode)
        }
        return {member for member in all_log_codes if 0 <= member.code < 5000}
