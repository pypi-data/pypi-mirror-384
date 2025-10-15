"""
Filters for Opensearch documents, inspired by django-filter.

This module provides a filtering system for Opensearch documents similar to
django-filter, but designed to work with Opensearch queries instead of Django ORM.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from django import forms
from django_opensearch_dsl import Document
from django_opensearch_dsl.search import Search


class BaseFilter(ABC):
    """Base class for all filters."""

    def __init__(self, field_name: str, label: str | None = None):
        """
        Initialize the filter.

        Args:
            field_name: The name of the field to filter on
            label: The label to use for the form field (defaults to field_name)
        """
        self.field_name = field_name
        self.label = label or field_name.replace("_", " ").title()

    @abstractmethod
    def filter(self, search: Search, value: Any) -> Search:
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: The value to filter by

        Returns:
            The filtered search object
        """

    @abstractmethod
    def get_form_field(self) -> forms.Field | dict[str, forms.Field]:
        """
        Get the form field for this filter.

        Returns:
            A Django form field or a dictionary of form fields
        """


class CharFilter(BaseFilter):
    """Filter for character fields."""

    def __init__(
        self,
        field_name: str,
        lookup_expr: str = "match",
        label: str | None = None,
    ):
        """
        Initialize the filter.

        Args:
            field_name: The name of the field to filter on
            lookup_expr: The lookup expression to use (match, term, wildcard, etc.)
            label: The label to use for the form field (defaults to field_name)
        """
        super().__init__(field_name, label)
        self.lookup_expr = lookup_expr

    def get_form_field(self) -> forms.Field:
        """
        Get the form field for this filter.

        Returns:
            A Django form field
        """
        return forms.CharField(
            label=self.label,
            required=False,
            widget=forms.TextInput(attrs={"class": "form-control"}),
        )

    def filter(self, search: Search, value: str) -> Search:
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: The value to filter by

        Returns:
            The filtered search object
        """
        if not value:
            return search

        if self.lookup_expr == "match":
            return search.query("match", **{self.field_name: value})
        if self.lookup_expr == "term":
            return search.query("term", **{self.field_name: value})
        if self.lookup_expr == "wildcard":
            return search.query("wildcard", **{self.field_name: f"*{value}*"})
        return search.query(self.lookup_expr, **{self.field_name: value})


class NumericFilter(BaseFilter):
    """Filter for numeric fields."""

    def __init__(
        self,
        field_name: str,
        lookup_expr: str = "term",
        label: str | None = None,
    ):
        """
        Initialize the filter.

        Args:
            field_name: The name of the field to filter on
            lookup_expr: The lookup expression to use (term, range, etc.)
            label: The label to use for the form field (defaults to field_name)
        """
        super().__init__(field_name, label)
        self.lookup_expr = lookup_expr

    def get_form_field(self) -> forms.Field:
        """
        Get the form field for this filter.

        Returns:
            A Django form field
        """
        return forms.FloatField(
            label=self.label,
            required=False,
            widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
        )

    def filter(self, search: Search, value: float) -> Search:
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: The value to filter by

        Returns:
            The filtered search object
        """
        if value is None:
            return search

        if self.lookup_expr == "term":
            return search.query("term", **{self.field_name: value})
        if self.lookup_expr == "gt":
            return search.query("range", **{self.field_name: {"gt": value}})
        if self.lookup_expr == "gte":
            return search.query("range", **{self.field_name: {"gte": value}})
        if self.lookup_expr == "lt":
            return search.query("range", **{self.field_name: {"lt": value}})
        if self.lookup_expr == "lte":
            return search.query("range", **{self.field_name: {"lte": value}})
        return search.query(self.lookup_expr, **{self.field_name: value})


class DateFilter(BaseFilter):
    """Filter for date fields."""

    def __init__(
        self,
        field_name: str,
        lookup_expr: str = "term",
        label: str | None = None,
    ):
        """
        Initialize the filter.

        Args:
            field_name: The name of the field to filter on
            lookup_expr: The lookup expression to use (term, range, etc.)
            label: The label to use for the form field (defaults to field_name)
        """
        super().__init__(field_name, label)
        self.lookup_expr = lookup_expr

    def get_form_field(self) -> forms.Field:
        """
        Get the form field for this filter.

        Returns:
            A Django form field
        """
        return forms.DateField(
            label=self.label,
            required=False,
            widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        )

    def filter(self, search: Search, value: str | datetime) -> Search:
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: The value to filter by

        Returns:
            The filtered search object
        """
        if not value:
            return search

        if self.lookup_expr == "term":
            return search.query("term", **{self.field_name: value})
        if self.lookup_expr == "gt":
            return search.query("range", **{self.field_name: {"gt": value}})
        if self.lookup_expr == "gte":
            return search.query("range", **{self.field_name: {"gte": value}})
        if self.lookup_expr == "lt":
            return search.query("range", **{self.field_name: {"lt": value}})
        if self.lookup_expr == "lte":
            return search.query("range", **{self.field_name: {"lte": value}})
        return search.query(self.lookup_expr, **{self.field_name: value})


class BooleanFilter(BaseFilter):
    """Filter for boolean fields."""

    def __init__(self, field_name: str, label: str | None = None):
        """
        Initialize the filter.

        Args:
            field_name: The name of the field to filter on
            label: The label to use for the form field (defaults to field_name)
        """
        super().__init__(field_name, label)

    def get_form_field(self) -> forms.Field:
        """
        Get the form field for this filter.

        Returns:
            A Django form field
        """
        return forms.BooleanField(
            label=self.label,
            required=False,
            widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        )

    def filter(self, search: Search, value: bool) -> Search:
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: The value to filter by

        Returns:
            The filtered search object
        """
        if value is None:
            return search

        return search.query("term", **{self.field_name: value})


class RangeFilter(BaseFilter):
    """Filter for range of numeric values."""

    def __init__(
        self,
        field_name: str,
        label: str | None = None,
        min_label: str | None = None,
        max_label: str | None = None,
    ):
        """
        Initialize the filter.

        Args:
            field_name: The name of the field to filter on
            label: The label to use for the form field (defaults to field_name)
            min_label: The label for the minimum value field (defaults to "Min {label}")
            max_label: The label for the maximum value field (defaults to "Max {label}")
        """
        super().__init__(field_name, label)
        self.min_label = min_label or f"Min {self.label}"
        self.max_label = max_label or f"Max {self.label}"

    def get_form_field(self) -> dict[str, forms.Field]:
        """
        Get the form fields for this filter.

        Returns:
            A dictionary with min_value and max_value form fields
        """
        return {
            "min_value": forms.FloatField(
                label=self.min_label,
                required=False,
                widget=forms.NumberInput(
                    attrs={"class": "form-control", "step": "any"},
                ),
            ),
            "max_value": forms.FloatField(
                label=self.max_label,
                required=False,
                widget=forms.NumberInput(
                    attrs={"class": "form-control", "step": "any"},
                ),
            ),
        }

    def filter(self, search: Search, value: dict[str, float]) -> Search:
        """
        Apply the filter to the search.

        Args:
            search: The search object to filter
            value: A dictionary with min_value and max_value

        Returns:
            The filtered search object
        """
        if not value or (
            value.get("min_value") is None and value.get("max_value") is None
        ):
            return search

        range_params = {}
        if value.get("min_value") is not None:
            range_params["gte"] = float(value["min_value"])
        if value.get("max_value") is not None:
            range_params["lte"] = float(value["max_value"])

        if range_params:
            return search.query("range", **{self.field_name: range_params})

        return search


class FilterSet:
    """Base class for filter sets."""

    def __init__(self, data: dict[str, Any] | None = None):
        """
        Initialize the filter set.

        Args:
            data: The data to filter by
        """
        self.data = data or {}
        self.filters = self.get_filters()

    @classmethod
    def get_filters(cls) -> dict[str, BaseFilter]:
        """
        Get all filters defined on the class.

        Returns:
            A dictionary of filter names to filter objects
        """
        filters = {}
        for name, obj in cls.__dict__.items():
            if isinstance(obj, BaseFilter):
                filters[name] = obj  # noqa: PERF403
        return filters

    def filter(self, search: Search) -> Search:
        """
        Apply all filters to the search.

        Args:
            search: The search object to filter

        Returns:
            The filtered search object
        """
        for name, filter_obj in self.filters.items():
            if isinstance(filter_obj, RangeFilter):
                # Handle RangeFilter which has multiple form fields
                min_field = f"{name}_min_value"
                max_field = f"{name}_max_value"

                # Check if either min or max value is provided
                if (
                    min_field in self.data and self.data[min_field] not in (None, "")
                ) or (
                    max_field in self.data and self.data[max_field] not in (None, "")
                ):
                    # Create a dictionary with min and max values
                    range_values = {}
                    if min_field in self.data and self.data[min_field] not in (
                        None,
                        "",
                    ):
                        range_values["min_value"] = self.data[min_field]
                    if max_field in self.data and self.data[max_field] not in (
                        None,
                        "",
                    ):
                        range_values["max_value"] = self.data[max_field]

                    # Apply the filter
                    search = filter_obj.filter(search, range_values)
            elif name in self.data and self.data[name] not in (None, ""):
                # Handle standard filters
                search = filter_obj.filter(search, self.data[name])

        # Apply sorting if specified
        if self.data.get("sort"):
            sort_field = self.data["sort"]
            search = search.sort(sort_field)

        return search


class DocumentFilterSet(FilterSet):
    """Base class for document filter sets."""

    document: type[Document] = None

    # Default sort choices - should be overridden by subclasses
    SORT_CHOICES = [
        ("", "Default"),
    ]

    # Pagination defaults
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100

    def __init__(self, data: dict[str, Any] | None = None):
        """
        Initialize the document filter set.

        Args:
            data: The data to filter by
        """
        super().__init__(data)
        if self.document is None:
            error_message = "DocumentFilterSet requires a document class"
            raise ValueError(error_message)

    def search(self) -> Search:
        """
        Get a filtered and paginated search for the document.

        Returns:
            A filtered and paginated search object
        """
        # Get the base search object
        search = self.document.search()

        # Apply filters and sorting
        search = self.filter(search)

        # Apply pagination if specified
        page = self.data.get("page", 1)
        if not page or page < 1:
            page = 1

        page_size = self.data.get("page_size", self.DEFAULT_PAGE_SIZE)
        if not page_size or page_size < 1:
            page_size = self.DEFAULT_PAGE_SIZE
        elif page_size > self.MAX_PAGE_SIZE:
            page_size = self.MAX_PAGE_SIZE

        # Calculate start and end indices for pagination
        start = (page - 1) * page_size
        end = start + page_size

        # Apply pagination
        search = search[start:end]

        return search  # noqa: RET504

    def get_form_class(self):
        """
        Get a form class for this filter set.

        Returns:
            A Django form class
        """
        form_fields = {}

        # Add filter fields
        for name, filter_obj in self.filters.items():
            form_field = filter_obj.get_form_field()
            if isinstance(form_field, dict):
                # Handle RangeFilter which returns a dictionary of form fields
                for field_suffix, field in form_field.items():
                    form_fields[f"{name}_{field_suffix}"] = field
            else:
                form_fields[name] = form_field

        # Add sorting field
        form_fields["sort"] = forms.ChoiceField(
            choices=self.SORT_CHOICES,
            required=False,
            label="Sort by",
            widget=forms.Select(attrs={"class": "form-select"}),
        )

        # Add pagination fields
        form_fields["page"] = forms.IntegerField(
            min_value=1,
            required=False,
            initial=1,
            label="Page",
            widget=forms.NumberInput(attrs={"class": "form-control"}),
        )

        form_fields["page_size"] = forms.IntegerField(
            min_value=1,
            max_value=self.MAX_PAGE_SIZE,
            required=False,
            initial=self.DEFAULT_PAGE_SIZE,
            label="Items per page",
            widget=forms.NumberInput(attrs={"class": "form-control"}),
        )

        return type(
            f"{self.__class__.__name__}Form",
            (forms.Form,),
            form_fields,
        )

    def get_form(self, **kwargs):
        """
        Get a form instance for this filter set.

        Args:
            **kwargs: Additional arguments to pass to the form constructor

        Returns:
            A Django form instance
        """
        form_class = self.get_form_class()

        if self.data:
            # If we have data, initialize the form with it
            return form_class(data=self.data, **kwargs)

        return form_class(**kwargs)