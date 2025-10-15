from pydantic import Field, BaseModel
from typing import Iterator, List, Dict

from .categories import Categories, Category
from .weaknesses import Weaknesses, Weakness


class Catalog(BaseModel):
    """The root CWE catalog model"""
    name: str = Field(..., alias="Name")
    version: str = Field(..., alias="Version")
    date: str = Field(..., alias="Date")
    weaknesses: Weaknesses = Field(..., alias="Weaknesses")
    categories: Categories = Field(..., alias="Categories")
    # TODO: add the resto of the fields (Views, and External References);

    def __iter__(self) -> Iterator[Weakness]:
        return iter(self.weaknesses.weaknesses)

    def get_ordered_weaknesses(self) -> List[Weakness]:
        """Return an ordered list of weaknesses"""
        return sorted(self.weaknesses.weaknesses, key=lambda weakness: weakness.id)

    def get_ordered_categories(self) -> List[Category]:
        """Return an ordered list of categories"""
        return sorted(self.categories.categories, key=lambda category: category.id)

    def get_weakness_memberships(self) -> Dict[int, set]:
        _memberships = {}

        for category in self.categories:
            for weakness in category.get_weakness_ids():
                if weakness not in _memberships:
                    _memberships[weakness] = set()

                _memberships[weakness].add(category.id)

        return _memberships
