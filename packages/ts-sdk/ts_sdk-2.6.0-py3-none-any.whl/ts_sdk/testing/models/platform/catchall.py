import functools

from ts_sdk.task import __util_ts_api as api

from ...util.requests import replacing, responses
from .. import Auth


def strip_url_or_404(function):
    @functools.wraps(function)
    def applicator(original, url: str, **kwargs):
        prefix = api.get_api_url()
        if url.startswith(prefix):
            url = url[len(prefix) :]
            return function(original, url, **kwargs)
        return responses.json(status_code=404)

    return applicator


def add_auth_or_401(function):
    @functools.wraps(function)
    def applicator(original, url, headers=None, **kwargs):
        if auth := Auth.get_instance():
            headers = headers or {}
            headers["x-org-slug"] = auth.org
            headers["ts-auth-token"] = auth.auth_token
            kwargs["verify"] = not auth.ignore_ssl
            url = auth.api_url + url
            return function(original, url, headers=headers, **kwargs)
        return responses.json(status_code=401)

    return applicator


@replacing("get", "")
@strip_url_or_404
@add_auth_or_401
def get_final(original, *args, **kwargs):
    return original(*args, **kwargs)


@replacing("put", "")
@strip_url_or_404
@add_auth_or_401
def put_final(original, *args, **kwargs):
    return original(*args, **kwargs)


@replacing("post", "")
@strip_url_or_404
@add_auth_or_401
def post_final(original, *args, **kwargs):
    return original(*args, **kwargs)


@replacing("patch", "")
@strip_url_or_404
@add_auth_or_401
def patch_final(original, *args, **kwargs):
    return original(*args, **kwargs)


@replacing("delete", "")
@strip_url_or_404
@add_auth_or_401
def delete_final(original, *args, **kwargs):
    return original(*args, **kwargs)


replacements = [
    get_final,
    put_final,
    post_final,
    patch_final,
    delete_final,
]
