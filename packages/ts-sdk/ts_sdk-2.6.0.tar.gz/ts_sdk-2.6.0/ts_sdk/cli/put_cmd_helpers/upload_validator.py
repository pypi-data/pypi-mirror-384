from typing import List


def bytes_as_human_readable_string(num_bytes: float, decimals: int = 1) -> str:
    """Return the file size as a human-readable string."""
    for unit in ["", "Ki", "Mi", "Gi", "Ti"]:
        if abs(num_bytes) < 1024.0:
            return f"{round(num_bytes, ndigits=decimals):.{decimals}f} {unit}B"
        num_bytes /= 1024.0
    return f"{round(num_bytes, ndigits=decimals):.{decimals}f} YiB"


class UploadValidator:
    """
    Check whether given file(s) or other data may be uploaded to Tetra Data Platform.
    """

    def __init__(self, max_upload_size: int = 50 * 1024 * 1024) -> None:
        """
        :param max_upload_size:
            The maximum file size in bytes.
        """
        self.max_upload_size = max_upload_size

    def validate(self, upload_content: bytes) -> List[str]:
        """
        Check whether the provided data may be uploaded.

        :param upload_content:
            The data to be uploaded.
        :return:
            If the data is invalid, return a list containing the error message.
            Otherwise, return an empty list.
        """
        file_size = len(upload_content)
        if file_size > self.max_upload_size:
            friendly_file_size = bytes_as_human_readable_string(file_size)
            friendly_max_file_size = bytes_as_human_readable_string(
                self.max_upload_size
            )
            friendly_excess = bytes_as_human_readable_string(
                file_size - self.max_upload_size
            )
            return [
                f"File exceeded upload limit of ~{friendly_max_file_size} "
                f"by ~{friendly_excess}. Actual file size: {friendly_file_size}"
            ]

        return []
