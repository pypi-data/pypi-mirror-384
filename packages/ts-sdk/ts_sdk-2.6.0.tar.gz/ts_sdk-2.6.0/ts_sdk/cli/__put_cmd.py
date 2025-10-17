import argparse
import io
import os
import re
import zipfile
from pathlib import Path
from time import sleep

import simplejson as json
from ids_validator.ids_validator import validate_ids_using_tdp_artifact
from ids_validator.tdp_api import APIConfig
from loguru import logger

from ts_sdk.cli.__api import TsApi
from ts_sdk.cli.__deprecated import deprecated
from ts_sdk.cli.__utils import zipdir
from ts_sdk.cli.put_cmd_helpers.upload_validator import (
    UploadValidator,
    bytes_as_human_readable_string,
)

DEFAULT_EXCLUDE_FOLDERS = [
    ".git",
    ".venv",
    "example-input",
    "example-output",
    "_tests_",
    "__tests__",
    "__test__",
    "example-files",
    "raw_data",
]


class ArtifactBuildError(Exception):
    """Raise when artifact build process fails"""


def put_cmd_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "type",
        type=str,
        choices=["ids", "protocol", "master-script", "task-script"],
        help="artifact type",
    )
    parser.add_argument("namespace", type=__namespace_type)
    parser.add_argument("slug", type=str.lower)
    parser.add_argument("version", type=__version_type)
    parser.add_argument(
        "folder", type=__folder_type, help="path to folder to be uploaded"
    )
    parser.add_argument(
        "--exclude-folders",
        action="store_true",
        default=True,
        help=f"Whether to exclude the following set of folders: {', '.join(DEFAULT_EXCLUDE_FOLDERS)}",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="force overwrite of an existing artifact",
    )
    parser.add_argument(
        "--ignore-ssl",
        "-i",
        action="store_true",
        help="ignore the SSL certificate verification",
    )

    parser.add_argument("--org", help="org slug", type=str)
    parser.add_argument("--api-url", help="platform API URL", type=str)
    parser.add_argument("--auth-token", help="authorization token", type=str)

    parser.add_argument(
        "--config",
        "-c",
        help="JSON file with configuration",
        type=argparse.FileType("r"),
    )

    parser.set_defaults(func=__cmd)


def __version_type(arg_value, pat=re.compile(r"^v")):
    if pat.match(arg_value):
        return arg_value
    return f"v{arg_value}"


def __folder_type(arg_value):
    if os.path.isdir(arg_value):
        return arg_value
    raise argparse.ArgumentTypeError("Not valid folder path provided!")


def __namespace_type(
    arg_value: str, ns_pattern=re.compile("^private-[0-9a-zA-Z-]+$")
) -> str:
    """
    Namespace validation function. Namespace must start with 'private-' and
    only contains alphanumeric characters and hyphens. A hyphen cannot
    succeed another hyphen. An exception is raised for invalid namespaces.

    Args:
        arg_value (str): namespace
        ns_pattern (re.Pattern): namespace validation regex.

     Returns:
         arg_value (str): validated namespace
    """

    # validate namespace
    if (
        not ns_pattern.match(arg_value)
        or arg_value.endswith("-")
        or re.search(r"--", arg_value)
    ):
        raise argparse.ArgumentTypeError(
            f"Invalid namespace {arg_value}. Namespace must start with "
            f"'private-' followed by alphanumeric characters or single "
            f"hyphens."
        )

    return arg_value


def __ensure_args(args: argparse.Namespace):
    # from config
    if getattr(args, "config", None):
        parsed_config = json.load(args.config)
        for k, v in parsed_config.items():
            if getattr(args, k, None) in [None, False]:
                setattr(args, k, v)
    else:
        # from env
        env_prefix = "TS_"
        for k, v in os.environ.items():
            if k.startswith(env_prefix):
                arg_key = k.replace(env_prefix, "").lower()
                if getattr(args, arg_key, None) in [None, False]:
                    setattr(args, arg_key, v)

    args.ignore_ssl = args.ignore_ssl in [True, "true", "True", "1"]


def __validate_ids(args, ts_api: TsApi, force: bool = False) -> None:
    """Run ts-ids-validator on the IDS artifact, raise an exception if it is invalid."""

    print("\n* Validating IDS")
    api_config = APIConfig.from_json_or_env(
        json_config=ts_api.opts,
        json_config_source="ts-sdk config",
    )
    # Validate IDS artifact.
    # API config is used to download the previous IDS for breaking change validation.
    ids_artifact_is_valid = validate_ids_using_tdp_artifact(
        Path(args.folder), api_config=api_config
    )
    if not ids_artifact_is_valid:
        if force:
            print("\n* IDS artifact validation failed, continuing due to 'force' flag.")
        else:
            raise ValueError(
                "IDS artifact validation with ts-ids-validator failed, see the output "
                "of the command for details."
            )


class PutCmdError(Exception):
    """Raised whenever the `ts-sdk put` command encounters an error."""


@deprecated
def __cmd(args):
    __ensure_args(args)
    print("Config:")
    keys_to_show = ["api_url", "org", "auth_token", "ignore_ssl"]
    config_to_show = {
        key_to_show: args.__dict__[key_to_show] for key_to_show in keys_to_show
    }
    if isinstance(config_to_show.get("auth_token"), str):
        config_to_show.update({"auth_token": f'{config_to_show["auth_token"][0:7]}...'})
    print(json.dumps(config_to_show, indent=4, sort_keys=True))

    ts_api = TsApi(**args.__dict__)

    if args.type == "ids":
        # Validate IDS schema.json using ts-ids-validator
        __validate_ids(args, ts_api=ts_api, force=args.force)

    if args.type == "task-script":
        # DE-3436: task-script folder must contain requirements.txt
        package_content = os.listdir(args.folder)
        if "requirements.txt" not in package_content:
            raise Exception("Task-Script package must contain 'requirements.txt'.")

    logger.info("Compressing...", flush=True)
    zip_buffer = io.BytesIO()
    zipf = zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False)
    exclude_folders = []
    if args.exclude_folders:
        exclude_folders = DEFAULT_EXCLUDE_FOLDERS
    zipdir(args.folder, zipf, exclude_folders)
    zipf.close()
    zip_bytes = zip_buffer.getvalue()

    upload_size_checker = UploadValidator()
    maybe_error_messages = upload_size_checker.validate(zip_bytes)
    if len(maybe_error_messages) > 0:
        raise PutCmdError(*maybe_error_messages)

    logger.info(f"Uploading {bytes_as_human_readable_string(len(zip_bytes))}...")

    r = ts_api.upload_artifact(args, zip_bytes)

    build_id = r.get("build", {}).get("id", None)
    if build_id:
        print("Build started", flush=True)
        print(
            "Note: A local script interruption doesn't stop a remote build!", flush=True
        )

        last_status = None
        prev_next_token = ""

        ARTIFACT_BUILD_ERROR_STR = "child process exited with code 1,"

        while True:
            build_info = ts_api.get_task_script_build_info(build_id)
            build_complete = build_info.get("build", {}).get("buildComplete")
            build_status = build_info.get("build", {}).get("buildStatus")

            sleep(3)

            logs_resp = ts_api.get_task_script_build_logs(
                build_id, {"nextToken": prev_next_token}
            )
            prev_next_token = logs_resp.get("nextToken", None)
            events = logs_resp.get("events", [])

            if len(events) > 0:
                print("\r", end="", flush=True)
            elif not build_complete:
                print(".", end="", flush=True)

            for event in events:
                msg_text = event.get("message", "").strip()
                if msg_text:
                    print(msg_text, flush=True)
                    if ARTIFACT_BUILD_ERROR_STR in msg_text:
                        raise ArtifactBuildError(
                            f"Artifact Build process failure:\n{msg_text}"
                        )

            if build_complete:
                last_status = build_status
                break

        print("", flush=True)

        # FAILED: The build failed.
        # FAULT: The build faulted.
        # STOPPED: The build stopped.
        # SUCCEEDED: The build succeeded.
        # TIMED_OUT: The build timed out.

        if last_status == "SUCCEEDED":
            print(
                json.dumps(
                    {
                        "type": args.type,
                        "namespace": args.namespace,
                        "slug": args.slug,
                        "version": args.version,
                    },
                    indent=4,
                    sort_keys=False,
                ),
                flush=True,
            )
        else:
            raise Exception("Build failed.")

    else:
        print(json.dumps(r, indent=4, sort_keys=True), flush=True)
