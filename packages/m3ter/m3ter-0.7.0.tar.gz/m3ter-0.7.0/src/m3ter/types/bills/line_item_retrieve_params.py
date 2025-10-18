# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["LineItemRetrieveParams"]


class LineItemRetrieveParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    bill_id: Required[Annotated[str, PropertyInfo(alias="billId")]]

    additional: SequenceNotStr[str]
    """Comma separated list of additional fields."""
