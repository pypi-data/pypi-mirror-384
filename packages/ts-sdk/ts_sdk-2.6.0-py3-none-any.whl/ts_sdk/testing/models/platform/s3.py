import contextlib
import json
import re
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import smart_open

from ts_sdk.task import __util_ts_api as api
from ts_sdk.task import s3_client
from ts_sdk.task.__util_metadata import FIELDS

from ...util import constants
from ..execution.datalake import get_by_location
from ..execution.file import File, InlineFile
from ..execution.label import Label

if TYPE_CHECKING:
    from ..execution.workflow import Workflow


class NoSuchKey(Exception):
    pass


class S3:
    workflow: "Workflow"
    label_storage: dict[str, list[dict]]

    def __init__(self, workflow: "Workflow"):
        self.workflow = workflow
        self.label_storage = dict()

    def create_multipart_upload(self, **kwargs):
        raise NotImplementedError

    def upload_part(self, **kwargs):
        raise NotImplementedError

    def put_object(
        self, *, Body, Bucket, Key, Metadata=None, ContentEncoding=None, **kwargs
    ):
        if match := re.match(
            ".*?/.*?/TMP/.*?/.*?/([^/]*?)\\.labels", Key, flags=re.DOTALL
        ):
            (file_id,) = match.groups()
            return self.save_labels(file_id=file_id, body=Body)
        elif Metadata:
            match = re.match("(.*?)/(.*?)/(.*?)/(.*)", Key, flags=re.DOTALL)
            org_slug, source_id, file_category, file_name = match.groups()
            tags: list[str] = list(
                filter(bool, Metadata.get(FIELDS["CUSTOM_TAGS"]).split(","))
            )
            metadata_entries = [
                entry.split("=")
                for entry in list(
                    filter(bool, Metadata.get(FIELDS["CUSTOM_METADATA"]).split("&"))
                )
            ]
            metadata = {key: value for key, value in metadata_entries}
            file_id = Metadata.get("ts_file_id")
            if file_id in self.label_storage:
                labels = [Label(**label) for label in self.label_storage[file_id]]
                del self.label_storage[file_id]
            else:
                labels = []

            file = InlineFile(
                contents=Body,
                bucket=Bucket,
                org_slug=org_slug,
                source_id=source_id,
                name=file_name,
                id=file_id,
                category=file_category,
                labels=labels,
                tags=tags,
                metadata=metadata,
                content_encoding=ContentEncoding,
            )

            if Metadata.get("ts_workflow_id") == self.workflow.id:
                self.workflow.output_files.append(file)

            return {
                "VersionId": file.version,
                "Metadata": S3.compress_metadata_and_tags(file),
                "ContentEncoding": file.content_encoding,
                "ResponseMetadata": {"HTTPStatusCode": 200},
            }
        raise NotImplementedError

    def complete_multipart_upload(self, **kwargs):
        raise NotImplementedError

    def upload_fileobj(self, **kwargs):
        raise NotImplementedError

    def copy(self, **kwargs):
        raise NotImplementedError

    def copy_object(self, **kwargs):
        raise NotImplementedError

    def save_labels(self, file_id: str, body: str) -> dict:
        self.label_storage[file_id] = json.loads(body)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    @staticmethod
    def compress_metadata_and_tags(file: File) -> dict:
        tags = ",".join(file.tags)
        metadata = "&".join([f"{key}={value}" for key, value in file.metadata.items()])
        return {FIELDS["CUSTOM_METADATA"]: metadata, FIELDS["CUSTOM_TAGS"]: tags}

    def head_object(self, **kwargs):
        if file := self.get_datalake_file(**kwargs):
            return {
                "VersionId": file.version,
                "Metadata": S3.compress_metadata_and_tags(file),
                "ContentEncoding": file.content_encoding,
                "ResponseMetadata": {"HTTPStatusCode": 200},
            }
        raise NoSuchKey

    @staticmethod
    def get_artifact_object(key: str):
        if search := re.search(f"/ids/([^/]*)/([^/]*)/([^/]*)/schema.json", key):
            namespace, slug, version = search.groups()
            try:
                response = api.get(
                    f"/artifacts/ids/{namespace}/{slug}/{version}/files/schema"
                )
                schema = response.text
                body = MagicMock()
                body.read = lambda: body
                body.decode = lambda encoding: schema
                return {
                    "ResponseMetadata": {"HTTPStatusCode": response.status_code},
                    "Body": body,
                }
            except:
                pass
        raise NoSuchKey

    def get_datalake_file(self, **kwargs):
        if kwargs.get("Key").startswith(self.workflow.org_slug):
            return get_by_location(
                bucket=kwargs.get("Bucket"),
                key=kwargs.get("Key"),
                version=kwargs.get("VersionId", None),
            )
        raise NoSuchKey

    def get_object(self, **kwargs):
        if kwargs.get("Bucket", None) in (
            constants.ARTIFACT_BUCKET,
            constants.ARTIFACT_BUCKET_PRIVATE,
        ):
            return self.get_artifact_object(kwargs.get("Key"))

        if file := self.get_datalake_file(**kwargs):
            return {
                "VersionId": file.version,
                "Metadata": S3.compress_metadata_and_tags(file),
                "Body": file.reader(),
                "ContentEncoding": file.content_encoding,
                "ResponseMetadata": {"HTTPStatusCode": 200},
            }
        raise NoSuchKey

    @staticmethod
    def generate_presigned_url(**kwargs):
        if file := S3.get_datalake_file(**kwargs.get("Params")):
            return file.uri()
        raise NoSuchKey


original_smart_open = smart_open.open


def mock_smart_open(uri, mode, *, transport_params):
    search = re.search(f"s3://([^/]*)/([^/]*)", uri)
    bucket, file_key = search.groups()
    version = transport_params.get("version_id")
    file = get_by_location(bucket, file_key, version)
    return original_smart_open(file.uri(), mode, transport_params=transport_params)


@contextlib.contextmanager
def patch_s3(workflow: "Workflow"):
    with (
        patch.object(smart_open, "open", new=mock_smart_open),
        patch.object(s3_client, "client") as mock_client,
    ):
        mock_client.return_value = S3(workflow=workflow)
        yield
