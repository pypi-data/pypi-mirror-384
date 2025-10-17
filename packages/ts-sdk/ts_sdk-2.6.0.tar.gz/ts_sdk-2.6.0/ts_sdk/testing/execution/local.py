from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Optional

from ts_sdk.task.__task_script_runner import run
from ts_sdk.task.__util_adapters.communication_format import (
    COMMUNICATION_FORMAT_ENV_KEY,
    CommunicationFormat,
)

from ..models import Auth
from ..models.platform import replacements
from ..models.platform.s3 import patch_s3
from ..optionals import MonkeyPatch
from ..util import constants
from ..util.add_path import add_path
from ..util.requests import patch_requests

if TYPE_CHECKING:
    from ..models import Task


def run_task(
    task: "Task", input: object = None
) -> (Optional[object], Optional[object]):
    task_script = task.function.task_script
    with (
        patch_requests(replacements, Auth.get_instance()),
        TemporaryDirectory() as temporary_directory,
        MonkeyPatch.context() as monkeypatch,
        patch_s3(workflow=task.workflow),
        add_path(task_script.path),
    ):
        monkeypatch.setenv("TMPDIR", temporary_directory)
        monkeypatch.setenv(COMMUNICATION_FORMAT_ENV_KEY, CommunicationFormat.V2.value)
        monkeypatch.setenv("KERNEL_ENDPOINT", f"http://localhost")
        try:
            protocol = task.workflow.pipeline.protocol
            result = run(
                input=input,
                context_from_arg={
                    "inputFile": task.workflow.trigger.file
                    and task.workflow.trigger.file.to_file_pointer(),
                    "pipelineConfig": task.workflow.pipeline.config.dict(),
                    "orgSlug": task.workflow.org_slug,
                    "pipelineId": task.workflow.pipeline.id,
                    "workflowId": task.workflow.id,
                    "masterScriptNamespace": protocol and protocol.namespace,
                    "masterScriptSlug": protocol and protocol.slug,
                    "masterScriptVersion": protocol and protocol.version,
                    "taskId": task.id,
                    "taskScript": f"{task_script.namespace}/{task_script.slug}:{task_script.version}",
                    "taskSlug": task.function.function_slug,
                },
                func=task.function.function_slug,
                correlation_id=task.id,
                func_dir=str(task_script.path),
                storage_type="s3file",
                storage_bucket=constants.STORAGE_BUCKET,
                storage_file_key=constants.ARTIFACT_FILE_KEY,
                storage_endpoint=constants.STORAGE_ENDPOINT,
                artifact_bucket=constants.ARTIFACT_BUCKET,
                artifact_prefix=constants.ARTIFACT_PREFIX,
                artifact_endpoint=constants.ARTIFACT_ENDPOINT,
                artifact_file_key=constants.ARTIFACT_FILE_KEY,
                artifact_bucket_private=constants.ARTIFACT_BUCKET_PRIVATE,
                artifact_prefix_private=constants.ARTIFACT_PREFIX_PRIVATE,
                artifact_endpoint_private=constants.ARTIFACT_ENDPOINT_PRIVATE,
                store_output=False,
            )
            if result["status"] == "completed":
                return result["result"], None
            return None, result["error"]
        except (SystemExit, Exception) as error:
            return None, str(error)
