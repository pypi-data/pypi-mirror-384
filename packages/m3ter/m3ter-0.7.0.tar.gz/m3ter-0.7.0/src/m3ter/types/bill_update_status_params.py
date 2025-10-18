# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BillUpdateStatusParams"]


class BillUpdateStatusParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    status: Required[Literal["PENDING", "APPROVED"]]
    """The new status you want to assign to the Bill.

    Must be one "Pending" or "Approved".
    """
