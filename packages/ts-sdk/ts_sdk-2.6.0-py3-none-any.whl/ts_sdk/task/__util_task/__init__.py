import os
import traceback

import requests
from requests.exceptions import RequestException
from tenacity import (
    RetryError,
    retry,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

from ts_sdk.task.__util_adapters import (
    CommunicationFormat,
    select_versioned_value,
)
from ts_sdk.task.__util_task.exceptions import (
    ContainerStoppedException,
    TaskUpdateConflictException,
    FailedPollTaskException,
)
from ts_sdk.task.__util_decorators import return_on_failure, raise_on_failure
from ts_sdk.task.__util_log import (
    CONTAINER_ID_KEY,
    LEVEL_KEY,
    MESSAGE_KEY,
    TASK_ID_KEY,
)
from ts_sdk.task.__util_log import Log


platform_props_hash = os.environ.get("PLATFORM_PROPS_HASH")
task_group_hash = os.environ.get("TASK_GROUP_HASH")
container_id = os.environ.get("CONTAINER_ID")

log = Log({CONTAINER_ID_KEY: container_id})


def get_endpoint():
    return select_versioned_value(
        {
            CommunicationFormat.V0: os.environ.get("ORCHESTRATOR_ENDPOINT"),
            CommunicationFormat.V1: os.environ.get("KERNEL_ENDPOINT"),
        }
    )


@raise_on_failure(RetryError, FailedPollTaskException)
@retry(
    wait=wait_exponential(min=1),
    retry=retry_if_result(lambda v: v is None),
    stop=stop_after_attempt(5),
)
def poll_task():
    try:
        poll_url = get_endpoint() + "/task/poll"
        response = requests.post(
            poll_url,
            json={
                "platformPropsHash": platform_props_hash,
                "taskGroupHash": task_group_hash,
                "containerId": container_id,
            },
            verify=False,
            timeout=300,
        )
        if response.status_code >= 400:
            message = f"Got {response.status_code} for {poll_url}"
            log.log({LEVEL_KEY: "error", MESSAGE_KEY: message})
            if response.status_code == 409:
                raise ContainerStoppedException(message)
            return None
        return generate_task_from_response(response.json())
    except RequestException:
        log.log({LEVEL_KEY: "error", MESSAGE_KEY: traceback.format_exc()})
        return None


def trim_result(result):
    return select_versioned_value(
        {
            CommunicationFormat.V0: {
                "status": result.get("status"),
                "result": result.get("result"),
            },
            # CommunicationFormat.V2: result,  # TODO uncomment when all deployments are off 3.6.{0,1}
        }
    )


@return_on_failure(RetryError, False)
@retry(
    wait=wait_exponential(min=1),
    retry=retry_if_result(lambda v: v is False),
    stop=stop_after_attempt(5),
)
def update_task_status(task, result):
    try:
        task_id = task.get("id")
        update_url = get_endpoint() + f"/task/{task_id}/update-status"
        response = requests.post(
            update_url,
            json=trim_result(result),
            verify=False,
            timeout=300,
        )
        if response.status_code >= 400:
            message = f"Got {response.status_code} for {update_url}"
            log.log(
                {
                    LEVEL_KEY: "error",
                    TASK_ID_KEY: task.get("id"),
                    MESSAGE_KEY: message,
                }
            )
            return False
    except RequestException:
        log.log(
            {
                LEVEL_KEY: "error",
                TASK_ID_KEY: task.get("id"),
                MESSAGE_KEY: traceback.format_exc(),
            }
        )
        return False
    return True


def generate_task_from_response(body):
    if body:
        data = body.get("data")
        return {
            "id": body.get("id"),
            "context": data.get("context", {}) or {},
            "input": data.get("input", {}) or {},
            "secrets": data.get("secrets", {}) or {},
            "func": data.get("func"),
            "workflow_id": data.get("workflowId"),
            "correlation_id": body.get("correlationId") or body.get("id"),
            "func_dir": data.get("funcDir", "./func") or "./func",
        }

    return {}


def extend_task_timeout(task):
    try:
        task_id = task.get("id")
        extend_timeout_url = get_endpoint() + f"/task/{task_id}/extend-timeout"

        response = requests.post(
            extend_timeout_url,
            json={},
            verify=False,
            timeout=300,
        )
        if response.status_code >= 400:
            message = f"Got {response.status_code} for {extend_timeout_url}"
            log.log(
                {
                    LEVEL_KEY: "error",
                    TASK_ID_KEY: task.get("id"),
                    MESSAGE_KEY: message,
                }
            )
            if response.status_code == 409:
                raise TaskUpdateConflictException(message)
        log.log(
            {
                LEVEL_KEY: "debug",
                TASK_ID_KEY: task.get("id"),
                MESSAGE_KEY: f"EXTENDING: {task_id}",
            }
        )
    except RequestException:
        log.log(
            {
                LEVEL_KEY: "error",
                TASK_ID_KEY: task.get("id"),
                MESSAGE_KEY: traceback.format_exc(),
            }
        )
