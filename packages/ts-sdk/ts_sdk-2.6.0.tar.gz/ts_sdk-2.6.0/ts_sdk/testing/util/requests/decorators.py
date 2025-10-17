from typing import Callable, cast

from .endpoint_replacement import (
    Method,
    OriginalImplementation,
    Replacement,
    ReplacementImplementation,
    Response,
    SideCondition,
)


def replacing(
    method: Method, path_prefix: str, side_condition: SideCondition = "always"
) -> Callable[[ReplacementImplementation], Replacement]:
    def decorator(function: ReplacementImplementation) -> Replacement:
        return Replacement(
            method=method,
            path_prefix=path_prefix,
            implementation=function,
            side_condition=side_condition,
        )

    return decorator


def before(
    method: Method, path_prefix: str, side_condition: SideCondition = "always"
) -> Callable[[Callable], Replacement]:
    def decorator(function) -> Replacement:
        def implementation(
            original: OriginalImplementation, url: str, **kwargs: object
        ):
            new_url, new_kwargs = function(url, **kwargs)
            return original(new_url, **new_kwargs)

        return Replacement(
            method=method,
            path_prefix=path_prefix,
            implementation=cast(ReplacementImplementation, implementation),
            side_condition=side_condition,
        )

    return decorator


def after(
    method: Method, path_prefix: str, side_condition: SideCondition = "always"
) -> Callable[[Callable], Replacement]:
    def decorator(function: Callable[[Response], Response]) -> Replacement:
        def implementation(
            original: OriginalImplementation, url: str, **kwargs: object
        ) -> Response:
            response = original(url, **kwargs)
            return function(response)

        return Replacement(
            method=method,
            path_prefix=path_prefix,
            implementation=cast(ReplacementImplementation, implementation),
            side_condition=side_condition,
        )

    return decorator
