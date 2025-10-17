from typing import NamedTuple


class LogCode(NamedTuple):
    #: Short human-readable description of the log.
    code_message: str
    #: Integer ID of the code.
    code: int
