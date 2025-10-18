# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["PricingBand"]


class PricingBand(BaseModel):
    fixed_price: float = FieldInfo(alias="fixedPrice")
    """Fixed price charged for the Pricing band."""

    lower_limit: float = FieldInfo(alias="lowerLimit")
    """Lower limit for the Pricing band."""

    unit_price: float = FieldInfo(alias="unitPrice")
    """Unit price charged for the Pricing band."""

    id: Optional[str] = None
    """The ID for the Pricing band."""

    credit_type_id: Optional[str] = FieldInfo(alias="creditTypeId", default=None)
    """**OBSOLETE - this is deprecated and no longer used.**"""
