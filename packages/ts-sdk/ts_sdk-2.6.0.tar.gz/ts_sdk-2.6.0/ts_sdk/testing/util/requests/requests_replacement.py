from typing import TYPE_CHECKING, List, Optional, cast

from ts_sdk.task import __util_ts_api as api

from .endpoint_replacement import *

if TYPE_CHECKING:
    from ...models.auth import Auth


def original_implementation_for_method(method: Method) -> OriginalImplementation:
    def implementation(replacement_url: str, **replacement_kwargs: object) -> Response:
        return requests.request(method, replacement_url, **replacement_kwargs)

    return cast(OriginalImplementation, implementation)


@dataclass(kw_only=True)
class RequestsReplacement:

    replacements: List[Replacement]
    auth: Optional["Auth"]

    def get_current_state(self) -> SideCondition:
        return "authed" if self.auth else "mocked"

    @staticmethod
    def replacement_matches(
        replacement: Replacement, method: Method, url: str, state: SideCondition
    ) -> bool:
        return (
            method == replacement.method
            and url.startswith(api.get_api_url(replacement.path_prefix))
            and replacement.side_condition in ("always", state)
        )

    def find_replacement(
        self, method: Method, url: str
    ) -> Optional[ReplacementImplementation]:
        state = self.get_current_state()
        for replacement in self.replacements:
            if self.replacement_matches(replacement, method, url, state):
                return replacement.implementation
        return None

    def request(self, method: Method, url: str, **kwargs):
        original = original_implementation_for_method(method)
        if replacement := self.find_replacement(method, url):
            return replacement(original, url, **kwargs)
        return original(url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("post", url, **kwargs)

    def get(self, url, **kwargs):
        return self.request("get", url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request("patch", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("put", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("delete", url, **kwargs)

    def head(self, url, **kwargs):
        return self.request("head", url, **kwargs)

    def options(self, url, **kwargs):
        return self.request("options", url, **kwargs)
