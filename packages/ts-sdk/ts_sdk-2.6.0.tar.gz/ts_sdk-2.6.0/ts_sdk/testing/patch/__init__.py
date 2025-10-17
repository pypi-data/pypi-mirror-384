from unittest.mock import patch


def unsafe(method_name: str):
    """
    Escape hatch patching -- user can patch any method or property of Context
    :param method_name:
    :return:
    """
    return patch(f"ts_sdk.task.__task_script_runner.Context.{method_name}")
