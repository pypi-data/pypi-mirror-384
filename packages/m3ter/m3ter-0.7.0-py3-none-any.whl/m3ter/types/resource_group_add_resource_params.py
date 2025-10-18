# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ResourceGroupAddResourceParams"]


class ResourceGroupAddResourceParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    type: Required[str]

    target_id: Required[Annotated[str, PropertyInfo(alias="targetId")]]
    """The id of the item or group you want to:

    - _Add Item_ call: add to a Resource Group.
    - _Remove Item_ call: remove from the Resource Group.
    """

    target_type: Required[Annotated[Literal["ITEM", "GROUP"], PropertyInfo(alias="targetType")]]
    """
    When adding to or removing from a Resource Group, specify whether a single item
    or group:

    - `item`
      - _Add Item_ call: use to add a single meter to a Resource Group
      - _Remove Item_ call: use to remove a single from a Resource Group.
    - `group`
      - _Add Item_ call: use to add a Resource Group to another Resource Group and
        form a nested Resource Group
      - _Remove Item_ call: use remove a nested Resource Group from a Resource
        Group.
    """

    version: int
    """The version number of the group."""
