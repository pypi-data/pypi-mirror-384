"""
pydantic-cwe - A Pythonic representation of CWE records using Pydantic models.

This package provides a structured, object-oriented way to work with the 
Common Weakness Enumeration (CWE) database using Pydantic models.
"""

from pydantic_cwe.loader import Loader
from pydantic_cwe.models import (
    CommonBase,
    RelatedWeakness,
    Weakness,
    Weaknesses,
    Category,
    Categories,
    Catalog
)

__all__ = [
    'Loader',
    'CommonBase',
    'RelatedWeakness',
    'Weakness',
    'Weaknesses',
    "Category",
    "Categories",
    'Catalog'
]