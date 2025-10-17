from dataclasses import dataclass, field

from ...util import random


@dataclass(init=False)
class Label:
    """
    Modelling of label is incomplete. In the real TDP, labels have an org slug, and have a (org,name) uniqueness property.
    In other words, it is normally not possible to have two labels, with the same (org,name), but different ID.
    We do not capture this in our mock
    """

    id: str
    name: str
    value: str

    def __init__(self, id: str = None, name: str = None, value: str = None, **_kwargs):
        """
        Custom constructor implemented to ignore excess values through kwargs.
        Sometimes we construct this object using tdp api responses, which may contain many excess fields
        :param id:
        :param name:
        :param value:
        :param _kwargs:
        """
        self.id = id or random.string()
        self.name = name or random.string()
        self.value = value or random.string()
