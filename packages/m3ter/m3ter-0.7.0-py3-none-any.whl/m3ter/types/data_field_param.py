# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["DataFieldParam"]


class DataFieldParam(TypedDict, total=False):
    category: Required[Literal["WHO", "WHERE", "WHAT", "OTHER", "METADATA", "MEASURE", "INCOME", "COST"]]
    """The type of field (WHO, WHAT, WHERE, MEASURE, METADATA, INCOME, COST, OTHER)."""

    code: Required[str]
    """Short code to identify the field

    **NOTE:** Code has a maximum length of 80 characters and can only contain
    letters, numbers, underscore, and the dollar character, and must not start with
    a number.
    """

    name: Required[str]
    """Descriptive name of the field."""

    unit: str
    """The units to measure the data with.

    Should conform to _Unified Code for Units of Measure_ (UCUM). Required only for
    numeric field categories.
    """
