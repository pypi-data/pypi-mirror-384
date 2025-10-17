# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["RawRepoByFullnameParams"]


class RawRepoByFullnameParams(TypedDict, total=False):
    full_names: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="fullNames")]]
    """Array of repository full names in "owner/name" format (1-100)"""
