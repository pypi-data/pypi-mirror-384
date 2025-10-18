# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["DataField"]


class DataField(BaseModel):
    category: Literal["WHO", "WHERE", "WHAT", "OTHER", "METADATA", "MEASURE", "INCOME", "COST"]
    """The type of field (WHO, WHAT, WHERE, MEASURE, METADATA, INCOME, COST, OTHER)."""

    code: str
    """Short code to identify the field

    **NOTE:** Code has a maximum length of 80 characters and can only contain
    letters, numbers, underscore, and the dollar character, and must not start with
    a number.
    """

    name: str
    """Descriptive name of the field."""

    unit: Optional[str] = None
    """The units to measure the data with.

    Should conform to _Unified Code for Units of Measure_ (UCUM). Required only for
    numeric field categories.
    """
