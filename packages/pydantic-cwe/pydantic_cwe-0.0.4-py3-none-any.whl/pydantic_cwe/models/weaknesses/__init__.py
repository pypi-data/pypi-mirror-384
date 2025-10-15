from typing import List
from pydantic import Field, model_validator

from .base import WeaknessBase
from .weakness import Weakness, RelatedWeakness


class Weaknesses(WeaknessBase):
    """Container for multiple weakness entries"""
    weaknesses: List[Weakness] = Field([], alias="Weakness")

    @model_validator(mode='before')
    @classmethod
    def handle_weakness_list(cls, data):
        """Ensure Weakness is always a list"""
        if data and "Weakness" in data:
            if not isinstance(data["Weakness"], list):
                data["Weakness"] = [data["Weakness"]]
        return data
