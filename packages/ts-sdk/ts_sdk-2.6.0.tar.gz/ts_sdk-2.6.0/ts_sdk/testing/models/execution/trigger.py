from dataclasses import dataclass, field
from typing import Literal

from ...util.context_singleton import ContextSingletonProtocol, context_singleton
from .file import File, InlineFile


@context_singleton
@dataclass(kw_only=True)
class Trigger(ContextSingletonProtocol):
    type: Literal["file"] = field(default="file")
    file: File = field(default_factory=InlineFile)
