"""Datalake functions"""

import gzip
import io
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Collection, Dict, Optional, Tuple, Union
from urllib.parse import parse_qs, urlencode
from uuid import uuid4

import simplejson as json
import smart_open

from . import s3_client
from .__util_metadata import FIELDS
from .__util_versioned_ref import VersionedRef
from .data_model import AnyLabel, ArtifactUtilDict
from .encoders import DataclassEncoder

WRITE_ALLOWED_CATEGORIES = ["IDS", "PROCESSED", "TMP"]
DISABLE_GZIP = bool(os.environ.get("DISABLE_GZIP"))
ENV = os.environ.get("ENV")
AWS_REGION = os.environ.get("AWS_REGION")
# don't use multipart if file size is smaller than 100MB
MULTIPART_SIZE = int(os.environ.get("MULTIPART_SIZE_MB", 100)) * 2**20
LARGE_FILE_SIZE_THRESHOLD_BYTES = (
    5 * 2**30
)  # We have to handle files that are > 5 GB differently


def lowerMetadataKeys(metadata: dict) -> dict:
    """Lowercases all keys in a dict"""
    return {k.lower(): v for k, v in metadata.items()}


def resolveCustomMetadataAndTags(metadata: dict) -> dict:
    custom_metadata_str = metadata.get(FIELDS["CUSTOM_METADATA"], "") or ""
    custom_tags_str = metadata.get(FIELDS["CUSTOM_TAGS"], "") or ""
    if not custom_tags_str:
        custom_tags = []
    else:
        custom_tags = custom_tags_str.split(",")

    return {
        "custom_metadata": parse_query(custom_metadata_str),
        "custom_tags": custom_tags,
    }


def getOrEmptyString(dic, key, default=""):
    val = dic.get(key, default)
    if val is None:
        return default
    return val


class InvalidPathException(Exception):
    """Exception for invalid path, listing path and reason"""

    def __init__(self, path, reason):
        super().__init__(f"Invalid path {path}: {reason}")
        self.path = path
        self.reason = reason


def getUpdatedPipelineHistoryStr(pipeline_id, existing_pipeline_history):
    new_pipeline_history = ""
    if existing_pipeline_history == "":
        new_pipeline_history = pipeline_id
    else:
        if pipeline_id in existing_pipeline_history:
            new_pipeline_history = existing_pipeline_history
        else:
            new_pipeline_history = existing_pipeline_history + "," + pipeline_id
    return new_pipeline_history


def parse_query(query_string: str) -> dict:
    result = dict()
    if not isinstance(query_string, str):
        return result
    if "?" in query_string:
        query_string = query_string.split("?")[-1]
    if "#" in query_string:
        query_string = query_string.split("#")[0]
    for key, values in parse_qs(query_string).items():
        if len(values) == 1:
            result[key] = values[0]
        else:
            result[key] = values
    return result


class S3FileobjUploader:
    """AWS S3 File object uploader"""

    def __init__(
        self, s3, fileobj, params, options={"disable_gzip": False, "compresslevel": 5}
    ):
        self.s3 = s3
        self.fileobj = fileobj
        self.params = params
        self.disable_gzip = options.get("disable_gzip", False)
        self.compresslevel = options.get("compresslevel", 5)
        self.stream = io.BytesIO()
        self.part_count = 0
        self.multipart = None
        self.parts = []
        if not self.disable_gzip:
            self.compressor = gzip.GzipFile(
                fileobj=self.stream, mode="wb", compresslevel=self.compresslevel
            )

    def _upload_part(self):
        print(f"upload multipart {self.part_count}")
        if self.part_count == 0:
            self.multipart = self.s3.create_multipart_upload(**self.params)
        self.part_count += 1
        self.stream.seek(0)
        part = self.s3.upload_part(
            Body=self.stream,
            Bucket=self.multipart["Bucket"],
            Key=self.multipart["Key"],
            PartNumber=self.part_count,
            UploadId=self.multipart["UploadId"],
        )
        self.parts.append({**part, "PartNumber": self.part_count})
        self.stream.seek(0)
        self.stream.truncate()

    def _upload_last_part(self):
        if self.part_count == 0:
            self.stream.seek(0)
            return self.s3.put_object(Body=self.stream, **self.params)
        self._upload_part()
        parts = []
        for part in self.parts:
            parts.append({"ETag": part["ETag"], "PartNumber": part["PartNumber"]})
        return self.s3.complete_multipart_upload(
            Bucket=self.multipart["Bucket"],
            Key=self.multipart["Key"],
            UploadId=self.multipart["UploadId"],
            MultipartUpload={"Parts": parts},
        )

    def upload(self):
        while True:
            chunk = self.fileobj.read(1024 * 1024)
            if not chunk:
                if not self.disable_gzip:
                    self.compressor.close()
                return self._upload_last_part()
            if self.disable_gzip:
                self.stream.write(chunk)
            else:
                self.compressor.write(chunk)
            if self.stream.tell() >= MULTIPART_SIZE:
                self._upload_part()


class MissingValidatorException(Exception):
    """An IDS cannot be validated because validator could not be found"""


class InvalidFileCategoryError(Exception):
    """The 'file category' is not valid. See :const:`~WRITE_ALLOWED_CATEGORIES`."""


class Datalake:
    """S3 Datalake class"""

    def __init__(self, endpoint, ids_util: Optional[ArtifactUtilDict] = None):
        self._ids_util = ids_util
        if endpoint:
            self.s3 = s3_client.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id="123",
                aws_secret_access_key="abc",
                region_name=AWS_REGION,
                config=s3_client.Config(signature_version="s3v4"),
            )
        else:
            self.s3 = s3_client.client(
                "s3",
                region_name=AWS_REGION,
                config=s3_client.Config(signature_version="s3v4"),
            )

    def get_s3_head(self, file: dict):
        """Retrieve first object from S3 bucket"""
        bucket = file["bucket"]
        file_key = file["fileKey"]
        if "version" in file:
            file_version = file["version"]
            head = self.s3.head_object(
                Bucket=bucket, Key=file_key, VersionId=file_version
            )
        else:
            head = self.s3.head_object(Bucket=bucket, Key=file_key)

        return head

    def get_file_meta(self, file):
        """Return lowercased metadata dictionary of file argument"""
        head = self.get_s3_head(file)
        return lowerMetadataKeys(head.get("Metadata"))

    def read_file(self, file, form="body", tmp_dir="/tmp"):
        """Read file from S3"""
        bucket = file["bucket"]
        file_key = file["fileKey"]
        if "version" in file:
            kwargs = {"VersionId": file["version"]}
        else:
            kwargs = {}

        if form == "body":
            response = self.s3.get_object(Bucket=bucket, Key=file_key, **kwargs)
        elif form in ["file_obj", "download"]:
            response = self.s3.head_object(Bucket=bucket, Key=file_key, **kwargs)
        else:
            raise ValueError(
                f"Invalid form={form}; supported values are body, file_obj and download"
            )

        status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status_code != 200:
            print({"level": "error", "message": response})
            raise Exception("Invalid response code")

        meta = lowerMetadataKeys(response.get("Metadata"))
        result = {"metadata": meta, **resolveCustomMetadataAndTags(meta)}

        if form == "body":
            content = response.get("Body").read()
            if response.get("ContentEncoding") == "gzip":
                result["body"] = gzip.decompress(content)
            else:
                result["body"] = content
        else:
            file_obj = smart_open.open(
                f"s3://{bucket}/{file_key}",
                "rb",
                transport_params={
                    "version_id": file.get("version"),
                    "client": self.s3,
                },
            )
            if response.get("ContentEncoding") == "gzip":
                file_obj = gzip.open(file_obj)

            if form == "download":
                with tempfile.NamedTemporaryFile(
                    mode="wb", delete=False, dir=tmp_dir
                ) as temp:
                    shutil.copyfileobj(file_obj, temp)
                    result["download"] = temp.name
                file_obj.close()
            else:
                result["file_obj"] = file_obj

        return result

    @classmethod
    def _is_file_path_valid(cls, filepath) -> Tuple[bool, str]:
        filepath = Path(filepath)
        if filepath.name == ".." or ".." in (
            parent.name for parent in filepath.parents
        ):
            return False, 'Path cannot contain a directory ".."'
        return True, ""

    @classmethod
    def _should_disable_gzip(cls, compression_level: int) -> bool:
        if compression_level == 0:
            return True
        else:
            return DISABLE_GZIP

    def write_file(
        self,
        context,
        content: Union[str, bytes, io.BytesIO, Dict],
        file_name: str,
        file_category: str,
        raw_file,
        file_meta,
        ids: str = None,
        source_type: Optional[str] = None,
        labels: Collection[AnyLabel] = (),
        gzip_compress_level: int = 5,
    ) -> dict:
        """Write file to S3"""
        if file_category not in WRITE_ALLOWED_CATEGORIES:
            raise InvalidFileCategoryError(
                f"{file_category} is not allowed category for write_file"
            )
        pattern = "(.*?)/(.*?)/(?:.*?)/(.*)"
        raw_file_key = re.sub("/{2,}", "/", raw_file["fileKey"])
        match = re.match(pattern, raw_file_key, flags=re.DOTALL)
        if not match:
            raise Exception(f'Raw file key {raw_file_key} does not match "{pattern}"')
        org_slug, destination_or_source_id, raw_file_path = match.groups()
        return self.write_detached_file(
            context=context,
            content=content,
            org_slug=org_slug,
            destination_or_source_id=destination_or_source_id,
            file_name=os.path.join(raw_file_path, file_name),
            file_category=file_category,
            file_meta=file_meta,
            ids=ids,
            source_type=source_type,
            labels=labels,
            gzip_compress_level=gzip_compress_level,
            bucket=raw_file["bucket"],
        )

    def write_detached_file(
        self,
        context,
        content: Union[str, bytes, io.BytesIO, Dict],
        org_slug: str,
        destination_or_source_id: str,
        file_name: str,
        file_category: str,
        file_meta,
        ids: str = None,
        source_type: Optional[str] = None,
        labels: Collection[AnyLabel] = (),
        gzip_compress_level: int = 5,
        bucket: str = os.environ.get("DATALAKE_BUCKET", None),
    ) -> dict:
        """Write file to S3"""
        disable_gzip = Datalake._should_disable_gzip(gzip_compress_level)

        if file_category == "IDS" and ids is None:
            raise Exception("ids can not be None when file_category is IDS")
        if source_type is not None:
            source_type_match = re.match("^[-a-z0-9]+$", source_type)
            if not source_type_match:
                raise Exception(
                    f'Source type "{source_type}" contains invalid character or upper case letter'
                )
        else:
            source_type = getOrEmptyString(file_meta, FIELDS["SOURCE_TYPE"], "unknown")

        file_key = os.path.join(
            org_slug, destination_or_source_id, file_category, file_name
        )

        is_valid_file_key, reason = self._is_file_path_valid(file_key)
        if not is_valid_file_key:
            raise InvalidPathException(file_key, reason)

        pipeline_config = context.get("pipelineConfig", {})
        pipeline_history_str = getUpdatedPipelineHistoryStr(
            getOrEmptyString(context, "pipelineId"),
            getOrEmptyString(file_meta, FIELDS["PIPELINE_HISTORY"]),
        )
        file_id = str(uuid4())
        ids_obj = VersionedRef(composite=ids)
        meta = {
            # constant
            FIELDS["INTEGRATION_TYPE"]: "datapipeline",
            FIELDS["VERSION"]: "2",
            # generated
            FIELDS["FILE_ID"]: file_id,
            # from raw file
            FIELDS["RAW_FILE_ID"]: getOrEmptyString(file_meta, FIELDS["FILE_ID"]),
            FIELDS["CUSTOM_METADATA"]: getOrEmptyString(
                file_meta, FIELDS["CUSTOM_METADATA"]
            ),
            FIELDS["CUSTOM_TAGS"]: getOrEmptyString(file_meta, FIELDS["CUSTOM_TAGS"]),
            FIELDS["SOURCE_ID"]: getOrEmptyString(file_meta, FIELDS["SOURCE_ID"]),
            FIELDS["DESTINATION_ID"]: getOrEmptyString(
                file_meta, FIELDS["DESTINATION_ID"]
            ),
            FIELDS["SOURCE_NAME"]: getOrEmptyString(file_meta, FIELDS["SOURCE_NAME"]),
            FIELDS["SOURCE_TYPE"]: source_type,
            FIELDS["TRACE_ID"]: getOrEmptyString(
                file_meta, FIELDS["TRACE_ID"], file_id
            ),
            # IDS/TMP
            **(
                {
                    FIELDS["IDS"]: ids_obj.composite,
                    FIELDS["IDS_TYPE"]: ids_obj.name,
                    FIELDS["IDS_VERSION"]: ids_obj.version,
                }
                if ids is not None and file_category in ["IDS", "TMP"]
                else {}
            ),
            # from pipeline context
            FIELDS["INTEGRATION_ID"]: getOrEmptyString(
                context, "pipelineId"
            ),  # pipeline id
            # https://github.com/tetrascience/ts-service-pipeline/blob/development/src/models/create-workflow-command.ts#L150
            FIELDS["INTEGRATION_NAME"]: getOrEmptyString(
                pipeline_config, "pipelineName"
            )[:254],
            FIELDS["PIPELINE_ID"]: getOrEmptyString(context, "pipelineId"),
            FIELDS["PIPELINE_WORKFLOW_ID"]: getOrEmptyString(context, "workflowId"),
            FIELDS["PIPELINE_MASTER_SCRIPT"]: (
                f"{context.get('masterScriptNamespace', '')}/{context.get('masterScriptSlug', '')}"
                f":{context.get('masterScriptVersion', '')}"
            ),
            FIELDS["PIPELINE_TASK_EXECUTION_ID"]: getOrEmptyString(context, "taskId"),
            FIELDS["PIPELINE_TASK_SCRIPT"]: getOrEmptyString(context, "taskScript"),
            FIELDS["PIPELINE_TASK_SLUG"]: getOrEmptyString(context, "taskSlug"),
            FIELDS["PIPELINE_HISTORY"]: pipeline_history_str,
            **(
                {FIELDS["API_USER_ID"]: os.getenv("TASK_USER_ID")}
                if os.getenv("TASK_USER_ID")
                else {}
            ),
        }

        if bucket is None:
            raise EnvironmentError(
                f"DATALAKE_BUCKET env or input file bucket is not set!"
            )

        params = {
            "Bucket": bucket,
            "Key": file_key,
            "Metadata": meta,
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": f"alias/customer-key-{ENV}-{org_slug}",
        }

        if not disable_gzip:
            params["ContentEncoding"] = "gzip"

        if len(labels) > 0:
            self.create_labels_file(
                target_file={
                    "type": "s3file",
                    "bucket": bucket,
                    "fileKey": file_key,
                    "fileId": file_id,
                },
                labels=labels,
                sse_kms_key_id=f"alias/customer-key-{ENV}-{org_slug}",
            )

        if hasattr(content, "read"):
            # BytesIO object has .read() attribute
            response = S3FileobjUploader(
                self.s3,
                content,
                params,
                {"disable_gzip": disable_gzip, "compresslevel": gzip_compress_level},
            ).upload()
            # fakeS3 does not return VersionId, so use '' to avoid an exception
            version_id = response.get("VersionId", "")
            print({"level": "debug", "message": "file created", "response": response})
        else:
            # Otherwise `content` is either str, bytes or dict
            if isinstance(content, dict):
                if file_category == "IDS":
                    if self._ids_util is not None and "validate_ids" in self._ids_util:
                        self._ids_util["validate_ids"](
                            content, ids_obj.namespace, ids_obj.name, ids_obj.version
                        )
                    else:
                        raise MissingValidatorException
                    content = json.dumps(content, ignore_nan=True)
                else:
                    raise Exception("Writing non-IDS dicts to S3 is not supported")

            if not disable_gzip:
                if isinstance(content, str):
                    content = content.encode()
                content = gzip.compress(content, compresslevel=gzip_compress_level)

            if len(content) >= LARGE_FILE_SIZE_THRESHOLD_BYTES:
                print({"level": "debug", "message": "writing a 5+ GB file to s3"})

                # the upload_fileobj method requires a file like object that implements read. This
                # means we have to wrap content into an in memory stream. We will use BytesIO
                # instead of StringIO since the metadata has to be encoded. This means that if
                # content is a string, we have to convert it to bytes first.
                file_like_obj = None
                if isinstance(content, str):
                    file_like_obj = io.BytesIO(content.encode("utf-8"))
                else:
                    # content was already bytes so we should not try to encode it again
                    file_like_obj = io.BytesIO(content)
                try:
                    extra_args = self.extract_extra_args_from_params(params)

                    self.s3.upload_fileobj(
                        Fileobj=file_like_obj,
                        Bucket=bucket,
                        Key=file_key,
                        ExtraArgs=extra_args,
                    )
                    version_id = self.get_latest_obj_version(bucket, file_key)
                    print({"level": "debug", "message": "file created"})

                except Exception as exc:
                    raise Exception(
                        f"encountered an error updating the metadata because of {exc}"
                    ) from exc
                finally:
                    file_like_obj.close()
            else:
                response = self.s3.put_object(Body=content, **params)
                # fakeS3 does not return VersionId, so use '' to avoid an exception
                version_id = response.get("VersionId", "")
                print(
                    {"level": "debug", "message": "file created", "response": response}
                )

        result_file = {
            "type": "s3file",
            "bucket": bucket,
            "fileKey": file_key,
            "fileId": file_id,
            "version": version_id,
        }

        return result_file

    def update_metadata_tags(
        self,
        context: dict,
        file: dict,
        custom_meta: dict,
        custom_tags: list,
        options: dict = {},
    ):
        """Update S3 metadata tags"""
        bucket = file["bucket"]
        file_key = file["fileKey"]

        head = self.get_s3_head(file)
        current_meta = lowerMetadataKeys(head.get("Metadata"))

        if FIELDS["FILE_ID"] not in current_meta:
            raise KeyError(f"{FIELDS['FILE_ID']} not found in meta!")

        if (not custom_meta) and (not custom_tags):
            print(
                {
                    "level": "debug",
                    "message": "no action taken because no metadata or tags provided",
                }
            )
            return file

        is_ascii = (
            lambda s: s and isinstance(s, str) and bool(re.match(r"^[\x00-\x7F]*$", s))
        )

        custom_meta_str = current_meta.get(FIELDS["CUSTOM_METADATA"], "") or ""
        current_custom_meta = parse_query(custom_meta_str)
        if custom_meta:
            custom_meta_merged = {**current_custom_meta, **custom_meta}
            custom_meta_merged = {
                k: v for k, v in custom_meta_merged.items() if v is not None
            }
            for k, v in custom_meta_merged.items():
                if not is_ascii(k):
                    raise Exception(f"Metadata key {k} contains non-ASCII character")
                if not is_ascii(str(v)):
                    raise Exception(f"Metadata value {v} contains non-ASCII character")
            custom_meta_str = urlencode(custom_meta_merged)

        custom_tags_str = current_meta.get(FIELDS["CUSTOM_TAGS"], "")
        if custom_tags:
            custom_tags = list(map(str, custom_tags))
            for tag in custom_tags:
                if not is_ascii(tag):
                    raise Exception(f"Tag {tag} contains non-ASCII character")
            new_custom_tags = list(set(custom_tags_str.split(",") + custom_tags))
            new_custom_tags.sort()
            custom_tags_str = ",".join([t for t in new_custom_tags if t])

        if len(custom_meta_str) + len(custom_tags_str) >= 1024 * 1.5:
            raise Exception("Metadata and tags length larger than 1.5KB")

        new_file_id = options.get("new_file_id", str(uuid4()))

        pipeline_config = context.get("pipelineConfig", {})

        pipeline_history_str = getUpdatedPipelineHistoryStr(
            getOrEmptyString(context, "pipelineId"),
            getOrEmptyString(current_meta, FIELDS["PIPELINE_HISTORY"]),
        )

        params = {
            "Bucket": bucket,
            "CopySource": f"/{bucket}/{file_key}",
            # 'CopySourceIfUnmodifiedSince': head['LastModified'], # ensure no conflict?
            "Key": file_key,
            "ContentEncoding": head.get("ContentEncoding", None),
            "ContentType": head["ContentType"],
            "Metadata": {
                **current_meta,
                # constant
                FIELDS["INTEGRATION_TYPE"]: "datapipeline",
                FIELDS["VERSION"]: "2",
                FIELDS["FILE_ID"]: new_file_id,
                FIELDS["CUSTOM_METADATA"]: custom_meta_str,
                FIELDS["CUSTOM_TAGS"]: custom_tags_str,
                # Indicate that the content of the new file comes from previous file
                FIELDS["CONTENT_CREATED_FROM_FILE_ID"]: current_meta.get(
                    FIELDS["FILE_ID"]
                ),
                # Explicitly tell the TDP that this file will not inherit labels
                # from the source or pipeline input file (RAW FILE ID)
                FIELDS["DO_NOT_INHERIT_LABELS"]: "true",
                # from pipeline context
                FIELDS["INTEGRATION_ID"]: getOrEmptyString(context, "pipelineId"),
                FIELDS["INTEGRATION_NAME"]: getOrEmptyString(
                    pipeline_config, "pipelineName"
                )[:254],
                FIELDS["PIPELINE_ID"]: getOrEmptyString(context, "pipelineId"),
                FIELDS["PIPELINE_WORKFLOW_ID"]: getOrEmptyString(context, "workflowId"),
                FIELDS["PIPELINE_MASTER_SCRIPT"]: (
                    f"{context.get('masterScriptNamespace', '')}/"
                    f"{context.get('masterScriptSlug', '')}:"
                    f"{context.get('masterScriptVersion', '')}"
                ),
                FIELDS["PIPELINE_TASK_EXECUTION_ID"]: getOrEmptyString(
                    context, "taskId"
                ),
                FIELDS["PIPELINE_TASK_SCRIPT"]: getOrEmptyString(context, "taskScript"),
                FIELDS["PIPELINE_TASK_SLUG"]: getOrEmptyString(context, "taskSlug"),
                FIELDS["PIPELINE_HISTORY"]: pipeline_history_str,
            },
            "MetadataDirective": "REPLACE",
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": head.get("SSEKMSKeyId", None),
        }

        params = {k: v for k, v in params.items() if v is not None}
        # fakeS3 does not return VersionId, so use '' to avoid an exception when we try to retrieve
        # from the head object or directly from the response object
        updated_version = ""

        # boto3.client.copy_object() has a maximum size of 5 GB. If the file exceeds this limit, we
        # have to use the boto3.copy() method that will do the multipart upload for us.
        file_size = head.get("ContentLength") or 0

        if file_size >= LARGE_FILE_SIZE_THRESHOLD_BYTES:
            print(
                {"level": "debug", "message": "updating the metadata of a 5+ GB file"}
            )
            extra_args = self.extract_extra_args_from_params(params)
            copy_source = {"Bucket": bucket, "Key": file_key}

            # unlike copy_object(), the copy() function does not return a response object. It will
            # raise an error instead. Additionally, we will have to make an additional request to
            # get the versionId if it exists
            try:
                self.s3.copy(
                    CopySource=copy_source,
                    Bucket=bucket,
                    Key=file_key,
                    ExtraArgs=extra_args,
                )
                updated_version = self.get_latest_obj_version(bucket, file_key)
            except Exception as exc:
                raise Exception(
                    f"encountered an error updating the metadata because of {exc}"
                ) from exc
        else:
            # For most cases when files are less than 5 GB in size. The versionId comes from the
            # response object of the copy_object() function
            response = self.s3.copy_object(**params)
            updated_version = response.get("VersionId", "")

        return {
            "type": "s3file",
            "bucket": bucket,
            "fileKey": file_key,
            "fileId": new_file_id,
            "version": updated_version,
        }

    def write_ids(
        self,
        context,
        content_obj: dict,
        file_suffix: str,
        raw_file,
        file_meta,
        ids: str,
        source_type: Optional[str],
        file_category: str,
        labels: Collection[AnyLabel],
        gzip_compress_level: int = 5,
    ) -> dict:
        """
        Write IDS to TDP using write_file.
        `content_obj` only accepts IDS content as a `dict`. This is required
        because `write_file` supports IDS validation only if the content
        passed to it is also a `dict`

        """
        ids_obj = VersionedRef(composite=ids)

        file_name = f"{ids_obj.namespace}-{ids_obj.name}-{file_suffix}"

        if not isinstance(content_obj, dict):
            raise TypeError(
                "'content_obj' passed to 'write_ids' must be of type 'dict'."
            )

        result = self.write_file(
            context,
            content_obj,
            file_name,
            file_category,
            raw_file,
            file_meta,
            ids,
            source_type,
            labels,
            gzip_compress_level,
        )
        return result

    def get_file_name(self, file: dict) -> str:
        """Get file basename from file metadata"""
        file_key = file["fileKey"]
        return os.path.basename(file_key)

    def get_presigned_url(self, file, ttl_sec):
        """Get Pre-signed URL from S3"""
        if ttl_sec is None or ttl_sec < 0 or ttl_sec > 900:
            raise Exception(
                "Cannot generate pre-signed S3 URL, expiration in seconds must be between 0 and "
                f"900, and specified value is {ttl_sec}"
            )

        kwargs = {"VersionId": file["version"]} if "version" in file else {}

        try:
            return self.s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": file["bucket"],
                    "Key": file["fileKey"],
                    **kwargs,
                },
                ExpiresIn=ttl_sec,
            )
        except Exception as exc:
            print(exc)

        return None

    def create_labels_file(
        self,
        target_file: dict,
        labels: Collection[AnyLabel],
        sse_kms_key_id: str = None,
    ):
        if sse_kms_key_id is None:
            try:
                head = self.get_s3_head(target_file)
                sse_kms_key_id = head.get("SSEKMSKeyId", "")
            except Exception as exc:
                print(exc)
                sse_kms_key_id = ""
        file_key = os.path.join(
            target_file["fileKey"], f'{target_file["fileId"]}.labels'
        )
        params = {
            "Bucket": target_file["bucket"],
            "Key": re.sub("/{2,}", "/", file_key)
            .replace("/RAW/", "/TMP/", 1)
            .replace("/IDS/", "/TMP/", 1)
            .replace("/PROCESSED/", "/TMP/", 1),
            "ContentType": "application/json",
        }
        if sse_kms_key_id != "":
            params["ServerSideEncryption"] = "aws:kms"
            params["SSEKMSKeyId"] = sse_kms_key_id
        else:
            params["ServerSideEncryption"] = "AES256"

        response = self.s3.put_object(
            Body=json.dumps(labels, cls=DataclassEncoder),
            **params,
        )
        print(
            {"level": "debug", "message": "labels file created", "response": response}
        )

    def extract_extra_args_from_params(self, params: dict) -> dict:
        """
        Return dictionary containing all arguments except Bucket, Key, CopySource

        These keys are already included in the copy() function signature.
        """
        return {
            k: v for k, v in params.items() if k not in ["Bucket", "Key", "CopySource"]
        }

    def get_latest_obj_version(self, bucket, file_key) -> str:
        """
        Get latest version of file_key in bucket

        We can't use s3.get_s3_head(file) because the file may have the old version before the copy
        command was called. So we need to make a direct call to head_object without the versionId
        to get the latest version of the file
        """
        try:
            new_head_obj = self.s3.head_object(Bucket=bucket, Key=file_key)
            return new_head_obj.get("VersionId", "")
        except Exception as exc:
            print(
                {
                    "level": "error",
                    "message": f"could not retrieve the latest version of the file because {exc}",
                }
            )
            return ""
