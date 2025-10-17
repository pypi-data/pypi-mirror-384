import functools
import threading
from typing import Optional, Type, TypeVar

from ..exceptions import SetupException

T = TypeVar("T")


class ContextSingletonProtocol:
    """
    Used just for type-hinting
    """

    @classmethod
    def get_instance(cls: Type[T]) -> Optional[T]: ...
    @classmethod
    def get_instance_or(cls: Type[T], *args, **kwargs) -> T: ...
    def __enter__(self: T) -> T: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
    def __call__(self, function: T) -> T: ...


def context_singleton(cls: Type[T]) -> Type[T]:

    _storage = threading.local()
    _storage.instance = None

    def get_instance(cls: Type[T]) -> Optional[T]:
        return _storage.instance

    def get_instance_or(cls: Type[T], *args, **kwargs) -> T:
        return cls.get_instance() or cls(*args, **kwargs)

    def __enter__(self: T) -> T:
        if _storage.instance:
            raise SetupException(
                f"Cannot use more than one instance of class {type(self)}"
            )
        _storage.instance = self
        return self

    def __exit__(self: T, exc_type, exc_val, exc_tb):
        if not _storage.instance:
            raise SetupException(f"Cannot exit unused instance {self}")
        _storage.instance = None

    def __call__(self: T, function):
        @functools.wraps(function)
        def applicator(*args, **kwargs):
            with self:
                return function(*args, **kwargs)

        return applicator

    cls.get_instance = classmethod(get_instance)
    cls.get_instance_or = classmethod(get_instance_or)
    cls.__enter__ = __enter__
    cls.__exit__ = __exit__
    cls.__call__ = __call__

    return cls
