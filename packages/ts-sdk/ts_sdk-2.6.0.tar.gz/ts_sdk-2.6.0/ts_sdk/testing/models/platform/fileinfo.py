import functools
import json
import re
from dataclasses import asdict
from typing import Optional
from urllib.parse import parse_qs, urlparse

from ...util.requests import replacing, responses
from ..auth import Auth
from ..execution import File, Label
from ..execution.datalake import get_by_id
from ..execution.file import RemoteFile

PATH_PREFIX = "/v1/fileinfo"


def get_org_slug_or_401(function):
    @functools.wraps(function)
    def applicator(original, url, headers, **kwargs):
        if org_slug := headers.get("x-org-slug"):
            return function(original, url, org_slug=org_slug, headers=headers, **kwargs)
        return responses.json(status_code=401)

    return applicator


def get_file_or_404(function):
    @functools.wraps(function)
    def applicator(original, url, org_slug, **kwargs):
        if file := find_file(url, org_slug):
            return function(original, url, file=file, **kwargs)
        return responses.json(status_code=404)

    return applicator


def find_file(url: str, org_slug: str) -> Optional[File]:
    if search := re.search(f"{PATH_PREFIX}/files/([^/]*)", url):
        file_id = search.group(1)
        file: Optional[File] = get_by_id(file_id)
        if not file and (auth := Auth.get_instance()):
            file = RemoteFile.pull(auth=auth, id=file_id)
        # file visibility is not prefix-based like artifacts
        # see https://github.com/tetrascience/ts-lambda-core/blob/99893124bb317d9fcef6fc2c76f9304c5dfbb55e/services/ts-core-fileinfo/src/models/file.ts#L29
        if file and file.org_slug == org_slug:
            return file
    return None


def labels_response(file: File):
    return responses.json(list(map(asdict, file.labels)))


def parse_query(url: str) -> list[str]:
    query = urlparse(url).query
    ids = parse_qs(query).get("id")
    if isinstance(ids, str):
        ids = [ids]
    return ids


@replacing("get", PATH_PREFIX)
@get_org_slug_or_401
@get_file_or_404
def get_file(original, url, file, **kwargs):
    if url.endswith("/labels"):
        return labels_response(file)
    return responses.json(
        {
            "type": "s3file",
            "fileId": file.id,
            "bucket": file.bucket,
            "fileKey": file.file_key,
            "version": file.version,
        }
    )


@replacing("post", PATH_PREFIX)
@get_org_slug_or_401
@get_file_or_404
def post_file(original, url, file, data, **kwargs):
    labels = json.loads(data)
    for label in labels:
        # TODO shouldn't be as simple as "append"
        #  see implementation: https://github.com/tetrascience/ts-lambda-core/blob/99893124bb317d9fcef6fc2c76f9304c5dfbb55e/services/ts-core-fileinfo/src/api/handlers/label/fileLabel.ts
        file.labels.append(Label(**label))
    return labels_response(file)


@replacing("delete", PATH_PREFIX)
@get_org_slug_or_401
@get_file_or_404
def delete_file(original, url, file, **kwargs):
    ids = parse_query(url)
    file.labels = list(filter(lambda label: label.id not in ids, file.labels))
    return labels_response(file)


replacements = [get_file, post_file, delete_file]
