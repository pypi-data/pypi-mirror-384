from urllib.parse import urlencode

import requests
import simplejson as json
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from ts_sdk.task.__util_adapters import (
    make_adapter,
    CommunicationFormat,
)
from ts_sdk.task.__util_adapters.endpoint_adapter import get_public_endpoint
from ts_sdk.task.encoders import DataclassEncoder

from ts_sdk.task import __util_ts_api as api

__RETRY_COUNT = 10
__RETRY_DELAY_SECONDS = 2


def get_endpoint():
    return get_public_endpoint("FILEINFO_ENDPOINT")


def request_format_adapter():
    return make_adapter(
        {
            CommunicationFormat.V0: {
                "get_headers": lambda org_slug: {"Content-Type": "application/json"},
                "get_labels_url": lambda org_slug, file_id: f"{get_endpoint()}/internal/{org_slug}/files/{file_id}/labels",
            },
            CommunicationFormat.V1: {
                "get_headers": lambda org_slug: {
                    "Content-Type": "application/json",
                    "x-org-slug": org_slug,
                },
                "get_labels_url": lambda org_slug, file_id: f"{get_endpoint()}/v1/fileinfo/files/{file_id}/labels",
            },
        }
    )


def format_pipeline_history_headers(context_data):
    # We set x-pipeline-id and x-pipeline-history to guard against self loops and circular pipelines
    return {
        "x-pipeline-id": context_data.get("pipelineId"),
        "x-workflow-id": context_data.get("workflowId"),
        "x-pipeline-history": pipeline_history_from_input_file_meta(context_data),
    }


retry_if_not_found = retry(
    wait=wait_fixed(__RETRY_DELAY_SECONDS),
    retry=retry_if_exception_type(FileNotFoundError),
    stop=stop_after_attempt(__RETRY_COUNT),
)


@retry_if_not_found
def add_labels(context_data, file_id, labels, no_propagate=False):
    org_slug = context_data.get("orgSlug")

    query_str = urlencode({"noPropagate": "true"} if no_propagate else {})
    url = f"{request_format_adapter().get_labels_url(org_slug, file_id)}?{query_str}"

    headers = {
        **request_format_adapter().get_headers(org_slug),
        **format_pipeline_history_headers(context_data),
    }
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(labels, cls=DataclassEncoder),
        verify=False,
    )

    if response.status_code == 200:
        print("Labels successfully added")
        return json.loads(response.text)
    elif response.status_code == 404:
        raise FileNotFoundError()
    else:
        print("Error adding labels: " + response.text)
        raise Exception(response.text)


@retry_if_not_found
def get_labels(context_data, file_id):
    org_slug = context_data.get("orgSlug")

    url = request_format_adapter().get_labels_url(org_slug, file_id)
    headers = request_format_adapter().get_headers(org_slug)
    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        print("Labels successfully obtained")
        return json.loads(response.text)
    elif response.status_code == 404:
        raise FileNotFoundError()
    else:
        print("Error getting labels: " + response.text)
        raise Exception(response.text)


@retry_if_not_found
def delete_labels(context_data, file_id, label_ids):
    org_slug = context_data.get("orgSlug")

    suffix = "&".join(map(lambda id: "id=" + str(id), label_ids))
    url = request_format_adapter().get_labels_url(org_slug, file_id)
    if suffix:
        url += f"?{suffix}"
    pipeline_id = context_data.get("pipelineId")

    # We set x-pipeline-id and x-pipeline-history to guard against self loops and circular pipelines
    headers = {
        **request_format_adapter().get_headers(org_slug),
        **format_pipeline_history_headers(context_data),
    }
    response = requests.delete(url, headers=headers, verify=False)

    if response.status_code == 200:
        print("Labels successfully deleted")
        return json.loads(response.text)
    elif response.status_code == 404:
        raise FileNotFoundError()
    else:
        print("Error deleting labels: " + response.text)
        raise Exception(response.text)


@retry_if_not_found
def get_file_pointer(context_data, file_id):
    org_slug = context_data.get("orgSlug")
    response = api.get(
        f"/v1/fileinfo/file/{file_id}",
        headers=request_format_adapter().get_headers(org_slug),
    )
    if response.status_code == 200:
        file_info = json.loads(response.text)
        file = file_info["file"]
        return {
            "type": "s3file",
            "fileId": file_id,
            "bucket": file["bucket"],
            "fileKey": file["path"],
            "version": file["version"],
        }
    elif response.status_code == 404:
        raise FileNotFoundError(f"File with fileId {file_id} not found")
    else:
        raise Exception(response.text)


# When we write a new file or update metadata or tags, we add the pipeline id and pipeline history to the
# new file's s3 metadata fields. If we only add labels, we don't update the file's s3 metadata fields because
# we don't generate a new file. To keep track of a file's pipeline history, we will have to use the
# `inputFile.meta` object that contains information about a file that may not exist in the s3 metadata fields.
def pipeline_history_from_input_file_meta(context_data):
    pipeline_id = context_data.get("pipelineId")
    if "pipelineHistory" in context_data.get("inputFile", {}).get("meta", {}):
        existing_pipeline_history = context_data["inputFile"]["meta"]["pipelineHistory"]
        # If the pipeline history field exists, but it is an empty string, we don't want a leading comma
        if len(existing_pipeline_history) == 0:
            new_pipeline_history = pipeline_id
        else:
            # Only add the pipeline's id if it is not already present in the history
            if pipeline_id in existing_pipeline_history:
                new_pipeline_history = existing_pipeline_history
            else:
                new_pipeline_history = existing_pipeline_history + "," + pipeline_id
    else:
        new_pipeline_history = pipeline_id
    return new_pipeline_history
