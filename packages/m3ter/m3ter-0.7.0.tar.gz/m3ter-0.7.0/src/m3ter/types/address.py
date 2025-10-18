# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Address"]


class Address(BaseModel):
    address_line1: Optional[str] = FieldInfo(alias="addressLine1", default=None)

    address_line2: Optional[str] = FieldInfo(alias="addressLine2", default=None)

    address_line3: Optional[str] = FieldInfo(alias="addressLine3", default=None)

    address_line4: Optional[str] = FieldInfo(alias="addressLine4", default=None)

    country: Optional[str] = None

    locality: Optional[str] = None

    post_code: Optional[str] = FieldInfo(alias="postCode", default=None)

    region: Optional[str] = None
