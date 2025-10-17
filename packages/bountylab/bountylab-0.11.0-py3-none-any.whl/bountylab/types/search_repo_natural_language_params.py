# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = [
    "SearchRepoNaturalLanguageParams",
    "IncludeAttributes",
    "IncludeAttributesContributors",
    "IncludeAttributesStarrers",
]


class SearchRepoNaturalLanguageParams(TypedDict, total=False):
    query: Required[str]
    """Natural language query describing the repositories you want to find"""

    include_attributes: Annotated[IncludeAttributes, PropertyInfo(alias="includeAttributes")]
    """Optional graph relationships to include (owner, contributors, starrers)"""

    max_results: Annotated[int, PropertyInfo(alias="maxResults")]
    """Maximum number of results to return (default: 100, max: 1000)"""


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
