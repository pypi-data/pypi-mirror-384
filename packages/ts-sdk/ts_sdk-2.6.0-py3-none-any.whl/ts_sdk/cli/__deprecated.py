import functools

from colorama import Fore

MESSAGE = """
This cli is being deprecated,
and will no longer be supported starting July 31st, 2025.
Migrate to the new TetraScience cli by running
pip3 install tetrascience-cli
"""


def deprecated(func):
    @functools.wraps(func)
    def deprecated_func(*args, **kwargs):
        print(f"{Fore.YELLOW}{MESSAGE}{Fore.RESET}")
        return func(*args, **kwargs)

    return deprecated_func
