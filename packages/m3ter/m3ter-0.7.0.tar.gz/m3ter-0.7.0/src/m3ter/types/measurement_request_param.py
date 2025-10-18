# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["MeasurementRequestParam"]


class MeasurementRequestParam(TypedDict, total=False):
    account: Required[str]
    """Code of the Account the measurement is for."""

    meter: Required[str]
    """Short code identifying the Meter the measurement is for."""

    ts: Required[Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]]
    """Timestamp for the measurement _(in ISO 8601 format)_."""

    cost: Dict[str, float]
    """'cost' values"""

    ets: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """End timestamp for the measurement _(in ISO 8601 format)_. _(Optional)_.

    Can be used in the case a usage event needs to have an explicit start and end
    rather than being instantaneous.
    """

    income: Dict[str, float]
    """'income' values"""

    measure: Dict[str, float]
    """'measure' values"""

    metadata: Dict[str, str]
    """'metadata' values"""

    other: Dict[str, str]
    """'other' values"""

    uid: str
    """Unique ID for this measurement."""

    what: Dict[str, str]
    """'what' values"""

    where: Dict[str, str]
    """'where' values"""

    who: Dict[str, str]
    """'who' values"""
