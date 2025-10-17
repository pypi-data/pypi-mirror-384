import json
import pathlib
import re
import typing as t


class MissingAllowedIDS:
    pass


MISSING_ALLOWED_IDS = MissingAllowedIDS()


class IDSNotAllowed(Exception):
    pass


class IDSInvalidWrite(Exception):
    pass


class IDSValidateWrongParams(Exception):
    pass


class NoAllowedIdsSpecified(Exception):
    pass


class InvalidIDSString(ValueError):
    pass


class IDS:
    """Abstraction for IDS Name"""

    def __init__(self, namespace: str, slug: str, version: str):
        self.namespace = namespace
        self.slug = slug
        self.version = version

    @classmethod
    def from_dict(cls, ids_dict: dict):
        return cls(ids_dict["namespace"], ids_dict["slug"], ids_dict["version"])

    @classmethod
    def from_str(cls, ids_str: str):
        regex = re.compile(r"(.*)/(.*):(.*)")
        match_result = regex.match(ids_str)
        if match_result is None:
            raise InvalidIDSString(
                f"Received invalid IDS string: '{ids_str}'. IDS strings are expected to have format "
                f"<namespace>/<slug>:<version>."
            )
        namespace, slug, version = match_result.groups()
        return IDS(namespace=namespace, slug=slug, version=version)

    def to_tuple(self):
        return self.namespace, self.slug, self.version

    def __str__(self):
        return f"{self.namespace}/{self.slug}:{self.version}"

    def __repr__(self):
        return (
            f"IDS(namespace={self.namespace}, slug={self.slug}, version={self.version})"
        )

    def __eq__(self, item):
        return str(item) == str(self)

    def __hash__(self):
        return hash(str(self))

    def __bool__(self) -> bool:
        if self.namespace and self.slug and self.version:
            return True
        else:
            return False


class AllowedIDS:
    """Abstraction for 'allowedIds' JSON object"""

    allowed_ids: t.Iterable[IDS]

    def __init__(self, allowed_ids: t.Optional[t.Union[IDS, t.Iterable[IDS]]]):
        if isinstance(allowed_ids, IDS):
            self.allowed_ids = [allowed_ids]
        else:
            self.allowed_ids = allowed_ids

    @classmethod
    def from_allowedIds(cls, allowed_ids: t.Union[dict, t.List[dict], None]):
        """
        Read config.json to get the value of 'allowedIds'
        if 'allowedIds' is null, return None
        else return list of IDS object
        """

        if isinstance(allowed_ids, dict):
            return cls(IDS.from_dict(allowed_ids))
        elif isinstance(allowed_ids, list):
            allowed_ids = [IDS.from_dict(ids) for ids in allowed_ids]
            allowed_ids = list(set(allowed_ids))
            return cls(allowed_ids)
        elif allowed_ids is None:
            return cls(allowed_ids)
        else:
            raise ValueError(
                "'allowedIds' for function config (in config.json) must be one of the following: \n"
                "1. JSON object representing IDS\n"
                "2. List of JSON objects, each representing IDS\n"
                "3. null\n"
            )

    def is_single(self):
        return len(self.allowed_ids) == 1

    def get_first(self):
        return self.allowed_ids[0]

    def is_reconcilable(self, ids_requested_to_be_written: t.Optional[str]) -> bool:
        if not self.allowed_ids:
            raise IDSInvalidWrite(
                "Task Script is not allowed to write or validate IDS.\n"
                "Please make sure 'allowedIds' for function config (in config.json) is one of the following: \n"
                "1. JSON object representing IDS\n"
                "2. List of JSON objects, each representing IDS\n"
            )

        if ids_requested_to_be_written:
            ids_obj = IDS.from_str(ids_requested_to_be_written)
            if ids_obj not in self.allowed_ids:
                raise IDSNotAllowed(
                    f"Task Script is trying to write IDS for {ids_obj}."
                    f"However, only following IDS are allowed {self.allowed_ids}"
                )
        else:
            if len(self.allowed_ids) > 1:
                raise IDSInvalidWrite(
                    f"Could not determine which IDS to use. \n"
                    f"'ids_requested_to_be_written' is set to None."
                    f"And multiple IDS are allowed : {self.allowed_ids}"
                )
        return True

    def get_ids_to_be_written(
        self, ids_requested_to_be_written: t.Optional[str]
    ) -> t.Optional[str]:
        """
        'ids_requested_to_be_written' is safe to use if it is present in 'allowedIds'.
        If 'ids_requested_to_be_written' is None, then safely determine which IDS should the
        task-script write.
        """
        if self.is_reconcilable(ids_requested_to_be_written):
            if not ids_requested_to_be_written:
                return (
                    str(self.allowed_ids[0])
                    if isinstance(self.allowed_ids, list)
                    else str(self.allowed_ids)
                )
            return ids_requested_to_be_written

    def __eq__(self, other) -> bool:
        if isinstance(other, MissingAllowedIDS):
            return False
        return str(self.allowed_ids) == str(other.allowed_ids)


class FunctionConfig:
    """Abstraction for function configuration in config.json"""

    def __init__(self, config_dict: dict = {}):
        self._config_dict = config_dict
        self.allowed_ids = self._get_allowed_ids()

    def _get_allowed_ids(self) -> t.Union[AllowedIDS, MissingAllowedIDS]:
        if "allowedIds" not in self._config_dict:
            return MISSING_ALLOWED_IDS
        else:
            allowed_ids = self._config_dict["allowedIds"]
            return AllowedIDS.from_allowedIds(allowed_ids)

    @classmethod
    def from_task_script_config(
        cls, task_script_config: dict, func_slug: str
    ) -> "FunctionConfig":
        """
        Given task_script_config and func_slug, return FunctionConfig object
        """
        if not task_script_config:
            return cls({})

        functions = task_script_config.get("functions", [])
        fx_config = [fx for fx in functions if fx.get("slug") == func_slug]
        fx_config = fx_config[0] if fx_config else {}
        return cls(fx_config)

    @classmethod
    def from_task_script_dir(cls, func_dir: str, func_slug: str) -> "FunctionConfig":
        """Read function's configuration from task-script's config.json

        Args:
            func_dir (str): path of the directory containing task-script
            func_slug (str): Slug for the function being called

        Returns:
            FunctionConfig object
        """
        config_file = pathlib.Path(func_dir) / "config.json"

        if not config_file.exists():
            return cls.from_task_script_config({}, func_slug)

        with open(config_file, "r") as config:
            config_dict = json.load(config)
            return cls.from_task_script_config(config_dict, func_slug)
