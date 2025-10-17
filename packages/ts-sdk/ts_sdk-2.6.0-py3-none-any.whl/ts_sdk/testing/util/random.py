from random import randrange
from typing import Callable
from uuid import uuid4

LIST_MAX_LENGTH = 10
VERSION_INT_MAX = 10


def string():
    return str(uuid4())


def namespace():
    return f"private-{string()}"


def version():
    return f"v{randrange(VERSION_INT_MAX)}.{randrange(VERSION_INT_MAX)}.{randrange(VERSION_INT_MAX)}"


def list_of(constructor: Callable[[], object]) -> object:
    return [constructor() for _ in range(randrange(LIST_MAX_LENGTH))]
