# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["TransactionCreateParams"]


class TransactionCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    amount: Required[float]
    """The financial value of the transaction."""

    applied_date: Annotated[Union[str, datetime], PropertyInfo(alias="appliedDate", format="iso8601")]
    """The date _(in ISO 8601 format)_ when the Balance transaction was applied."""

    currency_paid: Annotated[str, PropertyInfo(alias="currencyPaid")]
    """The currency code of the payment if it differs from the Balance currency.

    For example: USD, GBP or EUR.
    """

    description: str
    """A brief description explaining the purpose and context of the transaction."""

    paid: float
    """The payment amount if the payment currency differs from the Balance currency."""

    transaction_date: Annotated[Union[str, datetime], PropertyInfo(alias="transactionDate", format="iso8601")]
    """The date _(in ISO 8601 format)_ when the transaction occurred."""

    transaction_type_id: Annotated[str, PropertyInfo(alias="transactionTypeId")]
    """The unique identifier (UUID) of the transaction type.

    This is obtained from the list of created Transaction Types within the
    Organization Configuration.
    """

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
