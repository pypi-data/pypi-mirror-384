from dataclasses import dataclass, field

from ...util import random


@dataclass(kw_only=True)
class Artifact:
    namespace: str = field(default_factory=random.namespace)
    slug: str = field(default_factory=random.string)
    version: str = field(default_factory=random.version)
