import json
import os.path
from dataclasses import dataclass
from os import PathLike
from typing import Optional, Union

from ...optionals import yaml
from ...util.context_singleton import ContextSingletonProtocol, context_singleton


@context_singleton
@dataclass(kw_only=True)
class Auth(ContextSingletonProtocol):
    api_url: str
    auth_token: str
    ignore_ssl: bool
    org: str


class ConfigFileAuth(Auth):

    def __init__(self, *, path: Union[PathLike, str]):
        with open(os.path.expanduser(path)) as file:
            config = json.load(file)
        auth = Auth(**config)
        self.api_url = auth.api_url
        self.auth_token = auth.auth_token
        self.ignore_ssl = auth.ignore_ssl
        self.org = auth.org


class UserConfigAuth(Auth):
    """
    Reads auth from ~/.config/tetrascience/config similarly to ts-cli
    Long term we should remove this code and just reuse the ts-cli code
    """

    def __init__(self, *, use_global: bool = None, profile: str = None):
        with open(os.path.expanduser("~/.config/tetrascience/config")) as file:
            config = yaml.safe_load(file)
        if use_global:
            profile = None
        else:
            profile = profile or config.get("profile", None)
        profile_config = config.get("profiles", {}).get(profile, {}) if profile else {}
        self.api_url = profile_config.get("api_url", None) or config.get("api_url")
        self.auth_token = profile_config.get("auth_token", None) or config.get(
            "auth_token"
        )
        ignore_ssl: Optional[bool] = profile_config.get("ignore_ssl", None)
        if ignore_ssl is None:
            self.ignore_ssl = config.get("ignore_ssl")
        else:
            self.ignore_ssl = ignore_ssl
        self.org = profile_config.get("org", None) or config.get("org")
