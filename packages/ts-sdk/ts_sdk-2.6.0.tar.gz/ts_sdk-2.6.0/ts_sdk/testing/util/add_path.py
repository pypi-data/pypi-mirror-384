import os
import sys
from contextlib import contextmanager
from typing import Union


def _to_absolute_path(path: Union[str, os.PathLike]) -> str:
    path_string = os.fspath(path)
    return os.path.abspath(path_string)


@contextmanager
def add_path(path: Union[str, os.PathLike]):
    """Temporarily add a directory to sys.path."""
    absolute_path = _to_absolute_path(path)
    if absolute_path in sys.path:
        yield
    else:
        sys.path.append(absolute_path)
        try:
            yield
        finally:
            sys.path.remove(absolute_path)
