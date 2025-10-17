# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, Optional
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = [
    "SearchUserSearchParams",
    "Filters",
    "FiltersGenericFieldFilter",
    "FiltersCompositeFilter",
    "FiltersCompositeFilterFilter",
]


class SearchUserSearchParams(TypedDict, total=False):
    query: Required[str]
    """Full-text search query across user fields.

    Searches: login, displayName, bio, company, location, emails, resolvedCountry,
    resolvedState, resolvedCity (with login weighted 2x)
    """

    filters: Optional[Filters]
    """Optional filters for narrowing search results.

    Supports filtering on: githubId, login, displayName, bio, company, location,
    emails, resolvedCountry, resolvedState, resolvedCity.

    Full-text searchable fields (automatically searched): login, displayName, bio,
    company, location, emails, resolvedCountry, resolvedState, resolvedCity.

    Filter structure:

    - Field filters: { field: "fieldName", op: "Eq"|"In", value: string|string[] }
    - Composite filters: { op: "And"|"Or", filters: [...] }

    Supported operators:

    - String fields: Eq (exact match), In (one of array)
    - Use And/Or to combine multiple filters
    """

    max_results: Annotated[int, PropertyInfo(alias="maxResults")]
    """Maximum number of results to return (default: 100, max: 1000)"""


class FiltersGenericFieldFilter(TypedDict, total=False):
    field: Required[str]
    """Field name to filter on"""

    op: Required[str]
    """Operation (Eq, In, Gte, etc.)"""

    value: Required[Union[str, float, SequenceNotStr[str], Iterable[float]]]
    """Filter value"""


class FiltersCompositeFilterFilter(TypedDict, total=False):
    field: Required[str]
    """Field name to filter on"""

    op: Required[str]
    """Operation (Eq, In, Gte, etc.)"""

    value: Required[Union[str, float, SequenceNotStr[str], Iterable[float]]]
    """Filter value"""


class FiltersCompositeFilter(TypedDict, total=False):
    filters: Required[Iterable[FiltersCompositeFilterFilter]]
    """Array of filters to combine"""

    op: Required[Literal["And", "Or"]]
    """Logical operator"""


Filters: TypeAlias = Union[FiltersGenericFieldFilter, FiltersCompositeFilter]
