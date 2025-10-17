import urllib.parse

from ts_sdk.task.__util_adapters import (
    CommunicationFormat,
    select_versioned_value,
)

import os
import traceback

import requests
from requests.exceptions import RequestException

from ts_sdk.task.__util_adapters.endpoint_adapter import get_public_endpoint

task_group_hash = os.environ.get("TASK_GROUP_HASH")
container_id = os.environ.get("CONTAINER_ID")


def get_search_eql_api_url():
    return get_public_endpoint("ORCHESTRATOR_ENDPOINT") + select_versioned_value(
        {
            CommunicationFormat.V0: "/datalake/searchEql",
            CommunicationFormat.V1: "/v1/datalake/searchEql",
        }
    )


def es_datalake_search_eql(payload, query=None):
    try:
        url_encoded_query = urllib.parse.urlencode(query or {}, doseq=True)
        url_suffix = f"?{url_encoded_query}" if url_encoded_query else ""
        search_url = get_search_eql_api_url() + url_suffix
        response = requests.post(
            search_url,
            json=payload,
            headers={
                "x-task-group-hash": task_group_hash,
                "x-container-id": container_id,
                "content-type": "application/json; charset=utf-8",
            },
            verify=False,
        )
        if response.status_code >= 400:
            print({"level": "error", "message": response.text})
            raise Exception(f"Got {response.status_code} for {search_url}")
        return response.json()
    except RequestException:
        print({"level": "error", "message": traceback.format_exc()})
        raise


def es_hit_to_file_pointer(hit):
    es_file = hit["_source"]["file"]
    return {
        "type": "s3file",
        "bucket": es_file["bucket"],
        "fileKey": es_file["path"],
        "version": es_file["version"],
        "fileId": hit["_source"]["fileId"],
    }
