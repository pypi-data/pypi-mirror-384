# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["TransactionSummaryResponse"]


class TransactionSummaryResponse(BaseModel):
    balance_consumed: Optional[float] = FieldInfo(alias="balanceConsumed", default=None)
    """Amount consumed from the original balance"""

    expired_balance_amount: Optional[float] = FieldInfo(alias="expiredBalanceAmount", default=None)
    """Amount of the balance that expired without being used"""

    initial_credit_amount: Optional[float] = FieldInfo(alias="initialCreditAmount", default=None)

    rollover_consumed: Optional[float] = FieldInfo(alias="rolloverConsumed", default=None)
    """Amount consumed from rollover credit"""

    total_credit_amount: Optional[float] = FieldInfo(alias="totalCreditAmount", default=None)

    total_debit_amount: Optional[float] = FieldInfo(alias="totalDebitAmount", default=None)
