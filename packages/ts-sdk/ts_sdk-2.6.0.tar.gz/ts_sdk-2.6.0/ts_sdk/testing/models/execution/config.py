from typing import Optional

from ...util.context_singleton import ContextSingletonProtocol, context_singleton
from .secret import Secret


@context_singleton
class Config(ContextSingletonProtocol):
    _values: dict

    def __init__(self, *, inputs: Optional[dict] = None):
        inputs = inputs or {}
        self._values = {}
        for key, value in inputs.items():
            if isinstance(value, Secret):
                self._values[f"_resolved_:{value.ssm}"] = value.value
                self._values[key] = {"ssm": value.ssm}
            else:
                self._values[key] = value

    def dict(self):
        return self._values.copy()

    def __iter__(self):
        for item in self._values.items():
            yield item
