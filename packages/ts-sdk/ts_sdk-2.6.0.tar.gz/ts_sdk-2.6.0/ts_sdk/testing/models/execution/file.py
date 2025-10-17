import gzip
import os
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional, Union

import requests
from typing_extensions import Literal

from ts_sdk.task import FileCategory

from ...exceptions import SetupException
from ...util import random
from .. import Auth
from .datalake import ingest
from .label import Label


@dataclass(kw_only=True)
class File(ABC):
    bucket: str = field(default_factory=random.string)
    source_id: str = field(default_factory=random.string)
    id: str = field(default_factory=random.string)
    labels: List[Label] = field(default_factory=lambda: random.list_of(Label))
    tags: List[str] = field(default_factory=lambda: random.list_of(random.string))
    version: str = field(default_factory=random.string)
    org_slug: str = field(default_factory=random.string)
    content_encoding: Optional[Literal["gzip"]] = field(default=None)
    category: FileCategory = field(default="RAW")
    name: str = field(default_factory=random.string)
    metadata: dict = field(default_factory=dict)

    @property
    def file_key(self) -> str:
        return f"{self.org_slug}/{self.source_id}/{self.category}/{self.name}"

    def __post_init__(self):
        ingest(self)

    def __hash__(self):
        return hash((self.bucket, self.file_key, self.id))

    def to_file_pointer(self):
        return {
            "bucket": self.bucket,
            "fileKey": self.file_key,
            "fileId": self.id,
            "version": self.version,
        }

    @abstractmethod
    def _create_temp_file(self) -> NamedTemporaryFile: ...

    @cached_property
    def _temp_file(self) -> NamedTemporaryFile:
        return self._create_temp_file()

    def reader(self):
        self._temp_file.seek(0)
        return self._temp_file

    def __str__(self) -> str:
        contents = self.reader().read()
        if self.content_encoding == "gzip":
            contents = gzip.decompress(contents)
        if isinstance(contents, bytes):
            return contents.decode("utf-8")
        return str(contents)

    def uri(self):
        return f"file://{self._temp_file.name}"


@dataclass(kw_only=True)
class InlineFile(File):
    contents: Union[str, bytes] = field(default_factory=random.string)

    def _create_temp_file(self) -> NamedTemporaryFile:
        mode = "wb+" if isinstance(self.contents, bytes) else "w+"
        temporary_file = NamedTemporaryFile(delete=True, mode=mode)
        temporary_file.write(self.contents)
        return temporary_file


@dataclass(kw_only=True)
class LocalFile(File):

    path: Union[str, Path]

    def __post_init__(self):
        if not os.path.isfile(self.path):
            raise SetupException("Provided path does not exist")
        super().__post_init__()

    def _create_temp_file(self) -> NamedTemporaryFile:
        temporary_file = NamedTemporaryFile(delete=True, mode="w+")
        shutil.copy2(self.path, temporary_file.name)
        return temporary_file


@dataclass(kw_only=True)
class RemoteFile(File):
    @staticmethod
    def pull(auth: Auth, id: str) -> Optional["RemoteFile"]:
        try:
            return RemoteFile(auth=auth, id=id)
        except SetupException:
            return None

    def __init__(self, *, id: str, auth: Auth = None):
        self.auth = auth or Auth.get_instance()
        if not self.auth:
            raise SetupException(f"No auth provided. Cannot reach remote file {id}")
        response = self.get(f"/fileinfo/file/{id}")
        if not (response.status_code == 200):
            raise SetupException(
                f"Cannot reach remote file {id}. Error: {response.text}"
            )
        remote_file = response.json()
        self.id = id
        self.category = remote_file.get("category")
        self.source_id = remote_file.get("source").get("id")
        self.name = remote_file.get("file").get("tsEncodedPath")
        self.bucket = remote_file.get("file").get("bucket")
        self.version = remote_file.get("file").get("version")
        self.org_slug = remote_file.get("orgSlug")
        self.labels = [Label(**label) for label in remote_file.get("labels")]
        self.tags = remote_file.get("tags")
        self.content_encoding = remote_file.get("file").get("s3ContentEncoding", None)
        self.metadata = remote_file.get("metadata")
        ingest(self)

    def get(self, url: str):
        return requests.get(
            f"{self.auth.api_url}{url}",
            headers={
                "Content-Type": "application/json",
                "x-org-slug": self.auth.org,
                "ts-auth-token": self.auth.auth_token,
            },
        )

    def _create_temp_file(self) -> NamedTemporaryFile:
        temporary_file = NamedTemporaryFile(delete=True, mode="wb+")
        response = self.get(f"/datalake/retrieve?fileId={self.id}&getPresigned=false")
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temporary_file.write(chunk)
        temporary_file.flush()
        return temporary_file
