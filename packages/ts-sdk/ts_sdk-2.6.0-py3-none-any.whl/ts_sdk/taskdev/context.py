import io
import os
import pathlib
import tempfile
import typing as t

import typing_extensions as te

from ..task.__util_config import (
    MISSING_ALLOWED_IDS,
    AllowedIDS,
    FunctionConfig,
    MissingAllowedIDS,
)
from ..task.__util_log import Log
from ..task.data_model import File, FileCategory, ReadResult


class Context:
    """A development-time version of the context object that is passed into
    the task script handler when running as part of a pipeline.
    """

    def __init__(self, slug: t.Optional[str] = None, pipeline_config={}):
        self._storage = {}
        self._pipeline_config = pipeline_config
        self._log = Log({})
        self.slug = slug
        self._allowed_ids = self._get_allowed_ids()

    @property
    def allowed_ids(self):
        if isinstance(self._allowed_ids, MissingAllowedIDS):
            raise KeyError("'allowedIds' is not present in config.json")

        return self._allowed_ids

    def _get_allowed_ids(self) -> t.Union[MissingAllowedIDS, AllowedIDS]:
        if self.slug:
            func_dir = pathlib.Path(os.getcwd())
            func_config = FunctionConfig.from_task_script_dir(func_dir, self.slug)
            return func_config.allowed_ids
        return MISSING_ALLOWED_IDS

    @property
    def pipeline_config(self) -> t.Dict[str, str]:
        """Pipeline configuration including secrets."""
        return self._pipeline_config

    def read_file(self, file: File, form: str = "body") -> ReadResult:
        if form == "body":
            return self._storage[file["fileKey"]]
        elif form == "file_obj":
            result = self._storage[file["fileKey"]]
            body = result["body"]
            buf = io.BytesIO()
            buf.write(body)
            buf.seek(0)
            result["file_obj"] = buf
            return result
        elif form == "download":
            result = self._storage[file["fileKey"]]
            with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tf:
                tf.write(result["body"])
                result["download"] = tf.name
            return result
        raise Exception(f"Invalid form: {form}")

    def write_file(
        self,
        content: t.AnyStr,
        file_name: str,
        file_category: FileCategory,
        ids: str = None,
        custom_metadata: t.Dict[str, str] = None,
        custom_tags: t.List[str] = None,
        source_type: str = None,
        labels: t.Iterable[t.Mapping[te.Literal["name", "value"], str]] = [],
    ) -> File:
        if (
            self.slug
            and file_category == "IDS"
            and self._allowed_ids != MISSING_ALLOWED_IDS
        ):
            ids = self.allowed_ids.get_ids_to_be_written(ids)

        if type(content) == str:
            content = content.encode("UTF-8")

        self._storage[file_name] = {
            "metadata": {
                "TS_IDS": ids,
                "TS_SOURCE_TYPE": source_type,
                "TS_FILE_CATEGORY": file_category,
            },
            "body": content,
            "custom_metadata": custom_metadata,
            "custom_tags": custom_tags,
        }
        return {
            "type": "s3file",
            "bucket": "fake-unittest-bucket",
            "fileKey": file_name,
        }

    def get_ids(self, namespace: str, slug: str, version: str):
        return {}

    # always return true in local context
    def validate_ids(self, data: dict, namespace: str, slug: str, version: str) -> bool:
        if self.slug and self._allowed_ids != MISSING_ALLOWED_IDS:
            ids_str = f"{namespace}/{slug}:{version}"
            self.allowed_ids.is_reconcilable(ids_str)

        return True

    def write_ids(
        self,
        content_obj,
        file_suffix: str,
        ids: t.Optional[str] = None,
        custom_metadata: t.Mapping[str, str] = {},
        custom_tags: t.Iterable[str] = [],
        source_type: t.Optional[str] = None,
        file_category: t.Optional[str] = "IDS",
        labels: t.Iterable[t.Mapping[te.Literal["name", "value"], str]] = [],
    ) -> File:
        if file_category not in ["TMP", "IDS"]:
            file_category = "IDS"

        if (
            self.slug
            and file_category == "IDS"
            and self._allowed_ids != MISSING_ALLOWED_IDS
        ):
            ids = self.allowed_ids.get_ids_to_be_written(ids)

        return {}

    def get_file_name(self, file: File) -> str:
        return ""

    def get_logger(self):
        return self._log

    def get_secret_config_value(self, secret_name: str, silent_on_error=True) -> str:
        return self._pipeline_config[secret_name]

    def resolve_secret(self, secret) -> str:
        return secret

    def get_presigned_url(self, file: File, ttl_sec=300) -> str:
        return ""

    def update_metadata_tags(
        self,
        file: File,
        custom_meta: t.Mapping[str, str] = {},
        custom_tags: t.Iterable[str] = [],
    ) -> File:
        return {}

    def run_command(
        self,
        org_slug,
        target_id,
        action,
        metadata,
        payload,
        ttl_sec=300,
        initial_delay_sec=0,
    ):
        return {}

    def add_labels(self, file, labels):
        return {}

    def get_labels(self, file):
        return {}

    def delete_labels(self, file):
        return {}
