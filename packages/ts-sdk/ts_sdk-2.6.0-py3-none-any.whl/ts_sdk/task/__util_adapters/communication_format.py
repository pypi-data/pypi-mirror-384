import os
from enum import Enum
from itertools import takewhile
from typing import Optional


class CommunicationFormat(Enum):
    V0 = "v0"
    V1 = "v1"
    V2 = "v2"
    VZ = "v?"


DEFAULT_COMMUNICATION_FORMAT = CommunicationFormat.V0
MAXIMUM_COMMUNICATION_FORMAT = CommunicationFormat.V2
UNKNOWN_COMMUNICATION_FORMAT = CommunicationFormat.VZ

COMMUNICATION_FORMAT_ENV_KEY = "PIPELINES_COMMUNICATION_FORMAT"


def get_all_platform_formats():
    """
    :return: An ordered list of CommunicationFormats
    """
    return [communication_format for communication_format in CommunicationFormat]


def to_communication_format(provided_format: Optional[str]) -> CommunicationFormat:
    """
    Coerces a string representation of a communication format into a concreate CommunicationFormat
    :param provided_format: A string representation of a communication format
    :return: CommunicationFormat
    """
    if provided_format is None:
        return DEFAULT_COMMUNICATION_FORMAT
    else:
        search_value = provided_format.lower().strip()
        return next(
            (
                communication_format
                for communication_format in CommunicationFormat
                if communication_format.value == search_value
            ),
            UNKNOWN_COMMUNICATION_FORMAT,
        )


def get_communication_format() -> CommunicationFormat:
    """
    Gets the current CommunicationFormat set in the process's ENV
    :return: CommunicationFormat
    """
    user_communication_format = os.environ.get(COMMUNICATION_FORMAT_ENV_KEY)
    return to_communication_format(user_communication_format)


def get_formats_up_to(communication_format: CommunicationFormat):
    """
    Gets the ordered list of communication formats up to and including the provided CommunicationFormat
    :param communication_format: The final CommunicationFormat to be included in the list of formats
    :return: a list of CommunicationFormats
    """
    preceding_formats = list(
        takewhile(
            lambda other_format: other_format != communication_format,
            get_all_platform_formats(),
        )
    )
    return preceding_formats + [communication_format]
