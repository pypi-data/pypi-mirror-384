import os
import shutil
from argparse import ArgumentParser
from pathlib import Path

from ts_sdk.cli.__deprecated import deprecated


def init_cmd_args(parser: ArgumentParser):
    parser.add_argument(
        "--protocol_slug", "-p", type=str, required=True, help="Slug of the protocol"
    )
    parser.add_argument(
        "--task_script_slug",
        "-t",
        type=str,
        required=True,
        help="Slug of the task script",
    )
    parser.add_argument(
        "--folder_path", "-f", type=str, required=True, help="Destination folder"
    )
    parser.add_argument(
        "--remove",
        "-r",
        action="store_true",
        help="Force removal/overwrite if folder already exists",
    )
    parser.add_argument(
        "--org",
        "-o",
        type=str,
        required=True,
        help="Org into which the scripts will be uploaded",
    )
    parser.add_argument(
        "--preserve_templates",
        type=bool,
        default=False,
        help="If true, leave template files on disk instead of deleting them",
    )
    parser.add_argument(
        "--protocol_schema",
        type=str,
        default="v3",
        required=False,
        choices=["v2", "v3"],
        help="If set to 'v2', uses legacy protocol template",
    )
    parser.set_defaults(func=__cmd)


def copy_from_root_to_root(src_root, dst_root):
    def copy(src_relative, dst_relative):
        src_path = os.path.join(src_root, src_relative)
        dst_path = os.path.join(dst_root, dst_relative)
        shutil.copytree(src_path, dst_path)

    return copy


@deprecated
def __cmd(args):
    # Remove folder if it exists
    new_folder_path = os.path.abspath(args.folder_path)
    new_folder = Path(new_folder_path)
    if new_folder.exists():
        print(f"{new_folder_path} already exists")
        if args.remove:
            shutil.rmtree(new_folder_path)
            print(f"{new_folder_path} removed")
        else:
            print(
                f"{new_folder_path} exists, do nothing. You can use --remove to remove/overwrite"
            )
            return
    copy_from_template_to_new_folder = copy_from_root_to_root(
        src_root=os.path.join(os.path.dirname(__file__), "protocol-template"),
        dst_root=new_folder_path,
    )
    copy_from_template_to_new_folder(
        src_relative="task-script", dst_relative="task-script"
    )
    copy_from_template_to_new_folder(
        src_relative=("protocol-v2" if args.protocol_schema == "v2" else "protocol"),
        dst_relative="protocol",
    )
    for p in Path(new_folder_path).glob("**/*.template"):
        text = p.read_text()
        text = text.replace("{{ org }}", args.org)
        text = text.replace("{{ protocol_slug }}", args.protocol_slug)
        text = text.replace("{{ task_script_slug }}", args.task_script_slug)

        dest = p.with_name(p.stem)
        print(f"Generating {dest}")
        dest.write_text(text)

        if not args.preserve_templates:
            print(f"Deleting {p}")
            p.unlink()
