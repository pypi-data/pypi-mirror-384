from dataclasses import dataclass
from typing import Literal, Protocol

import requests

Method = Literal["post", "get", "patch", "put", "delete", "options", "head"]
SideCondition = Literal["always", "mocked", "authed"]
Response = requests.models.Response


class OriginalImplementation(Protocol):
    def __call__(self, url: str, **kwargs: object) -> Response: ...


class ReplacementImplementation(Protocol):
    def __call__(
        self, original: OriginalImplementation, url: str, **kwargs: object
    ) -> Response: ...


@dataclass(kw_only=True)
class Replacement:
    method: Method
    path_prefix: str
    implementation: ReplacementImplementation
    side_condition: SideCondition
