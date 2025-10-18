# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Union
from datetime import date
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .address_param import AddressParam

__all__ = ["AccountUpdateParams"]


class AccountUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    code: Required[str]
    """Code of the Account. This is a unique short code used for the Account."""

    email_address: Required[Annotated[str, PropertyInfo(alias="emailAddress")]]
    """Contact email for the Account."""

    name: Required[str]
    """Name of the Account."""

    address: AddressParam
    """Contact address."""

    auto_generate_statement_mode: Annotated[
        Literal["NONE", "JSON", "JSON_AND_CSV"], PropertyInfo(alias="autoGenerateStatementMode")
    ]
    """Specify whether to auto-generate statements once Bills are approved or locked.

    - **None**. Statements will not be auto-generated.
    - **JSON**. Statements are auto-generated in JSON format.
    - **JSON and CSV**. Statements are auto-generated in both JSON and CSV formats.
    """

    bill_epoch: Annotated[Union[str, date], PropertyInfo(alias="billEpoch", format="iso8601")]
    """
    Optional setting to define a _billing cycle date_, which sets the date of the
    first Bill and acts as a reference for when in the applied billing frequency
    period subsequent bills are created:

    - For example, if you attach a Plan to an Account where the Plan is configured
      for monthly billing frequency and you've defined the period the Plan will
      apply to the Account to be from January 1st, 2022 until January 1st, 2023. You
      then set a `billEpoch` date of February 15th, 2022. The first Bill will be
      created for the Account on February 15th, and subsequent Bills created on the
      15th of the months following for the remainder of the billing period - March
      15th, April 15th, and so on.
    - If not defined, then the relevant Epoch date set for the billing frequency
      period at Organization level will be used instead.
    - The date is in ISO-8601 format.
    """

    config_data: Annotated[Dict[str, object], PropertyInfo(alias="configData")]
    """Configuration data for the Account Supported settings:

    - SendBillsToThirdParties ("true"/"false")
    """

    credit_application_order: Annotated[
        List[Literal["PREPAYMENT", "BALANCE"]], PropertyInfo(alias="creditApplicationOrder")
    ]
    """
    Define the order in which any Prepayment or Balance amounts on the Account are
    to be drawn-down against for billing. Four options:

    - `"PREPAYMENT","BALANCE"`. Draw-down against Prepayment credit before Balance
      credit.
    - `"BALANCE","PREPAYMENT"`. Draw-down against Balance credit before Prepayment
      credit.
    - `"PREPAYMENT"`. Only draw-down against Prepayment credit.
    - `"BALANCE"`. Only draw-down against Balance credit.

    **NOTES:**

    - Any setting you define here overrides the setting for credit application order
      at Organization level.
    - If the Account belongs to a Parent/Child Account hierarchy, then the
      `creditApplicationOrder` settings are not available, and the draw-down order
      defaults always to Prepayment then Balance order.
    """

    currency: str
    """Account level billing currency, such as USD or GBP. Optional attribute:

    - If you define an Account currency, this will be used for bills.
    - If you do not define a currency, the billing currency defined at
      Organizational level will be used.

    **Note:** If you've attached a Plan to the Account that uses a different
    currency to the billing currency, then you must add the relevant currency
    conversion rate at Organization level to ensure the billing process can convert
    line items calculated using the Plan currency into the selected billing
    currency. If you don't add these conversion rates, then bills will fail for the
    Account.
    """

    custom_fields: Annotated[Dict[str, Union[str, float]], PropertyInfo(alias="customFields")]
    """User defined fields enabling you to attach custom data.

    The value for a custom field can be either a string or a number.

    If `customFields` can also be defined for this entity at the Organizational
    level, `customField` values defined at individual level override values of
    `customFields` with the same name defined at Organization level.

    See
    [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
    in the m3ter documentation for more information.
    """

    days_before_bill_due: Annotated[int, PropertyInfo(alias="daysBeforeBillDue")]
    """
    Enter the number of days after the Bill generation date that you want to show on
    Bills as the due date.

    **Note:** If you define `daysBeforeBillDue` at individual Account level, this
    will take precedence over any `daysBeforeBillDue` setting defined at
    Organization level.
    """

    parent_account_id: Annotated[str, PropertyInfo(alias="parentAccountId")]
    """Parent Account ID, or null if this Account does not have a parent."""

    purchase_order_number: Annotated[str, PropertyInfo(alias="purchaseOrderNumber")]
    """Purchase Order Number of the Account.

    Optional attribute - allows you to set a purchase order number that comes
    through into invoicing. For example, your financial systems might require this
    as a reference for clearing payments.
    """

    statement_definition_id: Annotated[str, PropertyInfo(alias="statementDefinitionId")]
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

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
