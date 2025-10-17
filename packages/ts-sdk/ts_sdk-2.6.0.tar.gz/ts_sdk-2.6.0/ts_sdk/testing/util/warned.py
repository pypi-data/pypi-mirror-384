import functools


def warned(message: str):

    def decorator(function):
        @functools.wraps(function)
        def applicator(*args, **kwargs):
            print(f"warning: {message}")
            return function(*args, **kwargs)

        return applicator

    return decorator
