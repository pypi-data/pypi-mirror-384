# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["RawUserContributesParams"]


class RawUserContributesParams(TypedDict, total=False):
    limit: str
    """Maximum number of results to return (default: 100, max: 1000)"""

    offset: str
    """Number of results to skip (default: 0)"""
