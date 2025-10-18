# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["CounterCreateParams"]


class CounterCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    name: Required[str]
    """Descriptive name for the Counter."""

    unit: Required[str]
    """
    User defined label for units shown on Bill line items, and indicating to your
    customers what they are being charged for.
    """

    code: str
    """Code for the Counter. A unique short code to identify the Counter."""

    product_id: Annotated[str, PropertyInfo(alias="productId")]
    """UUID of the product the Counter belongs to.

    _(Optional)_ - if left blank, the Counter is Global. A Global Counter can be
    used to price Plans or Plan Templates belonging to any Product.
    """

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
