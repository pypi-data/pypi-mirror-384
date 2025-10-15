from typing import List
from pydantic import Field, model_validator
from ..common import CommonBase
from .category import Category


class Categories(CommonBase):
    """Container for multiple category entries"""
    categories: List[Category] = Field(default_factory=list, alias="Category")

    @model_validator(mode='before')
    @classmethod
    def handle_category_list(cls, data):
        """Ensure Category is always a list"""
        if data and "Category" in data:
            if not isinstance(data["Category"], list):
                data["Category"] = [data["Category"]]
        return data
