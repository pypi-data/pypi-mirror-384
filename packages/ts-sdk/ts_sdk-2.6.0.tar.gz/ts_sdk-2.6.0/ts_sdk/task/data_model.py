import io
import typing as t
from dataclasses import dataclass
from typing import IO

import typing_extensions as te

FileCategory = te.Literal["IDS", "RAW", "PROCESSED", "TMP"]


class File(te.TypedDict, total=False):
    type: te.Literal["s3file"]
    bucket: str
    fileKey: str
    fileId: str
    version: t.Optional[str]


class ReadResult(te.TypedDict):
    metadata: t.Mapping[str, str]
    body: t.Optional[bytes]
    file_obj: t.Optional[io.BufferedIOBase]
    download: t.Optional[str]
    custom_metadata: t.Mapping[str, str]
    custom_tags: t.List[str]


ContextType = t.Union[IO, str, t.Dict[str, t.Any]]


class ArtifactUtilDict(te.TypedDict):
    """
    A dictionary containing utility functions for IDS and generic schema artifact retrieval and validation,
    as created in __util_artifact.py. Includes functions for getting IDS, getting schema artifacts, and validating IDS.
    """

    get_ids: t.Callable[[str, str, str], t.Dict[str, t.Any]]
    get_schema_artifact: t.Callable[[str, str, str], t.Dict[str, t.Any]]
    # fmt: off
    validate_ids: t.Callable[[ContextType, t.Optional[str], t.Optional[str], t.Optional[str]], None]
    # fmt: on


class LabelDict(te.TypedDict, total=False):
    """
    The dictionary representation of a "label" on a file in TDP.
    It represents a `key: value` pair where key is stored in `Label.name` and value is stored in `Label.value`

    `Label.name` has a maximum limit of 128 characters
    `Label.value` has maximum limit of 256 characters

    For further info, see
    https://developers.tetrascience.com/docs/basic-concepts-metadata-tags-and-labels
    """

    name: str
    value: str


@dataclass
class Label:
    """The class representation of a "label" on a file in TDP.

    It represents a `key: value` pair where key is stored in `Label.name` and value is stored in `Label.value`

    `Label.name` has a maximum limit of 128 characters
    `Label.value` has maximum limit of 256 characters

    For further info, see
    https://developers.tetrascience.com/docs/basic-concepts-metadata-tags-and-labels
    """

    name: str
    value: str


AnyLabel = t.Union[Label, LabelDict]
