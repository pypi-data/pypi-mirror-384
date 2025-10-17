import functools
import importlib
import json
import os
import re
import sys
import typing as t
import uuid
from contextlib import contextmanager

from ts_sdk.task.__exceptions import FatalError
from ts_sdk.task.__util_fileinfo import (
    add_labels,
    delete_labels,
    get_file_pointer,
    get_labels,
)

from .__util_adapters import CommunicationFormat, select_versioned_value
from .__util_adapters.communication_format import get_communication_format
from .__util_artifact import create_artifact_util
from .__util_command import run_command
from .__util_config import (
    MISSING_ALLOWED_IDS,
    AllowedIDS,
    FunctionConfig,
    IDSValidateWrongParams,
    MissingAllowedIDS,
    NoAllowedIdsSpecified,
)
from .__util_datalake import Datalake
from .__util_decorators import deprecated
from .__util_es_datalake import es_datalake_search_eql, es_hit_to_file_pointer
from .__util_log import Log
from .__util_merge import merge_arrays, merge_objects
from .__util_metadata import FIELDS
from .__util_permalink import ObjectType, get_permalink
from .__util_storage import Storage
from .__util_validation import (
    validate_file_labels,
    validate_file_meta,
    validate_file_tags,
)
from .data_model import AnyLabel, File, FileCategory, ReadResult

COMPLETED = "completed"
FAILED = "failed"

DEFAULT_GZIP_COMPRESS_LEVEL = int(os.environ.get("DEFAULT_GZIP_COMPRESS_LEVEL", 5))

# TODO these should be logged at a more verbose level than debug
# LOG_TAG_PRE_FUNCTION = 'pre_function_call'
# LOG_TAG_POST_FUNCTION = 'post_function_call'
LOG_TAG_SCRIPT_STARTED = "script_started"
LOG_TAG_SCRIPT_ENDED = "script_ended"

if "default_print" not in __builtins__:
    __builtins__["default_print"] = __builtins__["print"]


def wrap_log(func_name):
    def return_wrapper(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # TODO log at a finer level
            # id = str(uuid.uuid4())
            # Context.log.log({
            #     'level': 'debug',
            #     'tag': LOG_TAG_PRE_FUNCTION,
            #     'funcName': func_name,
            #     'id': id
            # })
            result = fn(*args, **kwargs)
            # Context.log.log({
            #     'level': 'debug',
            #     'tag': LOG_TAG_POST_FUNCTION,
            #     'funcName': func_name,
            #     'id': id
            # })
            return result

        return wrapper

    return return_wrapper


def camel_to_snake(value: str) -> str:
    return "".join(["_" + i.lower() if i.isupper() else i for i in value]).lstrip("_")


class Context:
    """A context object that is passed into
    the task script handler when running as part of a pipeline.
    """

    org_slug: str
    pipeline_id: str
    workflow_id: str

    master_script_namespace: str
    master_script_slug: str
    master_script_version: str

    input_file: File

    created_at: str
    task_id: str
    task_created_at: str

    pipeline_config: t.Mapping[str, str]

    platform_url: str
    platform_api_url: str
    platform_version: str

    tmp_dir: str

    def __init__(
        self,
        obj,
        datalake,
        artifact_util,
        log,
        allowed_ids: t.Union[AllowedIDS, MissingAllowedIDS] = MISSING_ALLOWED_IDS,
    ):
        self._obj = {
            **obj,
        }  # keys are later converted to snake case via "camel_to_snake"
        for key in self._obj:
            setattr(self, camel_to_snake(key), self._obj[key])
        self._datalake = datalake
        self._artifact_util = artifact_util
        self._log = log
        self._allowed_ids = allowed_ids
        self.tmp_dir = os.environ.get("TMPDIR")

    @property
    def allowed_ids(self) -> AllowedIDS:
        """Returns AllowedIDS object that either stores the list of allowed ids or
        a dict of allowed ids in `allowed_ids` attribute. These values are populated
        from `config.json`

        Raises:
            NoAllowedIdsSpecified: Raised if `config.json` has no `allowedIds` key
            for the task-script's slug.

        Returns:
            AllowedIDS object
        """
        if self._allowed_ids is MISSING_ALLOWED_IDS:
            raise NoAllowedIdsSpecified(
                "No 'allowedIds' found for the function being called. Please check 'config.json'."
            )
        return self._allowed_ids

    @wrap_log("context.get_file_pointer")
    def get_file_pointer(self, file_id: str) -> File:
        return get_file_pointer(self._obj, file_id)

    @wrap_log("context.read_file")
    def read_file(self, file: File, form: str = "body") -> ReadResult:
        """Reads a file from the data lake and returns its contents in one of
        three forms.

        If form='body' (the default), then result['body'] holds the contents of
        the file as a byte array. This approach cannot handle large files that
        don't fit in memory.

        If form='file_obj', then result['file_obj'] is a file-like object that
        can be used to access the body in a streaming manner. This object can
        be passed to Python libraries such as Pandas.

        If form='download', then result['download'] is the file name of a local
        file that has been downloaded from the specified data lake file. This
        is useful when the data needs to be processed by native code (e.g.
        SQLite) or an external utility program.

        >>> import json
        >>> import pandas as pd
        >>> import sqlite3
        >>> def task(input, context):
        ...     f = context.read_file(input, form='body')
        ...     json.loads(f['body'])
        ...
        ...     f = context.read_file(input, form='file_obj')
        ...     df = pd.read_csv(f['file_obj'])
        ...
        ...     f = context.read_file(input, form='download')
        ...     con = sqlite3.connect(f['download'])
        ...     df = pd.read_sql_query('SELECT * FROM foo', con)
        """

        if len(file.keys()) == 1 and file["fileId"] is not None:
            es_files = self.search_eql(
                {"size": 1, "query": {"term": {"fileId": {"value": file["fileId"]}}}},
                returns="filePointers",
            )
            if len(es_files) == 0:
                raise Exception(f"File with fileId {file['fileId']} not found!")
            file = es_files[0]

        return self._datalake.read_file(file, form, self.tmp_dir)

    @wrap_log("context.write_file")
    def write_file(
        self,
        content: t.Union[bytes, t.BinaryIO, str, t.Dict],
        file_name: str,
        file_category: FileCategory,
        ids: t.Optional[str] = None,
        custom_metadata: t.Optional[t.Mapping[str, str]] = None,
        custom_tags: t.Iterable[str] = (),
        source_type: t.Optional[str] = None,
        labels: t.Collection[AnyLabel] = (),
        gzip_compress_level: int = DEFAULT_GZIP_COMPRESS_LEVEL,
    ) -> File:
        """
        Writes output object to the data lake

        If content is a dictionary is passed with "IDS" file_category, IDS validation will be
        performed before serializing and writing dict to data lake.

        If `allowedIds` is defined for the function in `config.json` then IDS file will be
        created only if `ids` is allowed, i.e.:
        1. if `ids` passed is present as `allowedIds` for the function slug in config.json
        2. if `ids` passed is `None` and `allowedIDS` for function slug list only one IDS, then it
        will be used for writing the IDS file.
        An error will be raised if:
        1. `allowedIds` is not defined for the function slug and the value of the `ids` parameter is `None`
        2. `allowedIds` is set to `null` for the function slug (since that indicates the function does not write IDSes)

        Arguments:
            content: Data to be written, can be a file-like object, string or an IDS dictionary
            file_name: Filename of the object to be written
            file_category: Category of file to be written
            ids: (Optional) IDS value in format of NAMESPACE/SLUG:VERSION
            custom_metadata: (Optional) Additional metadata to be written
            custom_tags: (Optional) Additional tags to be written
            source_type: (Optional) Source type of object being written
            labels: (Optional) Labels for object being written
            gzip_compress_level: (Optional) 1 is fastest and 9 is slowest. 0 is no compression. The default is 5
        """

        if file_category == "IDS" and self._allowed_ids != MISSING_ALLOWED_IDS:
            ids = self.allowed_ids.get_ids_to_be_written(
                ids_requested_to_be_written=ids
            )

        if custom_metadata is None:
            custom_metadata = {}
        raw_file = self.input_file
        validate_file_meta(custom_metadata)
        validate_file_tags(custom_tags)
        validate_file_labels(labels)
        file_meta = {
            # in case custom_metadata & custom_tags are undefined in raw_file meta
            FIELDS["CUSTOM_METADATA"]: "",
            FIELDS["CUSTOM_TAGS"]: "",
            **self._datalake.get_file_meta(raw_file),
        }
        file_meta[FIELDS["CUSTOM_METADATA"]] = merge_objects(
            file_meta.get(FIELDS["CUSTOM_METADATA"], ""), custom_metadata
        )
        file_meta[FIELDS["CUSTOM_TAGS"]] = merge_arrays(
            file_meta.get(FIELDS["CUSTOM_TAGS"], ""),
            custom_tags,
        )
        file_meta[FIELDS["TRACE_ID"]] = file_meta.get(
            FIELDS["TRACE_ID"], raw_file["fileId"]
        )
        return self._datalake.write_file(
            context=self._obj,
            content=content,
            file_name=file_name,
            file_category=file_category,
            raw_file=raw_file,
            file_meta=file_meta,
            ids=ids,
            source_type=source_type,
            labels=labels,
            gzip_compress_level=gzip_compress_level,
        )

    @wrap_log("context.write_detached_file")
    def write_detached_file(
        self,
        content: t.Union[bytes, t.BinaryIO, str, t.Dict],
        file_name: str,
        file_category: FileCategory,
        custom_metadata: t.Optional[t.Mapping[str, str]] = None,
        custom_tags: t.Iterable[str] = (),
        source_type: t.Optional[str] = "pipeline",
        source_name: t.Optional[str] = None,
        source_id: t.Optional[str] = None,
        labels: t.Collection[AnyLabel] = (),
        gzip_compress_level: int = DEFAULT_GZIP_COMPRESS_LEVEL,
    ) -> File:
        """
        Writes an object to the data lake (detached)

        Arguments:
            content: Data to be written, can be a file-like object, string or an IDS dictionary
            file_name: Filename of the object to be written
            file_category: Category of file to be written
            custom_metadata: (Optional) Additional metadata to be written
            custom_tags: (Optional) Additional tags to be written
            source_type: (Optional) Source type of object being written
            source_name: (Optional) Source name of object being written
            source_id: (Optional) Source id of object being written
            labels: (Optional) Labels for object being written
            gzip_compress_level: (Optional) 1 is fastest and 9 is slowest. 0 is no compression. The default is 5
        """
        if custom_metadata is None:
            custom_metadata = {}
        validate_file_meta(custom_metadata)
        validate_file_tags(custom_tags)
        validate_file_labels(labels)
        file_meta = {
            FIELDS["CUSTOM_METADATA"]: merge_objects("", custom_metadata),
            FIELDS["CUSTOM_TAGS"]: merge_arrays("", custom_tags),
            FIELDS["SOURCE_TYPE"]: source_type,
            FIELDS["SOURCE_NAME"]: (
                source_name
                if source_name is not None
                else self.pipeline_config.get("pipelineName", "")
            ),
        }
        return self._datalake.write_detached_file(
            context=self._obj,
            content=content,
            org_slug=self._obj["orgSlug"],
            destination_or_source_id=(
                source_id if source_id is not None else self._obj["pipelineId"]
            ),
            file_name=file_name,
            file_category=file_category,
            file_meta=file_meta,
            labels=labels,
            gzip_compress_level=gzip_compress_level,
        )

    @wrap_log("context.get_ids")
    def get_ids(self, namespace: str, slug: str, version: str):
        """Retrieve the IDS Schema definition.

        Args:
            namespace (str): The namespace.
            slug (str): The slug (unique name).
            version (str): The version.

        Returns:
            dict: Parsed IDS schema as a Python dictionary.
        """
        return self._artifact_util["get_ids"](namespace, slug, version)

    @wrap_log("context.get_schema_artifact")
    def get_schema_artifact(self, namespace: str, slug: str, version: str):
        """Download and parse the `schema.json` file (or another specified file)
        from a Schema Artifact.
        Args:
            namespace (str): The namespace of the Schema Artifact.
            slug (str): The slug (unique name) of the Schema Artifact.
            version (str): The version of the Schema Artifact.

        Returns:
            dict: Parsed JSON content of the specified schema file.
        """
        return self._artifact_util["get_schema_artifact"](namespace, slug, version)

    @wrap_log("context.validate_ids")
    def validate_ids(
        self,
        data: t.Any,
        namespace: t.Optional[str] = None,
        slug: t.Optional[str] = None,
        version: t.Optional[str] = None,
        ignore_allowed_ids: bool = False,
    ):
        """
        1. Determine IDS from allowedIds when namespace, slug and versions are None
        2. Check if IDS is present in 'allowedIds', when `allowedIds` is defined in `config.json`.
        3. Checks validity of IDS content provided in `data`.
        Throws an error if not valid or not possible to determine IDS from allowedIds
        """

        if namespace and slug and version:
            pass
        elif namespace or slug or version:
            raise IDSValidateWrongParams(
                f"Namespace, slug and version have to be set or equal to None: {namespace}/{slug}:{version}"
            )
        else:
            # all namespace, slug and version are None
            if self._allowed_ids == MISSING_ALLOWED_IDS:
                raise IDSValidateWrongParams(
                    f"Not possible to determine the IDS to validate against: allowedIds is missing"
                )

            if self._allowed_ids.is_single():
                namespace, slug, version = self._allowed_ids.get_first().to_tuple()
            else:
                raise IDSValidateWrongParams(
                    f"Not possible to determine the IDS to validate against: allowedIds has more than 1 value"
                )

        if not ignore_allowed_ids and self._allowed_ids != MISSING_ALLOWED_IDS:
            ids_str = f"{namespace}/{slug}:{version}"
            self.allowed_ids.is_reconcilable(ids_str)

        return self._artifact_util["validate_ids"](data, namespace, slug, version)

    @wrap_log("context.write_ids")
    def write_ids(
        self,
        content_obj: t.Union[bytes, t.BinaryIO, str, t.Dict],
        file_suffix: str,
        ids: t.Optional[str] = None,
        custom_metadata: t.Optional[t.Mapping[str, str]] = None,
        custom_tags: t.Iterable[str] = (),
        source_type: t.Optional[str] = None,
        file_category: t.Optional[FileCategory] = "IDS",
        labels: t.Collection[AnyLabel] = (),
        gzip_compress_level: int = DEFAULT_GZIP_COMPRESS_LEVEL,
    ) -> File:
        """
        Writes output IDS to the data lake.  If `content_obj` is a dictionary, then it will also be validated against
        the IDS schema.
        If `allowedIds` is defined for the function in `config.json`, then the IDS file will be created only if `ids`
        is allowed ie:
        1. if `ids` passed is present as `allowedIds` for the function slug in config.json
        2. if `ids` passed is `None` and `allowedIDS` for function slug list only one IDS, then it
        will be used for writing the IDS file.
        An error will be raised if:
        1. `allowedIds` is not defined for the function slug and the value of the `ids` parameter is `None`
        2. `allowedIds` is set to `null` for the function slug (since that indicates the function does not write IDSes)

        Arguments:
            content_obj: Data to be written, can be a file-like object, string or an IDS dictionary
            file_suffix: IDS filenames follow the form {IDS_NAMESPACE}-{IDS_SLUG}-{file_suffix}.json
            ids: The IDS to use for validation.  String of the form NAMESPACE/SLUG:VERSION.  If `None` (default), an
                Exception is raised.
            custom_metadata: (Optional) Additional metadata to be written
            custom_tags: (Optional) Additional tags to be written
            source_type: (Optional) Source type of object being written.  If `None` (default), value comes from the
                value in `custom_metadata` belonging to the key "ts_source_type".  If the key does not exist, it
                defaults to "unknown"
            file_category: Category of file to be written. Defaults to "IDS".  If not "IDS" or "TMP", the category will
                be "IDS".
            labels: (Optional) Labels for object being written
            gzip_compress_level: (Optional) 1 is fastest and 9 is slowest. 0 is no compression. The default is 5
        """
        if file_category not in ("IDS", "TMP"):
            file_category = "IDS"

        if file_category == "IDS" and self._allowed_ids != MISSING_ALLOWED_IDS:
            ids = self.allowed_ids.get_ids_to_be_written(
                ids_requested_to_be_written=ids
            )

        if custom_metadata is None:
            custom_metadata = {}
        raw_file = self.input_file
        validate_file_meta(custom_metadata)
        validate_file_tags(custom_tags)
        validate_file_labels(labels)
        file_meta = {
            # in case custom_metadata & custom_tags are undefined in raw_file meta
            FIELDS["CUSTOM_METADATA"]: "",
            FIELDS["CUSTOM_TAGS"]: "",
            **self._datalake.get_file_meta(raw_file),
        }
        file_meta[FIELDS["CUSTOM_METADATA"]] = merge_objects(
            file_meta.get(FIELDS["CUSTOM_METADATA"], ""), custom_metadata
        )
        file_meta[FIELDS["CUSTOM_TAGS"]] = merge_arrays(
            file_meta.get(FIELDS["CUSTOM_TAGS"], ""),
            custom_tags,
        )
        file_meta[FIELDS["TRACE_ID"]] = file_meta.get(
            FIELDS["TRACE_ID"], raw_file["fileId"]
        )

        return self._datalake.write_ids(
            context=self._obj,
            content_obj=content_obj,
            file_suffix=file_suffix,
            raw_file=raw_file,
            file_meta=file_meta,
            ids=ids,
            source_type=source_type,
            file_category=file_category,
            labels=labels,
            gzip_compress_level=gzip_compress_level,
        )

    def get_file_name(self, file: File) -> str:
        """Returns the filename of the file not downloading it locally"""
        return self._datalake.get_file_name(file)

    @wrap_log("context.get_file_permalink")
    def get_file_permalink(self, file: File) -> str:
        return get_permalink(
            self.platform_api_url, ObjectType.FILE, self.get_file_id(file)
        )

    def get_logger(self):
        """Returns the structured logger object.
        The input should be an object (eg. containing a message field, among others).

        ...     logger = context.get_logger()
        ...     logger.log({
        ...         "message": "Starting the main parser",
        ...         "level": "info"
        ...     })

        """
        return self._log

    @deprecated(
        "'context.get_secret_config_value' deprecated, use 'context.resolve_secret' instead!"
    )
    def get_secret_config_value(self, secret_name: str, silent_on_error=True) -> str:
        """Returns the value of the secret.
        If secret is missing, empty string or throws error, depending on the second argument.
        """

        return get_secret_config_value(self._obj, secret_name, silent_on_error)

    def resolve_secret(self, secret) -> t.Optional[str]:
        """Returns the value of the secret."""

        if type(secret) is dict and "ssm" in secret:
            pipeline_config = self._obj.get("pipelineConfig")
            if f'_resolved_:{secret["ssm"]}' in pipeline_config:
                return pipeline_config.get(f'_resolved_:{secret["ssm"]}')
            key = re.sub(r"^/[^/]*/[^/]*/org-secrets/", "", secret["ssm"])
            key = re.sub(r"[^a-z0-9]+", "_", key, flags=re.IGNORECASE)
            secret_value = os.environ.get("SECRET_" + key)
            return secret_value
        return secret

    def get_presigned_url(self, file: File, ttl_sec=300) -> str:
        """Returns a time-limited HTTPS URL that can be used to access the file.
        If URL generation fails for any reason (except invalid value for ttl_sec parameter) `None` will be returned.
        """
        return self._datalake.get_presigned_url(file, ttl_sec)

    @wrap_log("context.update_metadata_tags")
    def update_metadata_tags(
        self,
        file: File,
        custom_meta: t.Optional[t.Mapping[str, str]] = None,
        custom_tags: t.Iterable[str] = (),
        options: t.Mapping[str, str] = {},
    ) -> File:
        """Updates file's custom metadata and tags.
        Use 'None' to remove a meta entry.
        New tags will be appended to existing ones.
        """
        if custom_meta is None:
            custom_meta = {}
        validate_file_meta(custom_meta)
        validate_file_tags(custom_tags)
        return self._datalake.update_metadata_tags(
            context=self._obj,
            file=file,
            custom_meta=custom_meta,
            custom_tags=custom_tags,
            options=options,
        )

    @deprecated("'context.run_command' deprecated, use 'context.run_cmd' instead!")
    @wrap_log("context.run_command")
    def run_command(
        self,
        org_slug,
        target_id,
        action,
        metadata,
        payload,
        ttl_sec=300,
        initial_delay_sec=0,
        return_command=False,
    ):
        """Invokes remote command/action on target (agent or connector) and returns its response"""
        return run_command(
            self._obj,
            org_slug,
            target_id,
            action,
            metadata,
            payload,
            ttl_sec,
            initial_delay_sec,
            return_command,
        )

    @wrap_log("context.run_cmd")
    def run_cmd(
        self,
        target_id,
        action,
        metadata,
        payload,
        ttl_sec=300,
        initial_delay_sec=0,
        return_command=False,
    ):
        """Invokes remote command/action on target (agent or connector) and returns its response"""
        return run_command(
            self._obj,
            self.org_slug,
            target_id,
            action,
            metadata,
            payload,
            ttl_sec,
            initial_delay_sec,
            return_command,
        )

    def get_file_id(self, file):
        if "fileId" in file:
            file_id = file["fileId"]
        else:
            file_metadata = self._datalake.get_file_meta(file)
            file_id = file_metadata.get(FIELDS["FILE_ID"])
        return file_id

    @wrap_log("context.add_labels")
    def add_labels(
        self,
        file: File,
        labels: t.Optional[t.Collection[AnyLabel]],
        no_propagate: bool = False,
    ):
        if validate_file_labels(labels):
            file_id = self.get_file_id(file)
            return add_labels(self._obj, file_id, labels, no_propagate)
        else:
            print(
                {
                    "level": "warning",
                    "message": "no labels provided in add_labels()!",
                }
            )
            return self.get_labels(file)

    def get_labels(self, file):
        file_id = self.get_file_id(file)
        return get_labels(self._obj, file_id)

    @wrap_log("context.delete_labels")
    def delete_labels(self, file, label_ids):
        file_id = self.get_file_id(file)
        return delete_labels(self._obj, file_id, label_ids if label_ids else [])

    @wrap_log("context.add_attributes")
    def add_attributes(
        self,
        file: File,
        custom_meta: t.Optional[t.Mapping[str, str]] = None,
        custom_tags: t.Iterable[str] = (),
        labels: t.Collection[AnyLabel] = (),
    ) -> File:
        if custom_meta is None:
            custom_meta = {}

        # case where only labels are provided
        if not custom_meta and not custom_tags:
            if labels:
                # no need to validate labels before here, because add_labels will validate for us
                self.add_labels(file, labels)
            else:
                print(
                    {
                        "level": "warning",
                        "message": "no attributes provided in add_attributes()!",
                    }
                )
            return file

        # case where meta and/or tags are specified

        new_file_id = str(uuid.uuid4())

        if validate_file_labels(labels):
            self._datalake.create_labels_file(
                target_file={**file, "fileId": new_file_id},
                # TODO: this line will overwrite the label, instead, should merge with the existing labels
                # otherwise, the behavior is different from when metadata, tag are not provided.
                labels=labels,
            )

        # metadata and tags are validated in this function
        new_file = self.update_metadata_tags(
            file=file,
            custom_meta=custom_meta,
            custom_tags=custom_tags,
            options={"new_file_id": new_file_id},
        )

        return new_file

    @wrap_log("context.search_eql")
    def search_eql(self, payload, returns="raw", query=None):
        search_res = es_datalake_search_eql(payload, query=query)
        if returns == "filePointers":
            return list(map(es_hit_to_file_pointer, search_res["hits"]["hits"]))
        return search_res

    @wrap_log("context.raise_fatal_error")
    def raise_fatal_error(self, message: str = "No message"):
        # From CommunicationFormatV2 onward, the platform supports fatal errors
        if select_versioned_value(
            {
                CommunicationFormat.V0: True,
                CommunicationFormat.V2: False,
            }
        ):
            self.get_logger().log(
                "Fatal errors are not supported in this environment, and will be treated like a regular error"
            )
        raise FatalError(message)


def output_response(storage, response, correlation_id):
    storage.writeObject({**response, "id": correlation_id})


def resolve_func(func_dir, func_slug):
    func_conf_file = os.path.join(func_dir, "config.json")
    with open(func_conf_file, "r") as file:
        func_conf = json.load(file)
    for f in func_conf["functions"]:
        if f["slug"] == func_slug:
            function = f["function"]
            break
    else:
        raise Exception(f"function not found: {func_slug}")
    # print(function)
    func_module, _, func_name = function.rpartition(".")
    return func_module, func_name


def resolve_secrets_in_pipeline_config(context_from_arg):
    secrets = {}
    pipeline_config = context_from_arg.get("pipelineConfig")
    for key in pipeline_config:
        if key.startswith("ts_secret_name_"):
            secret_name = key.split("ts_secret_name_", 1)[1]
            secrets[secret_name] = get_secret_config_value(context_from_arg, key, True)
    return secrets


def get_secret_config_value(context_from_arg, secret_name, silent_on_error=True):
    pipeline_config = context_from_arg.get("pipelineConfig")

    if secret_name.startswith("ts_secret_name_"):
        secret_short_name = secret_name.split("ts_secret_name_", 1)[1]
        secret_full_key = secret_name
    else:
        secret_short_name = secret_name
        secret_full_key = "ts_secret_name_" + secret_name

    if f"_resolved_:{secret_short_name}" in pipeline_config:
        return pipeline_config.get(f"_resolved_:{secret_short_name}")

    if (
        not secret_full_key in pipeline_config.keys()
        or pipeline_config.get(secret_full_key) is None
    ):
        if silent_on_error:
            Context.log.log(
                f"Secret {secret_full_key} not found in the workflow config."
            )
            return ""
        else:
            raise Exception(
                f"Secret {secret_full_key} not found in the workflow config."
            )

    try:
        if os.environ.get("TASK_SCRIPTS_CONTAINERS_MODE") == "ecs":
            secret_value = os.environ.get(
                "TS_SECRET_"
                + re.sub(r"[^a-z0-9]+", "_", secret_short_name, flags=re.IGNORECASE)
            )
            if secret_value is None:
                raise Exception(f"Secret {secret_short_name} not found")
            return secret_value
        raise Exception(f"Could not resolve secret value for  {secret_full_key}")
    except Exception as e:
        if silent_on_error:
            Context.log.log(e)
            return ""
        else:
            raise Exception(
                f"Could not resolve secret value for  {secret_full_key}"
            ) from e


def should_override_builtin_print():
    """
    This is the essence of CommunicationFormat v2
    If v2: don't override the built-in print, because we know
    that the fluentbit sidecar is present, and will capture all
    stdout and send it to s3/cloudwatch
    :return:
    """
    return select_versioned_value(
        {
            CommunicationFormat.V0: True,
            CommunicationFormat.V2: False,
        }
    )


def construct_shadow_print(log: Log):
    """
    Constructs a function that captures `log`
    Intended to replace the __builtin__ print statement and pass the arguments to Log class
    which will decorate log messages with more information
    :param log:
    :return:
    """

    def shadow_print(*values, sep=" ", end="\n", file=sys.stdout, flush=False):
        """
        If a file is not sys.stdout:
            uses the default print because a user is attempting to print to a file
        Otherwise, defers to Log.log
        """
        if file is not sys.stdout:
            __builtins__["default_print"](
                *values, sep=sep, end=end, file=file, flush=flush
            )
        else:
            # No need to pass flush to our logger, the script's dockerfile is set up to always flush stdout
            log.log(*values, sep=sep)

    return shadow_print


@contextmanager
def module(module_name: str):
    imported_module = importlib.import_module(module_name)
    try:
        yield imported_module
    finally:
        del sys.modules[module_name]


def run(
    input,
    context_from_arg,
    func,
    correlation_id,
    func_dir,
    storage_type,
    storage_bucket,
    storage_file_key,
    storage_endpoint,
    artifact_bucket,
    artifact_prefix,
    artifact_endpoint,
    artifact_file_key,
    artifact_bucket_private,
    artifact_prefix_private,
    artifact_endpoint_private,
    store_output=True,
):
    log = Log(context_from_arg)
    Context.log = log
    log.log({"level": "debug", "tag": LOG_TAG_SCRIPT_STARTED})
    log.log(
        {
            "level": "debug",
            "communication format version": get_communication_format().value,
        }
    )
    if storage_type != "s3file":
        raise Exception(f"Invalid storage type: {storage_type}")

    context_from_arg["pipelineConfig"] = {
        **context_from_arg.get("pipelineConfig"),
        **resolve_secrets_in_pipeline_config(context_from_arg),
    }

    # override print function with our own, which decorates with workflow id and task id
    if should_override_builtin_print():
        __builtins__["print"] = construct_shadow_print(log)

    prefix = artifact_prefix if artifact_prefix else ""
    if not prefix and artifact_file_key:
        prefix = re.sub(r"ids/.*$", "", artifact_file_key)

    artifact_util = create_artifact_util(
        [
            {
                "bucket": artifact_bucket,
                "prefix": prefix,
                "endpoint": artifact_endpoint,
                "namespacePattern": r"^(common|client-.*)$",
            },
            {
                "name": "private",
                "bucket": artifact_bucket_private,
                "prefix": artifact_prefix_private if artifact_prefix_private else "",
                "endpoint": artifact_endpoint_private,
                "namespacePattern": r"^(private-.*)$",
            },
        ]
    )
    storage = Storage(storage_bucket, storage_file_key, storage_endpoint)
    datalake = Datalake(storage_endpoint, artifact_util)
    func_config = FunctionConfig.from_task_script_dir(func_dir=func_dir, func_slug=func)
    context = Context(
        context_from_arg,
        datalake,
        artifact_util,
        log,
        allowed_ids=func_config.allowed_ids,
    )
    func_module, func_name = resolve_func(func_dir, func)
    try:
        with module(func_module) as imported_module:
            # TODO log at a finer level
            # log.log({ 'level': 'debug', 'tag': LOG_TAG_PRE_FUNCTION, 'funcName': f'{func_module}.{func_name}' })
            result = getattr(imported_module, func_name)(input, context)
            # log.log({ 'level': 'debug', 'tag': LOG_TAG_POST_FUNCTION, 'funcName': func_name })

        if store_output:
            output_response(
                storage, {"type": COMPLETED, "result": result}, correlation_id
            )

        taskResult = {
            "status": "completed",
            "result": result if result is not None else {},
        }
    except MemoryError as e:
        log.log(e)
        log.log({"level": "error", "message": "Got MemoryError"})
        os._exit(137)
    except FatalError as fatal_error:
        log.log(fatal_error)
        log.log(
            {"level": "error", "message": f"Got FatalError: '{fatal_error.message}'"}
        )
        os._exit(126)
    except Exception as e:
        log.log(e)

        if "SIGKILL" in str(e):
            log.log({"level": "error", "message": "Got SIGKILL - possible OOM"})
            os._exit(137)

        if store_output:
            output_response(storage, {"type": FAILED, "error": str(e)}, correlation_id)

        taskResult = {"status": "failed", "result": {"error": str(e)}}
    log.log({"level": "debug", "tag": LOG_TAG_SCRIPT_ENDED})
    return taskResult
