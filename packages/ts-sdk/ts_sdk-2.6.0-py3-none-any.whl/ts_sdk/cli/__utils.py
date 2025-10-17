import os
import pathlib
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Iterable, Optional, Union

import requests
from colorama import Fore


def get_latest_version():
    try:
        r = requests.get("https://pypi.org/rss/project/ts-sdk/releases.xml", timeout=5)
        root = ET.fromstring(r.content)
        return root.findall("channel/item/title")[0].text
    except:
        return "0.0.0"


def check_update_required(current_version):
    try:
        latest_version_path = Path.home() / ".ts-sdk.latest"
        latest_version = "0.0.0"

        # refresh saved latest version once per day
        if (
            latest_version_path.is_file()
            and time.time() - latest_version_path.stat().st_mtime < 24 * 3600
        ):
            latest_version = latest_version_path.read_text()
        else:
            latest_version = get_latest_version()
            latest_version_path.write_text(latest_version)

        if latest_version and check_versions_for_update(
            current_version, latest_version
        ):
            print(
                f"\n{Fore.YELLOW}Please upgrade ts-sdk (local: {current_version}, latest: {latest_version}){Fore.RESET}"
            )
            print(f"{Fore.YELLOW}Use: pip3 install ts-sdk --upgrade{Fore.RESET}\n")

    except Exception as ex:
        # print(ex)
        pass


def check_versions_for_update(current: str, latest: str):
    current_major, current_minor, *rest = current.split(".")
    latest_major, latest_minor, *rest = latest.split(".")
    if int(current_major) < int(latest_major):
        return True
    if int(current_minor) < int(latest_minor):
        return True
    return False


def zipdir(
    path: Union[str, pathlib.Path],
    zip_archive: zipfile.ZipFile,
    folders_to_exclude: Optional[Iterable[str]] = None,
) -> None:
    if folders_to_exclude is None:
        folders_to_exclude = set()
    folders_to_exclude = set(folders_to_exclude)
    for root, folders, files in os.walk(path, topdown=True):
        actually_excluded_folders = set(folders).intersection(folders_to_exclude)
        for folder in actually_excluded_folders:
            folders.remove(folder)
        for file in files:
            local_path = os.path.join(root, file)
            zip_path = os.path.relpath(os.path.join(root, file), os.path.join(path))
            zip_archive.write(local_path, zip_path)
