try:
    import yaml
    from pytest import MonkeyPatch
except ImportError:
    raise NotImplementedError(
        "Optional dependencies are not installed. Please install the 'testing' extra"
    )
