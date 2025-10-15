from typing import List, Iterator
from pydantic import Field, model_validator

from .category import Category
from ..common import CommonBase


class Categories(CommonBase):
    """Container for multiple category entries"""
    categories: List[Category] = Field(default_factory=list, alias="Category")

    def __iter__(self) -> Iterator[Category]:
        return iter(self.categories)

    @model_validator(mode='before')
    @classmethod
    def handle_category_list(cls, data):
        """Ensure Category is always a list"""
        if data and "Category" in data:
            if not isinstance(data["Category"], list):
                data["Category"] = [data["Category"]]
        return data
