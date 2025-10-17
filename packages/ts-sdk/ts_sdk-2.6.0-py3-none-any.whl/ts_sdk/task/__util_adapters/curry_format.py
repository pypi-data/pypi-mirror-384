from functools import partial


def curry_for_each_method(format_implementation: dict, *args, **kwargs):
    """
    A _very_ naive implementation of currying, for each callable value inside a dict
    Created to support the common use of currying URLs for API adapters
    Only curries to level callables -- does not recur down a dict tree
    :param format_implementation: The dict that may contain callables
    :param args:
    :param kwargs:
    :return: the dict containing curried functions
    """
    return {
        key: partial(value, *args, **kwargs) if callable(value) else value
        for key, value in format_implementation.items()
    }
