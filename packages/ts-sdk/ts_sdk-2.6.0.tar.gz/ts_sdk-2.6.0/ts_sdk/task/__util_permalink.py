from enum import Enum
from typing import Union


class ObjectType(Enum):
    FILE = "file"
    _DEBUG = "_debug"


short_names = {ObjectType.FILE: "fi"}


def remove_trailing_slash(url: str) -> str:
    return url.rstrip("/")


def to_object_type(value: str) -> ObjectType:
    object_type = next(
        (object_type for object_type in ObjectType if object_type.value == value), None
    )
    if object_type is None:
        raise ValueError(f"{value} is not a valid object type")
    else:
        return object_type


def ensure_object_type(value: Union[ObjectType, str]) -> ObjectType:
    if isinstance(value, ObjectType):
        return value
    elif isinstance(value, str):
        return to_object_type(value)
    else:
        raise ValueError("Object type must be either an ObjectType or a string")


def select_short_name(object_type: ObjectType) -> str:
    if object_type in short_names:
        return short_names[object_type]
    else:
        raise NotImplementedError(
            f"Permalink cannot be created for object of type {object_type.value}"
        )


def get_permalink(
    platform_api_url: str, object_type: Union[ObjectType, str], uuid: str
):
    if not isinstance(uuid, str):
        raise ValueError("UUID must be a string")
    if not isinstance(platform_api_url, str):
        raise ValueError("Platform API URL must be a string")
    api_url = remove_trailing_slash(platform_api_url)
    surely_object_type = ensure_object_type(object_type)
    short_name = select_short_name(surely_object_type)
    return f"{api_url}/o/{short_name}/{uuid}"
