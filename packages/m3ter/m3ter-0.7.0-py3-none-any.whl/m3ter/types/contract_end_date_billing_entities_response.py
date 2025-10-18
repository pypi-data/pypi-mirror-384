# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.set_string import SetString

__all__ = ["ContractEndDateBillingEntitiesResponse", "FailedEntities", "UpdatedEntities"]


class FailedEntities(BaseModel):
    accountplan: Optional[SetString] = FieldInfo(alias="ACCOUNTPLAN", default=None)

    contract: Optional[SetString] = FieldInfo(alias="CONTRACT", default=None)

    counter_pricings: Optional[SetString] = FieldInfo(alias="COUNTER_PRICINGS", default=None)

    prepayment: Optional[SetString] = FieldInfo(alias="PREPAYMENT", default=None)

    pricings: Optional[SetString] = FieldInfo(alias="PRICINGS", default=None)


class UpdatedEntities(BaseModel):
    accountplan: Optional[SetString] = FieldInfo(alias="ACCOUNTPLAN", default=None)

    contract: Optional[SetString] = FieldInfo(alias="CONTRACT", default=None)

    counter_pricings: Optional[SetString] = FieldInfo(alias="COUNTER_PRICINGS", default=None)

    prepayment: Optional[SetString] = FieldInfo(alias="PREPAYMENT", default=None)

    pricings: Optional[SetString] = FieldInfo(alias="PRICINGS", default=None)


class ContractEndDateBillingEntitiesResponse(BaseModel):
    failed_entities: Optional[FailedEntities] = FieldInfo(alias="failedEntities", default=None)
    """
    A dictionary with keys as identifiers of billing entities and values as lists
    containing details of the entities for which the update failed.
    """

    status_message: Optional[str] = FieldInfo(alias="statusMessage", default=None)
    """A message indicating the status of the operation."""

    updated_entities: Optional[UpdatedEntities] = FieldInfo(alias="updatedEntities", default=None)
    """
    A dictionary with keys as identifiers of billing entities and values as lists
    containing details of the updated entities.
    """
