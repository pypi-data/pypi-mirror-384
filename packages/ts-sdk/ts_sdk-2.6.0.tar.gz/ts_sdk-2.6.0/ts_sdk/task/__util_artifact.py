import os
import re

import simplejson as json
from ids_validator.instance import validate_ids_instance

from ts_sdk.task import __util_ts_api as api
from ts_sdk.task.__util_adapters import CommunicationFormat
from ts_sdk.task.__util_adapters.communication_format import get_communication_format

from . import s3_client
from .data_model import ArtifactUtilDict


def create_artifact_util(locations) -> ArtifactUtilDict:
    def get_location(namespace):
        for location in locations:
            if re.search(location["namespacePattern"], namespace):
                return location
        raise Exception(f"Invalid namespace: {namespace}")

    def get_artifact_file_from_s3(
        namespace: str, slug: str, version: str, artifact_type: str
    ) -> dict:
        """Download and parse a JSON file from an S3-backed artifact storage.

        This function resolves the S3 location for the given artifact, builds the
        full S3 object key, downloads the file using a s3 client, and returns the
        parsed JSON content.
        (It keeps the original implementation logic from the previous API-based
        function but now reads the file directly from S3.)

        Args:
            namespace (str): Artifact namespace (e.g., tenant or organization).
            slug (str): Unique slug identifying the artifact.
            version (str): Version of the artifact (e.g., "1.0.0").
            artifact_type (str): Type/category of the artifact (e.g., "ids", "schemas").

        Returns:
            dict: The parsed JSON content of the downloaded artifact file.
        """
        location = get_location(namespace)
        bucket = location["bucket"]
        prefix = location["prefix"]
        endpoint = location["endpoint"]
        if endpoint:
            s3 = s3_client.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id="123",
                aws_secret_access_key="abc",
            )
        else:
            s3 = s3_client.client("s3")

        file_key = os.path.join(
            prefix, artifact_type, namespace, slug, version, "schema.json"
        )
        print(f"downloading {artifact_type.upper()}, {bucket}, {file_key}")
        try:
            read_response = s3.get_object(Bucket=bucket, Key=file_key)
            status_code = read_response.get("ResponseMetadata", {}).get(
                "HTTPStatusCode"
            )
            body = read_response.get("Body").read().decode("utf-8")
            return json.loads(body)
        except Exception as exc:
            raise Exception(
                f"Failed to get {artifact_type.upper()}, {namespace}/{slug}:{version} from bucket: {bucket}, "
                f"file_key: {file_key}."
            ) from exc

    def get_artifact_file_from_api(
        namespace: str, slug: str, version: str, artifact_type: str
    ) -> dict:
        """Fetch a file from an artifact stored in the ArMS API.

        Args:
            namespace (str): Artifact namespace (e.g., tenant or organization).
            slug (str): Unique slug identifying the artifact.
            version (str): Version of the artifact (e.g., "1.0.0").
            artifact_type (str): Type/category of the artifact (e.g., "ids", "schemas").

        Returns:
            dict: Parsed JSON content of the requested artifact file.
        """
        route = (
            f"v1/artifacts/{artifact_type}/{namespace}/{slug}/{version}/files/schema"
        )
        print(f"Fetching artifact file from ArMS: '{route}'...")
        response = api.get(route)
        response.raise_for_status()
        file = response.json()
        print(
            f"Successfully retrieved file 'schema.json' from artifact '{artifact_type}'"
        )
        return file

    def get_artifact_file(namespace, slug, version, artifact_type: str):
        """Retrieve a file from an artifact stored either in ArMS or S3 depending on the
        communication format.

        Args:
            namespace (str): Artifact namespace (e.g., tenant or org).
            slug (str): Unique slug of the artifact.
            version (str): Artifact version (e.g., "0.1.0").
            artifact_type (str): Type of artifact (e.g., "ids", "schemas").

        Returns:
            dict: Parsed JSON content of the requested file.
        """
        communication_format = get_communication_format()
        if communication_format == CommunicationFormat.V0:
            return get_artifact_file_from_s3(namespace, slug, version, artifact_type)

        return get_artifact_file_from_api(namespace, slug, version, artifact_type)

    def get_ids(namespace: str, slug: str, version: str) -> dict:
        """Retrieve an `ids` artifact file from ArMS.

        Args:
            namespace (str): Artifact namespace.
            slug (str): Unique slug of the artifact.
            version (str): Artifact version.

        Returns:
            dict: Parsed JSON content of the `ids` artifact file.
        """
        body = get_artifact_file(namespace, slug, version, "ids")
        return body

    def get_schema_artifact(namespace: str, slug: str, version: str) -> dict:
        """Retrieve a `schema` artifact file from ArMS.

        Args:
            namespace (str): Artifact namespace.
            slug (str): Unique slug of the artifact.
            version (str): Artifact version.

        Returns:
            dict: Parsed JSON content of the `schema` artifact file.
        """
        body = get_artifact_file(namespace, slug, version, "schemas")
        return body

    def validate_ids(data, namespace, slug, version):
        ids = get_ids(namespace, slug, version)
        validate_ids_instance(data, ids)

    return {
        "get_ids": get_ids,
        "get_schema_artifact": get_schema_artifact,
        "validate_ids": validate_ids,
    }
