# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .data_field import DataField

__all__ = ["DerivedField"]


class DerivedField(DataField):
    calculation: str
    """
    The calculation used to transform the value of submitted `dataFields` in usage
    data. Calculation can reference `dataFields`, `customFields`, or system
    `Timestamp` fields. _(Example: datafieldms datafieldgb)_
    """
