import random
import time
from datetime import datetime, timedelta, timezone

import requests
import simplejson as json

from ts_sdk.task.__util_adapters import CommunicationFormat, select_versioned_value
from ts_sdk.task.__util_adapters.endpoint_adapter import get_public_endpoint


def get_command_url():
    return get_public_endpoint("COMMAND_ENDPOINT") + select_versioned_value(
        {
            CommunicationFormat.V0: "/internal",
            CommunicationFormat.V1: "/v1/commands",
        }
    )


def run_command(
    context_data,
    org_slug,
    target_id,
    action,
    metadata,
    payload,
    ttl_sec,
    initial_delay_sec=0,
    return_command=False,
):
    if org_slug is None:
        raise Exception("Param org_slug is missing")
    if target_id is None:
        raise Exception("Param target_id is missing")
    if action is None:
        raise Exception("Param action is missing")
    if payload is None:
        raise Exception("Param payload is missing")
    if ttl_sec < 60 or ttl_sec > 900:
        raise Exception("Param ttl_sec must be between 60 and 900 seconds")
    if initial_delay_sec < 0 or initial_delay_sec > 60:
        raise Exception(
            "Param initial_delay_sec must be non-negative and less than 60 seconds"
        )

    if metadata is None:
        metadata = {}

    metadata["workflowId"] = context_data.get("workflowId")
    metadata["pipelineId"] = context_data.get("pipelineId")
    metadata["taskId"] = context_data.get("taskId")

    url = get_command_url()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_sec)

    command_create_payload = {
        "targetId": target_id,
        "action": action,
        "metadata": metadata,
        "expiresAt": expires_at.isoformat(),
        "payload": payload,
    }

    headers = {"x-org-slug": org_slug, "Content-Type": "application/json"}

    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(command_create_payload),
        verify=False,
    )
    if response.status_code == 200:
        print("Command successfully created")
        r = json.loads(response.text)
        command_id = r.get("id")

        command_url = get_command_url() + "/" + command_id
        command_headers = {"x-org-slug": org_slug}

        time_elapsed = 0
        max_sleep_time = (
            32  # Maximum sleep time in seconds to prevent excessive waiting
        )
        jitter_range = (
            0.8,
            1.2,
        )  # Jitter range for exponential backoff, arbitrarily chosen without a specific reason
        sleep_time = 1 * random.uniform(*jitter_range)  # Initial sleep time

        # Wait for the initial delay before starting to poll
        if initial_delay_sec > 0:
            print(f"Waiting for {initial_delay_sec} seconds before polling...")
            time.sleep(initial_delay_sec)

        # We use 'time_elapsed < ttl_sec' instead of 'time_elapsed <= ttl_sec'
        # because if time_elapsed == ttl_sec, the remaining sleep time would be 0.
        # In that case, min(sleep_time, ttl_sec - time_elapsed) would result in 0,
        # causing an endless loop since no more time is added to time_elapsed.
        # By stopping when time_elapsed is equal to ttl_sec, we ensure the loop exits
        # once the total elapsed time meets or exceeds the ttl_sec.
        while time_elapsed < ttl_sec:
            # Polling with exponential backoff
            sleep_time = min(
                sleep_time, ttl_sec - time_elapsed
            )  # Ensure we don't sleep past the TTL
            print(f"Polling for command status (sleeping {sleep_time} seconds)...")
            time.sleep(sleep_time)
            time_elapsed += sleep_time

            command_response = requests.get(
                command_url, headers=command_headers, verify=False
            )
            if command_response.status_code == 200:
                command = json.loads(command_response.text)
                command_status = command.get("status")
                print("Current command status: " + command_status)
                if command_status == "SUCCESS":
                    if return_command:
                        return command
                    return command.get("responseBody")
                elif command_status in ["CREATED", "PENDING", "PROCESSING"]:
                    # Continue polling with backoff and jitter
                    jitter = random.uniform(*jitter_range)
                    sleep_time = min(
                        max_sleep_time, sleep_time * 2 * jitter
                    )  # Double sleep time, up to max_sleep_time
                    continue
                else:
                    if return_command:
                        return command
                    raise Exception(command.get("responseBody"))

        print("TTL for command has expired")
        if return_command:
            return command
        raise Exception("Command TTL has expired")
    else:
        print("Error creating command: " + response.text)
        raise Exception(response.text)
