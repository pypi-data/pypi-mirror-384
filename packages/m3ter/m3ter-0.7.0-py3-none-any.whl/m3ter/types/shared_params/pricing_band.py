# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["PricingBand"]


class PricingBand(TypedDict, total=False):
    fixed_price: Required[Annotated[float, PropertyInfo(alias="fixedPrice")]]
    """Fixed price charged for the Pricing band."""

    lower_limit: Required[Annotated[float, PropertyInfo(alias="lowerLimit")]]
    """Lower limit for the Pricing band."""

    unit_price: Required[Annotated[float, PropertyInfo(alias="unitPrice")]]
    """Unit price charged for the Pricing band."""

    id: str
    """The ID for the Pricing band."""

    credit_type_id: Annotated[str, PropertyInfo(alias="creditTypeId")]
    """**OBSOLETE - this is deprecated and no longer used.**"""
