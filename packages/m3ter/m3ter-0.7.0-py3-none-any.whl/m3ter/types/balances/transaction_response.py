# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["TransactionResponse"]


class TransactionResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    amount: Optional[float] = None
    """The financial value of the transaction, as recorded in the balance."""

    applied_date: Optional[datetime] = FieldInfo(alias="appliedDate", default=None)
    """
    The date _(in ISO 8601 format)_ when the balance transaction was applied, i.e.,
    when the balance was affected.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) for the user who created the balance transaction."""

    currency_paid: Optional[str] = FieldInfo(alias="currencyPaid", default=None)
    """
    The currency code such as USD, GBP, EUR of the payment, if it differs from the
    balance currency.
    """

    description: Optional[str] = None
    """A brief description explaining the purpose or context of the transaction."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """
    The date and time _(in ISO 8601 format)_ when the balance transaction was first
    created.
    """

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The date and time _(in ISO 8601 format)_ when the balance transaction was last
    modified.
    """

    entity_id: Optional[str] = FieldInfo(alias="entityId", default=None)
    """
    The unique identifier (UUID) for the entity associated with the Transaction, as
    specified by the `entityType`.
    """

    entity_type: Optional[Literal["BILL", "COMMITMENT", "USER", "SERVICE_USER", "SCHEDULER"]] = FieldInfo(
        alias="entityType", default=None
    )
    """
    The type of entity associated with the Transaction - identifies who or what was
    responsible for the Transaction being added to the Balance - such as a **User**,
    a **Service User**, or a **Bill**.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """
    The unique identifier (UUID) for the user who last modified the balance
    transaction.
    """

    paid: Optional[float] = None
    """
    The actual payment amount if the payment currency differs from the Balance
    currency.
    """

    transaction_date: Optional[datetime] = FieldInfo(alias="transactionDate", default=None)
    """
    The date _(in ISO 8601 format)_ when the transaction was recorded in the system.
    """

    transaction_type_id: Optional[str] = FieldInfo(alias="transactionTypeId", default=None)
    """The unique identifier (UUID) for the Transaction type.

    This is obtained from the list of created Transaction Types within the
    Organization Configuration.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
