# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["AccountEndDateBillingEntitiesParams"]


class AccountEndDateBillingEntitiesParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    billing_entities: Required[
        Annotated[
            List[Literal["CONTRACT", "ACCOUNTPLAN", "PREPAYMENT", "PRICINGS", "COUNTER_PRICINGS"]],
            PropertyInfo(alias="billingEntities"),
        ]
    ]
    """
    Defines which billing entities associated with the Account will have the
    specified end-date applied. For example, if you want the specified end-date to
    be applied to all Prepayments/Commitments created for the Account use
    `"PREPAYMENT"`.
    """

    end_date: Required[Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]]
    """
    The end date and time applied to the specified billing entities _(in ISO 8601
    format)_.
    """

    apply_to_children: Annotated[bool, PropertyInfo(alias="applyToChildren")]
    """A Boolean TRUE/FALSE flag.

    For Parent Accounts, set to TRUE if you want the specified end-date to be
    applied to any billing entities associated with Child Accounts. _(Optional)_
    """
