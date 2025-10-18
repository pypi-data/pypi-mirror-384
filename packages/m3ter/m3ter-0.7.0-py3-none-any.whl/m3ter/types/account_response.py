# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import date, datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .address import Address
from .._models import BaseModel

__all__ = ["AccountResponse"]


class AccountResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    address: Optional[Address] = None
    """Contact address."""

    auto_generate_statement_mode: Optional[Literal["NONE", "JSON", "JSON_AND_CSV"]] = FieldInfo(
        alias="autoGenerateStatementMode", default=None
    )
    """Specify whether to auto-generate statements once Bills are approved or locked.

    - **None**. Statements will not be auto-generated.
    - **JSON**. Statements are auto-generated in JSON format.
    - **JSON and CSV**. Statements are auto-generated in both JSON and CSV formats.
    """

    bill_epoch: Optional[date] = FieldInfo(alias="billEpoch", default=None)
    """Defines first bill date for Account Bills.

    For example, if the Plan attached to the Account is set for monthly billing
    frequency and you set the first bill date to be January 1st, Bills are created
    every month starting on that date.

    Optional attribute - if not defined, then first bill date is determined by the
    Epoch settings at Organizational level.
    """

    code: Optional[str] = None
    """Code of the Account. This is a unique short code used for the Account."""

    config_data: Optional[Dict[str, object]] = FieldInfo(alias="configData", default=None)
    """Configuration data for the Account"""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created the account."""

    credit_application_order: Optional[List[Literal["PREPAYMENT", "BALANCE"]]] = FieldInfo(
        alias="creditApplicationOrder", default=None
    )
    """
    The order in which any Prepayment or Balance amounts on the Account are to be
    drawn-down against for billing. Four options:

    - `"PREPAYMENT","BALANCE"`. Draw-down against Prepayment credit before Balance
      credit.
    - `"BALANCE","PREPAYMENT"`. Draw-down against Balance credit before Prepayment
      credit.
    - `"PREPAYMENT"`. Only draw-down against Prepayment credit.
    - `"BALANCE"`. Only draw-down against Balance credit.
    """

    currency: Optional[str] = None
    """Account level billing currency, such as USD or GBP. Optional attribute:

    - If you define an Account currency, this will be used for bills.
    - If you do not define a currency, the billing currency defined at
      Organizational will be used.

    **Note:** If you've attached a Plan to the Account that uses a different
    currency to the billing currency, then you must add the relevant currency
    conversion rate at Organization level to ensure the billing process can convert
    line items calculated using the Plan currency into the selected billing
    currency. If you don't add these conversion rates, then bills will fail for the
    Account.
    """

    custom_fields: Optional[Dict[str, Union[str, float]]] = FieldInfo(alias="customFields", default=None)
    """User defined fields enabling you to attach custom data.

    The value for a custom field can be either a string or a number.

    If `customFields` can also be defined for this entity at the Organizational
    level,`customField` values defined at individual level override values of
    `customFields` with the same name defined at Organization level.

    See
    [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
    in the m3ter documentation for more information.
    """

    days_before_bill_due: Optional[int] = FieldInfo(alias="daysBeforeBillDue", default=None)
    """
    The number of days after the Bill generation date shown on Bills as the due
    date.
    """

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the Account was created _(in ISO 8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the Account was last modified _(in ISO 8601 format)_."""

    email_address: Optional[str] = FieldInfo(alias="emailAddress", default=None)
    """Contact email for the Account."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified the Account."""

    name: Optional[str] = None
    """Name of the Account."""

    parent_account_id: Optional[str] = FieldInfo(alias="parentAccountId", default=None)
    """Parent Account ID, or null if this account does not have a parent."""

    purchase_order_number: Optional[str] = FieldInfo(alias="purchaseOrderNumber", default=None)
    """Purchase Order Number of the Account.

    Optional attribute - allows you to set a purchase order number that comes
    through into invoicing. For example, your financial systems might require this
    as a reference for clearing payments.
    """

    statement_definition_id: Optional[str] = FieldInfo(alias="statementDefinitionId", default=None)
    """
    The UUID of the statement definition used when Bill statements are generated for
    the Account. If no statement definition is specified for the Account, the
    statement definition specified at Organizational level is used.

    Bill statements can be used as informative backing sheets to invoices. Based on
    the usage breakdown defined in the statement definition, generated statements
    give a breakdown of usage charges on Account Bills, which helps customers better
    understand usage charges incurred over the billing period.

    See
    [Working with Bill Statements](https://www.m3ter.com/docs/guides/running-viewing-and-managing-bills/working-with-bill-statements)
    in the m3ter documentation for more details.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
