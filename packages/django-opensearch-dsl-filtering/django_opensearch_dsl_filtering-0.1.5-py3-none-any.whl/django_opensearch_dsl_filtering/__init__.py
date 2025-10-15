"""
Document FilterSet package for filtering Opensearch documents.

This package provides a filtering system for Opensearch documents similar to
django-filter, but designed to work with Opensearch queries instead of Django ORM.
"""

from .filters import (
    BaseFilter,
    BooleanFilter,
    CharFilter,
    DateFilter,
    DocumentFilterSet,
    FilterSet,
    NumericFilter,
    RangeFilter,
)

__all__ = [
    "BaseFilter",
    "BooleanFilter",
    "CharFilter",
    "DateFilter",
    "DocumentFilterSet",
    "FilterSet",
    "NumericFilter",
    "RangeFilter",
]
