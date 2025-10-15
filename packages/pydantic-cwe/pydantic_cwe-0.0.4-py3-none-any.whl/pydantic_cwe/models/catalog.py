from typing import Iterator, List
from pydantic import Field, BaseModel

from .weaknesses import Weaknesses, Weakness


class WeaknessCatalog(BaseModel):
    """The root CWE catalog model"""
    name: str = Field(..., alias="Name")
    version: str = Field(..., alias="Version")
    date: str = Field(..., alias="Date")
    weaknesses: Weaknesses = Field(..., alias="Weaknesses")
    # TODO: add the resto of the fields (Categories, Views, and External References);

    def __iter__(self) -> Iterator[Weakness]:
        return iter(self.weaknesses.weaknesses)

    def get_ordered_weaknesses(self) -> List[Weakness]:
        """Return an ordered list of weaknesses"""
        return sorted(self.weaknesses.weaknesses, key=lambda weakness: weakness.id)
