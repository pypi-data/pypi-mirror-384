# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required

from .data_field_param import DataFieldParam

__all__ = ["DerivedFieldParam"]


class DerivedFieldParam(DataFieldParam, total=False):
    calculation: Required[str]
    """
    The calculation used to transform the value of submitted `dataFields` in usage
    data. Calculation can reference `dataFields`, `customFields`, or system
    `Timestamp` fields. _(Example: datafieldms datafieldgb)_
    """
