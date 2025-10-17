import functools


def deprecated(message):
    def deprecated_decorator(func):
        @functools.wraps(func)
        def deprecated_func(*args, **kwargs):
            print(
                {
                    "level": "warn",
                    "message": message,
                }
            )
            return func(*args, **kwargs)

        return deprecated_func

    return deprecated_decorator


def return_on_failure(errors=(Exception,), default_value=None):
    def decorator(func):
        @functools.wraps(func)
        def applicator(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors:
                return default_value

        return applicator

    return decorator


def raise_on_failure(errors=(Exception,), exception=Exception):
    def decorator(func):
        @functools.wraps(func)
        def applicator(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors:
                raise exception

        return applicator

    return decorator


def cached(function):
    """
    Decorates a function such that is only executes a single time
    The return value is cached and returned for every future invocation
    IMPORTANT: Will not re-execute even if arguments change
    :param function: the method to be decorated
    :return: a function with the same signature as the provided function
    """
    result = None

    @functools.wraps(function)
    def applicator(*args, **kwargs):
        nonlocal result
        if kwargs.get("force"):
            result = None
            kwargs.pop("force")
        if result is None:
            result = function(*args, **kwargs)
        return result

    return applicator


def predicated_on(predicate, message):
    def decorator(function):
        @functools.wraps(function)
        def applicator(*args, **kwargs):
            if predicate(*args, **kwargs) is False:
                raise ValueError(message)
            return function(*args, **kwargs)

        return applicator

    return decorator
