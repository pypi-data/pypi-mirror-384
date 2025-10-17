from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .file import File

datalake: dict[str, "File"] = dict()
s3_versioned: dict[str, "File"] = dict()
s3_unversioned: dict[str, "File"] = dict()


def ingest(file: "File"):
    datalake[file.id] = file
    s3_versioned[f"{file.bucket}:{file.file_key}:{file.version}"] = file
    s3_unversioned[f"{file.bucket}:{file.file_key}"] = file


def delete(file: "File"):
    location_key = f"{file.bucket}:{file.file_key}"
    versioned_location_key = f"{file.bucket}:{file.file_key}:{file.version}"
    if file.id in datalake and datalake[file.id].version == file.version:
        del datalake[file.id]
    if (
        location_key in s3_unversioned
        and s3_unversioned[location_key].version == file.version
    ):
        del s3_unversioned[location_key]
    if versioned_location_key in s3_versioned:
        del s3_versioned[versioned_location_key]


def clear() -> None:
    datalake.clear()
    s3_versioned.clear()
    s3_unversioned.clear()


def get_by_id(id: str) -> Optional["File"]:
    return datalake.get(id, None)


def get_by_location(
    bucket: str, key: str, version: Optional[str] = None
) -> Optional["File"]:
    if version:
        return s3_versioned.get(f"{bucket}:{key}:{version}", None)
    return s3_unversioned.get(f"{bucket}:{key}", None)
