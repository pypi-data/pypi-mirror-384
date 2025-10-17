from dataclasses import asdict, is_dataclass

from simplejson import JSONEncoder


class DataclassEncoder(JSONEncoder):
    """Custom json encoder to allow dataclasses to be encoded as JSON objects

    For more about the encoder, see https://docs.python.org/3.7/library/json.html#json.JSONEncode
    """

    def default(self, o):
        """Override the encoding function to allow dataclasses to be encoded.

        For more about dataclass functions, see: https://docs.python.org/3.7/library/dataclasses.html#dataclasses.is_dataclass
        """
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        return super().default(o)
