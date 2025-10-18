# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["AddressParam"]


class AddressParam(TypedDict, total=False):
    address_line1: Annotated[str, PropertyInfo(alias="addressLine1")]

    address_line2: Annotated[str, PropertyInfo(alias="addressLine2")]

    address_line3: Annotated[str, PropertyInfo(alias="addressLine3")]

    address_line4: Annotated[str, PropertyInfo(alias="addressLine4")]

    country: str

    locality: str

    post_code: Annotated[str, PropertyInfo(alias="postCode")]

    region: str
