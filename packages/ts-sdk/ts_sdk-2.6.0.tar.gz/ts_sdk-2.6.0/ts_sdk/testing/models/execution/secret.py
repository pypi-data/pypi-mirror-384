from typing import Optional

from ...util import random


class Secret:
    value: str
    ssm: str

    def __init__(self, *, value: Optional[str] = None):
        self.value = value or random.string()
        self.ssm = random.string()
