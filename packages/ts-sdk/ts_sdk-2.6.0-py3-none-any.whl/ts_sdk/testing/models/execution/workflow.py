from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

from ...exceptions import SetupException
from ...util import random
from ...util.context_singleton import ContextSingletonProtocol, context_singleton
from .file import File, InlineFile
from .pipeline import Pipeline
from .trigger import Trigger

if TYPE_CHECKING:
    from .task import Task


@context_singleton
@dataclass(kw_only=True)
class Workflow(ContextSingletonProtocol):
    id: str = field(default_factory=random.string)
    tasks: List["Task"] = field(default_factory=lambda: [])
    pipeline: Pipeline = field(default_factory=Pipeline.get_instance_or)
    output_files: List[File] = field(default_factory=lambda: random.list_of(InlineFile))
    org_slug: str = field(default=None)
    trigger: Trigger = field(default=None)

    def __post_init__(self):
        if self.trigger is None and self.org_slug is not None:
            self.trigger = Trigger.get_instance_or(
                file=InlineFile(org_slug=self.org_slug)
            )
        elif self.trigger is not None and self.org_slug is None:
            self.org_slug = self.trigger.file.org_slug
        elif self.org_slug is None and self.trigger is None:
            self.trigger = Trigger.get_instance_or()
            self.org_slug = self.trigger.file.org_slug
        if self.org_slug != self.trigger.file.org_slug:
            raise SetupException("Workflow input file must match workflow org slug")
