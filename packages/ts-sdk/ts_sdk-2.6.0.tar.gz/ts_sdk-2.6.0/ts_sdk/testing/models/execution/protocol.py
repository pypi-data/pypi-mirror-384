from dataclasses import dataclass

from ...util.context_singleton import ContextSingletonProtocol, context_singleton
from .artifact import Artifact


@context_singleton
@dataclass(kw_only=True)
class Protocol(Artifact, ContextSingletonProtocol):
    pass
