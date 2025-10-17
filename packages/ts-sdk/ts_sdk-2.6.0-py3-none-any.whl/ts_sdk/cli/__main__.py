from argparse import ArgumentParser

import colorama

from ts_sdk import __version__
from ts_sdk.task.__util_adapters.communication_format import (
    MAXIMUM_COMMUNICATION_FORMAT,
)

from .__init_cmd import init_cmd_args
from .__put_cmd import put_cmd_args
from .__utils import check_update_required


def main():
    colorama.init()

    parser = ArgumentParser(
        prog="ts-sdk",
        description="This cli is being deprecated May 1st, 2025. Try out the new cli: `pip3 install tetrascience-cli`",
    )

    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--max-supported-communication-format",
        action="version",
        version=MAXIMUM_COMMUNICATION_FORMAT.value,
        help="TDP communication format",
    )

    subparsers = parser.add_subparsers()

    init_cmd_args(
        subparsers.add_parser(
            "init", help="initialize master and task script from a template"
        )
    )

    put_cmd_args(
        subparsers.add_parser(
            "put", help="puts artifact identified by namespace/slug:version"
        )
    )

    args = parser.parse_args()

    check_update_required(__version__)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
