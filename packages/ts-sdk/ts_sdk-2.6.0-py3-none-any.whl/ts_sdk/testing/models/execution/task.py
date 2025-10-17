from dataclasses import dataclass
from typing import Union

from ...execution.local import run_task
from ...util import random
from .task_script import TaskScriptFunction
from .workflow import Workflow


@dataclass(init=False, kw_only=True)
class Task:
    id: str
    function: TaskScriptFunction
    workflow: Workflow

    def __init__(
        self,
        *,
        id: str = None,
        function: Union[TaskScriptFunction, str] = None,
        workflow: Workflow = None,
    ):
        if isinstance(function, str):
            function = TaskScriptFunction(function_slug=function)
        self.function = function or TaskScriptFunction.get_instance_or()
        self.id = id or random.string()
        self.workflow = workflow or Workflow.get_instance_or()

        if self not in self.workflow.tasks:
            self.workflow.tasks.append(self)

    def run(self, input: object = None):
        return run_task(self, input)
