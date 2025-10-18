# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["DataExplorerGroupParam"]


class DataExplorerGroupParam(TypedDict, total=False):
    group_type: Annotated[Literal["ACCOUNT", "DIMENSION", "TIME"], PropertyInfo(alias="groupType")]
