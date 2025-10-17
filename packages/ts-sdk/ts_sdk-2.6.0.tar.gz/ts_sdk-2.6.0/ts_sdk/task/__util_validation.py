import re
from typing import Any, Collection, List, Optional

from ts_sdk.task.data_model import AnyLabel, Label

meta_name_reg = re.compile(r"^[0-9a-zA-Z-_+ ]+$")
meta_value_reg = re.compile(r"^[0-9a-zA-Z-_+.,/ ]+$")
tag_reg = re.compile(r"^[0-9a-zA-Z-_+./ ]+$")
label_reg = re.compile(r"[^\uFFFE\uFFFF\n\r\\]+")
string_is_trimmed_reg = re.compile(r"^\S(.*\S)?$")

LABEL_NAME_MAX_CHARACTER_LIMIT = 128
LABEL_VALUE_MAX_CHARACTER_LIMIT = 256
TAG_MAX_CHAR_LIMIT = 128


def validate_file_meta(meta) -> bool:
    if meta is None:
        return True
    for key, value in meta.items():
        if not meta_name_reg.match(key):
            raise ValueError(
                f"Invalid metadata key {key}! Expected pattern: {meta_name_reg.pattern}"
            )
        if not meta_value_reg.match(str(value)):
            raise ValueError(
                f"Invalid metadata value {value}! Expected pattern: {meta_value_reg.pattern}"
            )
        validate_string_is_trimmed(key)
        validate_string_is_trimmed(value)
    return True


def validate_file_tags(tags: List[str]) -> bool:
    """
    Validate file tags as per https://developers.tetrascience.com/docs/basic-concepts-metadata-tags-and-labels
    """
    if tags is None:
        return True
    for tag in tags:
        if not isinstance(tag, str):
            raise TypeError(
                f"Invalid Tag. Expected type(tag) is str. Received type: {type(tag)}. Tag: {tag}"
            )
        if len(tag) > TAG_MAX_CHAR_LIMIT:
            raise ValueError(f"Tag length is greater that 128 chars. tag: {tag}")
        if not tag_reg.match(str(tag)):
            raise ValueError(f"Invalid tag {tag}! Expected pattern: {tag_reg.pattern}")
    return True


def cast_iterable(maybe_iterable, identifier) -> Collection:
    try:
        return iter(maybe_iterable)
    except TypeError:
        raise ValueError(
            f"{identifier} must be an iterable.  Given {type(maybe_iterable)}."
        )


def validate_not_none(maybe_none, identifier) -> bool:
    if maybe_none is None:
        raise ValueError(f"{identifier} should not be None.  Given None.")
    return True


def validate_not_empty(maybe_empty, identifier) -> bool:
    collection = cast_iterable(maybe_empty, identifier)
    if len(collection) == 0:
        raise ValueError(
            f"{identifier} must be a non-empty iterable of labels. Given an empty iterable."
        )
    return True


def validate_file_labels(labels: Optional[Collection[AnyLabel]]) -> bool:
    """
    Validates the list of labels given.
    List of labels must be made up of Label dictionaries
    """
    if labels is None or len(labels) == 0:
        return False

    # make sure the input is iterable
    labels_iter = cast_iterable(labels, "Labels")
    if labels_iter:
        valid_keys = {"name", "value"}
        errors = []
        for label in labels_iter:
            if not isinstance(label, (dict, Label)):
                errors.append(
                    f'Label must be a dictionary of the form {{"name": "foo", "value": "bar"}} or an instance of "ts_sdk.task.types.Label". Given: {label} ({type(label)})'
                )
                continue
            if isinstance(label, dict):
                # validate the shape of the dictionary
                label_keys = set(label.keys())
                if valid_keys - label_keys:
                    errors.append(
                        f"Label is missing required keys: {list(valid_keys - label_keys)}. Given: {label}"
                    )
                    continue

                if label_keys - valid_keys:
                    errors.append(
                        f"Label has extra keys: {list(label_keys - valid_keys)}. Given: {label}"
                    )
                    continue

                # validate the types of the inputs
                label_name = label["name"]
                label_value = label["value"]
            else:
                # no need to validate the shape of a dataclass
                label_name = label.name
                label_value = label.value

            if not isinstance(label_name, str):
                errors.append(
                    f'Invalid label name "{label_name}"! Must be a string. Given {type(label_name)}'
                )
                continue
            if not isinstance(label_value, str):
                errors.append(
                    f'Invalid label value "{label_value}"! Must be a string. Given {type(label_value)}'
                )
                continue

            # validate the characters used in the inputs
            if label_reg.fullmatch(label_name) is None:
                errors.append(
                    f'Invalid label name "{label_name}"! Expected pattern: "{label_reg.pattern}"'
                )
                continue
            if label_reg.fullmatch(label_value) is None:
                errors.append(
                    f'Invalid label value "{label_value}"! Expected pattern: "{label_reg.pattern}"'
                )
                continue

            # Validate character limits
            if len(label_name) > LABEL_NAME_MAX_CHARACTER_LIMIT:
                errors.append(
                    f"Invalid label_name length. Max limit is {LABEL_NAME_MAX_CHARACTER_LIMIT} characters"
                    f"label name: {label_name}"
                )
                continue

            if len(str(label_value)) > LABEL_VALUE_MAX_CHARACTER_LIMIT:
                errors.append(
                    f"Invalid label_value length. Max limit is {LABEL_VALUE_MAX_CHARACTER_LIMIT} characters"
                    f"label value: {label_value}"
                )
                continue
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Invalid label(s).  Errors:\n{error_msg}")
    return True


def validate_string_is_trimmed(value: Any) -> bool:
    """Validates that the given value has no leading or trailing whitespace

    If the given value is not a string, its `str()` representation is checked instead.
    """
    # Need to typecast non-string values to string in order to use the regex
    string_value = str(value)
    if not string_is_trimmed_reg.match(string_value):
        raise ValueError(f'Value "{value}" cannot contain leading or trailing spaces!')
    return True
