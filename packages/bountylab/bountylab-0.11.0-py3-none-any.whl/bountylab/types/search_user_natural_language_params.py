# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["SearchUserNaturalLanguageParams"]


class SearchUserNaturalLanguageParams(TypedDict, total=False):
    query: Required[str]
    """Natural language query describing the users you want to find"""

    max_results: Annotated[int, PropertyInfo(alias="maxResults")]
    """Maximum number of results to return (default: 100, max: 1000)"""
