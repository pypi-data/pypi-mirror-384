import contextlib
from typing import TYPE_CHECKING, List, Optional
from unittest.mock import patch

from tenacity import wait_fixed

from .requests_replacement import RequestsReplacement

if TYPE_CHECKING:
    from ...models.auth import Auth
    from .endpoint_replacement import Replacement


@contextlib.contextmanager
def patch_requests(replacements: List["Replacement"], auth: Optional["Auth"] = None):
    replacement = RequestsReplacement(replacements=replacements, auth=auth)
    with (
        patch("ts_sdk.task.__util_fileinfo.requests", replacement),
        patch("ts_sdk.task.__util_task.requests", replacement),
        patch("ts_sdk.task.__util_es_datalake.requests", replacement),
        patch("ts_sdk.task.__util_fileinfo.requests", replacement),
        patch("ts_sdk.task.__util_ts_api.requests", replacement),
        patch.object(wait_fixed, "__call__", return_value=0.0),
    ):
        yield
