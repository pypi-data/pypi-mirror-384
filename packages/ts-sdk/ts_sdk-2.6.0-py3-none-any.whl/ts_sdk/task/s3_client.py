"""
This file exists to provide better browser support,
as this import will fail in the browser,
but the function will not be applied in the browser code path
"""


def _raises(*args, **kwargs):
    raise NotImplementedError("attempting to get s3 client")


try:
    from boto3 import client
    from botocore.client import Config
except ImportError:
    Config = lambda *args, **kwargs: None
    client = _raises
