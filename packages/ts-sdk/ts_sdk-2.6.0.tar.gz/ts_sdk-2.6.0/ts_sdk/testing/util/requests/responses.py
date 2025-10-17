from json import dumps
from unittest.mock import MagicMock

from requests import HTTPError


def raise_for_status(status_code: int):
    def implementation():
        if status_code >= 400:
            raise HTTPError(f"{status_code} Error: unknown reason")

    return implementation


def json(value: object = None, status_code: int = 200):
    response = MagicMock()
    response.status_code = status_code
    response.json = lambda: value
    response.text = dumps(value)
    response.raise_for_status = raise_for_status(status_code)
    return response


def text(value: str = "", status_code: int = 200):
    response = MagicMock()
    response.status_code = status_code
    response.text = value
    response.raise_for_status = raise_for_status(status_code)
    return response
