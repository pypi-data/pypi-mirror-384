# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, Optional
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = [
    "SearchRepoSearchParams",
    "Filters",
    "FiltersGenericFieldFilter",
    "FiltersCompositeFilter",
    "FiltersCompositeFilterFilter",
    "IncludeAttributes",
    "IncludeAttributesContributors",
    "IncludeAttributesStarrers",
]


class SearchRepoSearchParams(TypedDict, total=False):
    query: Required[str]
    """
    Natural language search query for semantic search across repository README and
    description using vector embeddings
    """

    filters: Optional[Filters]
    """Optional filters for narrowing search results.

    Supports filtering on: githubId, ownerLogin, name, stargazerCount, language,
    totalIssuesCount, totalIssuesOpen, totalIssuesClosed, lastContributorLocations.

    Filter structure:

    - Field filters: { field: "fieldName", op: "Eq"|"In"|"Gte"|"Lte", value:
      string|number|array }
    - Composite filters: { op: "And"|"Or", filters: [...] }

    Supported operators:

    - String fields: Eq (exact match), In (one of array)
    - Number fields: Eq (exact), In (one of array), Gte (>=), Lte (<=)
    - Use And/Or to combine multiple filters
    """

    include_attributes: Annotated[IncludeAttributes, PropertyInfo(alias="includeAttributes")]
    """Optional graph relationships to include (owner, contributors, starrers)"""

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


class IncludeAttributesContributors(TypedDict, total=False):
    limit: Required[int]
    """Maximum number of contributors to return (max: 100)"""


class IncludeAttributesStarrers(TypedDict, total=False):
    limit: Required[int]
    """Maximum number of starrers to return (max: 100)"""


class IncludeAttributes(TypedDict, total=False):
    contributors: IncludeAttributesContributors
    """Include repository contributors with limit"""

    owner: bool
    """Include repository owner information"""

    starrers: IncludeAttributesStarrers
    """Include users who starred the repository with limit"""
