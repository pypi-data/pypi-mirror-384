import os
from urllib.parse import urljoin

import requests

from ts_sdk.task.__util_adapters import select_versioned_value, CommunicationFormat


def get(path, params=None, **kwargs):
    return requests.get(get_api_url(path), params=params, **{"verify": False, **kwargs})


def delete(path, **kwargs):
    return requests.delete(get_api_url(path), **{"verify": False, **kwargs})


def patch(path, data=None, **kwargs):
    return requests.patch(get_api_url(path), data=data, **{"verify": False, **kwargs})


def post(path, data=None, json=None, **kwargs):
    return requests.post(
        get_api_url(path), data=data, json=json, **{"verify": False, **kwargs}
    )


def put(path, data=None, **kwargs):
    return requests.put(get_api_url(path), data=data, **{"verify": False, **kwargs})


def get_api_url(path=""):
    try:
        kernel_endpoint = select_versioned_value(
            {
                CommunicationFormat.V0: None,
                CommunicationFormat.V1: os.environ.get("KERNEL_ENDPOINT"),
            }
        )
        if not isinstance(path, str):
            raise ValueError("Path supplied to `get_ts_api_url` must be a string")
        if path != "" and not path.startswith("/"):
            path = "/" + path
        return urljoin(kernel_endpoint, "api") + path
    except NotImplementedError:
        raise NotImplementedError(
            "`get_ts_api_url` is not supported in this environment"
        )
