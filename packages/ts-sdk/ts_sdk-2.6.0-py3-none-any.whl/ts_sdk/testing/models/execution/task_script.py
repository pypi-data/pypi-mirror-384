import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from ...exceptions import SetupException
from ...util import random
from ...util.context_singleton import ContextSingletonProtocol, context_singleton
from .artifact import Artifact


@context_singleton
@dataclass(kw_only=True)
class TaskScript(Artifact, ContextSingletonProtocol):
    path: os.PathLike = field(default_factory=lambda: Path(os.getcwd()))

    @staticmethod
    def from_manifest(manifest_path: Union[os.PathLike, str] = None) -> "TaskScript":
        """
        consumes a manifest path and returns a task script
        :return:
        """
        if manifest_path:
            path = os.path.dirname(manifest_path)
        else:
            path = os.getcwd()
            manifest_path = os.path.join(path, "manifest.json")

        if not Path(manifest_path).is_file():
            raise SetupException("Manifest does not exist")
        with open(manifest_path, encoding="utf-8") as manifest_file:
            try:
                manifest = json.load(manifest_file)
            except:
                raise SetupException("Could not parse manifest.json contents")
        if not isinstance(manifest, dict):
            raise SetupException("Expected manifest to be a dict")
        namespace = manifest.get("namespace", None)
        slug = manifest.get("slug", None)
        version = manifest.get("version", None)
        if (
            not isinstance(namespace, str)
            or not isinstance(slug, str)
            or not isinstance(version, str)
        ):
            raise SetupException("Manifest should include namespace, slug and version")
        return TaskScript(path=path, namespace=namespace, slug=slug, version=version)

    def __getitem__(self, function: str) -> "TaskScriptFunction":
        return self.function(function)

    def function(self, function: str) -> "TaskScriptFunction":
        return TaskScriptFunction(task_script=self, function_slug=function)


@context_singleton
@dataclass(kw_only=True)
class TaskScriptFunction(ContextSingletonProtocol):
    function_slug: str = field(default_factory=random.string)
    task_script: TaskScript = field(default_factory=TaskScript.get_instance_or)
