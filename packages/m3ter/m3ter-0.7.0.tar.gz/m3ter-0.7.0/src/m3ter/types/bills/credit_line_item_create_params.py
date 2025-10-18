# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["CreditLineItemCreateParams"]


class CreditLineItemCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    accounting_product_id: Required[Annotated[str, PropertyInfo(alias="accountingProductId")]]

    amount: Required[float]
    """The amount for the line item."""

    description: Required[str]
    """The description for the line item."""

    product_id: Required[Annotated[str, PropertyInfo(alias="productId")]]
    """The UUID of the Product."""

    referenced_bill_id: Required[Annotated[str, PropertyInfo(alias="referencedBillId")]]
    """The UUID of the bill for the line item."""

    referenced_line_item_id: Required[Annotated[str, PropertyInfo(alias="referencedLineItemId")]]
    """The UUID of the line item."""

    service_period_end_date: Required[
        Annotated[Union[str, datetime], PropertyInfo(alias="servicePeriodEndDate", format="iso8601")]
    ]
    """
    The service period end date in ISO-8601 format._(exclusive of the ending date)_.
    """

    service_period_start_date: Required[
        Annotated[Union[str, datetime], PropertyInfo(alias="servicePeriodStartDate", format="iso8601")]
    ]
    """The service period start date in ISO-8601 format.

    _(inclusive of the starting date)_.
    """

    credit_reason_id: Annotated[str, PropertyInfo(alias="creditReasonId")]
    """The UUID of the credit reason."""

    line_item_type: Annotated[
        Literal[
            "STANDING_CHARGE",
            "USAGE",
            "COUNTER_RUNNING_TOTAL_CHARGE",
            "COUNTER_ADJUSTMENT_DEBIT",
            "COUNTER_ADJUSTMENT_CREDIT",
            "USAGE_CREDIT",
            "MINIMUM_SPEND",
            "MINIMUM_SPEND_REFUND",
            "CREDIT_DEDUCTION",
            "MANUAL_ADJUSTMENT",
            "CREDIT_MEMO",
            "DEBIT_MEMO",
            "COMMITMENT_CONSUMED",
            "COMMITMENT_FEE",
            "OVERAGE_SURCHARGE",
            "OVERAGE_USAGE",
            "BALANCE_CONSUMED",
            "BALANCE_FEE",
        ],
        PropertyInfo(alias="lineItemType"),
    ]

    reason_id: Annotated[str, PropertyInfo(alias="reasonId")]
    """The UUID of the line item reason."""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
