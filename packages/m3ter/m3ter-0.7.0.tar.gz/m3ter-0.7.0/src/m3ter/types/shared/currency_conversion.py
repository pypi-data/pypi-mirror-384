# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["CurrencyConversion"]


class CurrencyConversion(BaseModel):
    from_: str = FieldInfo(alias="from")
    """Currency to convert from. For example: GBP."""

    to: str
    """Currency to convert to. For example: USD."""

    multiplier: Optional[float] = None
    """Conversion rate between currencies."""
