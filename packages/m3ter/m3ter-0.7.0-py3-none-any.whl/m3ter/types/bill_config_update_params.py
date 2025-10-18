# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import date
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BillConfigUpdateParams"]


class BillConfigUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    bill_lock_date: Annotated[Union[str, date], PropertyInfo(alias="billLockDate", format="iso8601")]
    """The global lock date when all Bills will be locked _(in ISO 8601 format)_.

    For example: `"2024-03-01"`.
    """

    version: int
    """The version number:

    - Default value when newly created is one.
    - On Update, version is required and must match the existing version because a
      check is performed to ensure sequential versioning is preserved. Version is
      incremented by 1 and listed in the response
    """
