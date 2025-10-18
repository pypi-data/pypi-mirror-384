# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable
from typing_extensions import Literal

import httpx

from ..types import organization_config_update_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.organization_config_response import OrganizationConfigResponse
from ..types.shared_params.currency_conversion import CurrencyConversion

__all__ = ["OrganizationConfigResource", "AsyncOrganizationConfigResource"]


class OrganizationConfigResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> OrganizationConfigResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return OrganizationConfigResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OrganizationConfigResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return OrganizationConfigResourceWithStreamingResponse(self)

    def retrieve(
        self,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrganizationConfigResponse:
        """
        Retrieve the Organization-wide configuration details.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._get(
            f"/organizations/{org_id}/organizationconfig",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationConfigResponse,
        )

    def update(
        self,
        *,
        org_id: str | None = None,
        currency: str,
        day_epoch: str,
        days_before_bill_due: int,
        month_epoch: str,
        timezone: str,
        week_epoch: str,
        year_epoch: str,
        auto_approve_bills_grace_period: int | Omit = omit,
        auto_approve_bills_grace_period_unit: str | Omit = omit,
        auto_generate_statement_mode: Literal["NONE", "JSON", "JSON_AND_CSV"] | Omit = omit,
        bill_prefix: str | Omit = omit,
        commitment_fee_bill_in_advance: bool | Omit = omit,
        consolidate_bills: bool | Omit = omit,
        credit_application_order: List[Literal["PREPAYMENT", "BALANCE"]] | Omit = omit,
        currency_conversions: Iterable[CurrencyConversion] | Omit = omit,
        default_statement_definition_id: str | Omit = omit,
        external_invoice_date: str | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        scheduled_bill_interval: float | Omit = omit,
        sequence_start_number: int | Omit = omit,
        standing_charge_bill_in_advance: bool | Omit = omit,
        suppressed_empty_bills: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrganizationConfigResponse:
        """
        Update the Organization-wide configuration details.

        Args:
          currency:
              The currency code for the Organization. For example: USD, GBP, or EUR:

              - This defines the _billing currency_ for the Organization. You can override
                this by selecting a different billing currency at individual Account level.
              - You must first define the currencies you want to use in your Organization. See
                the [Currency](https://www.m3ter.com/docs/api#tag/Currency) section in this
                API Reference.

              **Note:** If you use a different currency as the _pricing currency_ for Plans to
              set charge rates for Product consumption by an Account, you must define a
              currency conversion rate from the pricing currency to the billing currency
              before you run billing for the Account, otherwise billing will fail. See below
              for the `currencyConversions` request parameter.

          day_epoch: Optional setting that defines the billing cycle date for Accounts that are
              billed daily. Defines the date of the first Bill:

              - For example, suppose the Plan you attach to an Account is configured for daily
                billing frequency and will apply to the Account from January 1st, 2022 until
                June 30th, 2022. If you set a `dayEpoch` date of January 2nd, 2022, then the
                first Bill is created for the Account on that date and subsequent Bills are
                created for the Account each day following through to the end of the billing
                service period.
              - The date is in ISO-8601 format.

          days_before_bill_due: Enter the number of days after the Bill generation date that you want to show on
              Bills as the due date.

              **Note:** If you define `daysBeforeBillDue` at individual Account level, this
              will take precedence over any `daysBeforeBillDue` setting defined at
              Organization level.

          month_epoch: Optional setting that defines the billing cycle date for Accounts that are
              billed monthly. Defines the date of the first Bill and then acts as reference
              for when subsequent Bills are created for the Account:

              - For example, suppose the Plan you attach to an Account is configured for
                monthly billing frequency and will apply to the Account from January 1st, 2022
                until June 30th, 2022. If you set a `monthEpoch` date of January 15th, 2022,
                then the first Bill is created for the Account on that date and subsequent
                Bills are created for the Account on the 15th of each month following through
                to the end of the billing service period - February 15th, March 15th, and so
                on.
              - The date is in ISO-8601 format.

          timezone: Sets the timezone for the Organization.

          week_epoch: Optional setting that defines the billing cycle date for Accounts that are
              billed weekly. Defines the date of the first Bill and then acts as reference for
              when subsequent Bills are created for the Account:

              - For example, suppose the Plan you attach to an Account is configured for
                weekly billing frequency and will apply to the Account from January 1st, 2022
                until June 30th, 2022. If you set a `weekEpoch` date of January 15th, 2022,
                which falls on a Saturday, then the first Bill is created for the Account on
                that date and subsequent Bills are created for the Account on Saturday of each
                week following through to the end of the billing service period.
              - The date is in ISO-8601 format.

          year_epoch: Optional setting that defines the billing cycle date for Accounts that are
              billed yearly. Defines the date of the first Bill and then acts as reference for
              when subsequent Bills are created for the Account:

              - For example, suppose the Plan you attach to an Account is configured for
                yearly billing frequency and will apply to the Account from January 1st, 2022
                until January 15th, 2028. If you set a `yearEpoch` date of January 1st, 2023,
                then the first Bill is created for the Account on that date and subsequent
                Bills are created for the Account on January 1st of each year following
                through to the end of the billing service period - January 1st, 2023, January
                1st, 2024 and so on.
              - The date is in ISO-8601 format.

          auto_approve_bills_grace_period: Grace period before bills are auto-approved. Used in combination with
              `autoApproveBillsGracePeriodUnit` parameter.

              **Note:** When used in combination with `autoApproveBillsGracePeriodUnit`
              enables auto-approval of Bills for Organization, which occurs when the specified
              time period has elapsed after Bill generation.

          auto_approve_bills_grace_period_unit: Time unit of grace period before bills are auto-approved. Used in combination
              with `autoApproveBillsGracePeriod` parameter. Allowed options are MINUTES,
              HOURS, or DAYS.

              **Note:** When used in combination with `autoApproveBillsGracePeriod` enables
              auto-approval of Bills for Organization, which occurs when the specified time
              period has elapsed after Bill generation.

          auto_generate_statement_mode: Specify whether to auto-generate statements once Bills are _approved_ or
              _locked_. It will not auto-generate if a bill is in _pending_ state.

              The default value is **None**.

              - **None**. Statements will not be auto-generated.
              - **JSON**. Statements are auto-generated in JSON format.
              - **JSON and CSV**. Statements are auto-generated in both JSON and CSV formats.

          bill_prefix: Prefix to be used for sequential invoice numbers. This will be combined with the
              `sequenceStartNumber`.

              **NOTES:**

              - If you do not define a `billPrefix`, a default will be used in the Console for
                the Bill **REFERENCE** number. This default will concatenate **INV-** with the
                last four characters of the `billId`.
              - If you do not define a `billPrefix`, the Bill response schema for API calls
                that retrieve Bill data will not contain a `sequentialInvoiceNumber`.

          commitment_fee_bill_in_advance: Boolean setting to specify whether commitments _(prepayments)_ are billed in
              advance at the start of each billing period, or billed in arrears at the end of
              each billing period.

              - **TRUE** - bill in advance _(start of each billing period)_.
              - **FALSE** - bill in arrears _(end of each billing period)_.

          consolidate_bills: Boolean setting to consolidate different billing frequencies onto the same bill.

              - **TRUE** - consolidate different billing frequencies onto the same bill.
              - **FALSE** - bills are not consolidated.

          credit_application_order: Define the order in which any Prepayment or Balance amounts on Accounts are to
              be drawn-down against for billing. Four options:

              - `"PREPAYMENT","BALANCE"`. Draw-down against Prepayment credit before Balance
                credit.
              - `"BALANCE","PREPAYMENT"`. Draw-down against Balance credit before Prepayment
                credit.
              - `"PREPAYMENT"`. Only draw-down against Prepayment credit.
              - `"BALANCE"`. Only draw-down against Balance credit.

              **NOTES:**

              - You can override this Organization-level setting for `creditApplicationOrder`
                at the level of an individual Account.
              - If the Account belongs to a Parent/Child Account hierarchy, then the
                `creditApplicationOrder` settings are not available, and the draw-down order
                defaults always to Prepayment then Balance order.

          currency_conversions:
              Define currency conversion rates from _pricing currency_ to _billing currency_:

              - You can use the `currency` request parameter with this call to define the
                billing currency for your Organization - see above.
              - You can also define a billing currency at the individual Account level and
                this will override the Organization billing currency.
              - A Plan used to set Product consumption charge rates on an Account might use a
                different pricing currency. At billing, charges are calculated in the pricing
                currency and then converted into billing currency amounts to appear on Bills.
                If you haven't defined a currency conversion rate from pricing to billing
                currency, billing will fail for the Account.

          default_statement_definition_id: Organization level default `statementDefinitionId` to be used when there is no
              statement definition linked to the account.

              Statement definitions are used to generate bill statements, which are
              informative backing sheets to invoices.

          external_invoice_date: Date to use for the invoice date. Allowed values are `FIRST_DAY_OF_NEXT_PERIOD`
              or `LAST_DAY_OF_ARREARS`.

          minimum_spend_bill_in_advance: Boolean setting to specify whether minimum spend amounts are billed in advance
              at the start of each billing period, or billed in arrears at the end of each
              billing period.

              - **TRUE** - bill in advance _(start of each billing period)_.
              - **FALSE** - bill in arrears _(end of each billing period)_.

          scheduled_bill_interval: Sets the required interval for updating bills. It is an optional parameter that
              can be set as:

              - **For portions of an hour (minutes)**. Two options: **0.25** (15 minutes) and
                **0.5** (30 minutes).
              - **For full hours.** Enter **1** for every hour, **2** for every two hours, and
                so on. Eight options: **1**, **2**, **3**, **4**, **6**, **8**, **12**, or
                **24**.
              - **Default.** The default is **0**, which disables scheduling.

          sequence_start_number: The starting number to be used for sequential invoice numbers. This will be
              combined with the `billPrefix`.

              For example, if you define `billPrefix` to be **INVOICE-** and you set the
              `seqenceStartNumber` as **100**, the first Bill created after updating your
              Organization Configuration will have a `sequentialInvoiceNumber` assigned of
              **INVOICE-101**. Subsequent Bills created will be numbered in time sequence for
              their initial creation date/time.

          standing_charge_bill_in_advance: Boolean setting to specify whether the standing charge is billed in advance at
              the start of each billing period, or billed in arrears at the end of each
              billing period.

              - **TRUE** - bill in advance _(start of each billing period)_.
              - **FALSE** - bill in arrears _(end of each billing period)_.

          suppressed_empty_bills: Boolean setting that supresses generating bills that have no line items.

              - **TRUE** - prevents generating bills with no line items.
              - **FALSE** - bills are still generated even when they have no line items.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._put(
            f"/organizations/{org_id}/organizationconfig",
            body=maybe_transform(
                {
                    "currency": currency,
                    "day_epoch": day_epoch,
                    "days_before_bill_due": days_before_bill_due,
                    "month_epoch": month_epoch,
                    "timezone": timezone,
                    "week_epoch": week_epoch,
                    "year_epoch": year_epoch,
                    "auto_approve_bills_grace_period": auto_approve_bills_grace_period,
                    "auto_approve_bills_grace_period_unit": auto_approve_bills_grace_period_unit,
                    "auto_generate_statement_mode": auto_generate_statement_mode,
                    "bill_prefix": bill_prefix,
                    "commitment_fee_bill_in_advance": commitment_fee_bill_in_advance,
                    "consolidate_bills": consolidate_bills,
                    "credit_application_order": credit_application_order,
                    "currency_conversions": currency_conversions,
                    "default_statement_definition_id": default_statement_definition_id,
                    "external_invoice_date": external_invoice_date,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "scheduled_bill_interval": scheduled_bill_interval,
                    "sequence_start_number": sequence_start_number,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "suppressed_empty_bills": suppressed_empty_bills,
                    "version": version,
                },
                organization_config_update_params.OrganizationConfigUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationConfigResponse,
        )


class AsyncOrganizationConfigResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncOrganizationConfigResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncOrganizationConfigResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOrganizationConfigResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncOrganizationConfigResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrganizationConfigResponse:
        """
        Retrieve the Organization-wide configuration details.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return await self._get(
            f"/organizations/{org_id}/organizationconfig",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationConfigResponse,
        )

    async def update(
        self,
        *,
        org_id: str | None = None,
        currency: str,
        day_epoch: str,
        days_before_bill_due: int,
        month_epoch: str,
        timezone: str,
        week_epoch: str,
        year_epoch: str,
        auto_approve_bills_grace_period: int | Omit = omit,
        auto_approve_bills_grace_period_unit: str | Omit = omit,
        auto_generate_statement_mode: Literal["NONE", "JSON", "JSON_AND_CSV"] | Omit = omit,
        bill_prefix: str | Omit = omit,
        commitment_fee_bill_in_advance: bool | Omit = omit,
        consolidate_bills: bool | Omit = omit,
        credit_application_order: List[Literal["PREPAYMENT", "BALANCE"]] | Omit = omit,
        currency_conversions: Iterable[CurrencyConversion] | Omit = omit,
        default_statement_definition_id: str | Omit = omit,
        external_invoice_date: str | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        scheduled_bill_interval: float | Omit = omit,
        sequence_start_number: int | Omit = omit,
        standing_charge_bill_in_advance: bool | Omit = omit,
        suppressed_empty_bills: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrganizationConfigResponse:
        """
        Update the Organization-wide configuration details.

        Args:
          currency:
              The currency code for the Organization. For example: USD, GBP, or EUR:

              - This defines the _billing currency_ for the Organization. You can override
                this by selecting a different billing currency at individual Account level.
              - You must first define the currencies you want to use in your Organization. See
                the [Currency](https://www.m3ter.com/docs/api#tag/Currency) section in this
                API Reference.

              **Note:** If you use a different currency as the _pricing currency_ for Plans to
              set charge rates for Product consumption by an Account, you must define a
              currency conversion rate from the pricing currency to the billing currency
              before you run billing for the Account, otherwise billing will fail. See below
              for the `currencyConversions` request parameter.

          day_epoch: Optional setting that defines the billing cycle date for Accounts that are
              billed daily. Defines the date of the first Bill:

              - For example, suppose the Plan you attach to an Account is configured for daily
                billing frequency and will apply to the Account from January 1st, 2022 until
                June 30th, 2022. If you set a `dayEpoch` date of January 2nd, 2022, then the
                first Bill is created for the Account on that date and subsequent Bills are
                created for the Account each day following through to the end of the billing
                service period.
              - The date is in ISO-8601 format.

          days_before_bill_due: Enter the number of days after the Bill generation date that you want to show on
              Bills as the due date.

              **Note:** If you define `daysBeforeBillDue` at individual Account level, this
              will take precedence over any `daysBeforeBillDue` setting defined at
              Organization level.

          month_epoch: Optional setting that defines the billing cycle date for Accounts that are
              billed monthly. Defines the date of the first Bill and then acts as reference
              for when subsequent Bills are created for the Account:

              - For example, suppose the Plan you attach to an Account is configured for
                monthly billing frequency and will apply to the Account from January 1st, 2022
                until June 30th, 2022. If you set a `monthEpoch` date of January 15th, 2022,
                then the first Bill is created for the Account on that date and subsequent
                Bills are created for the Account on the 15th of each month following through
                to the end of the billing service period - February 15th, March 15th, and so
                on.
              - The date is in ISO-8601 format.

          timezone: Sets the timezone for the Organization.

          week_epoch: Optional setting that defines the billing cycle date for Accounts that are
              billed weekly. Defines the date of the first Bill and then acts as reference for
              when subsequent Bills are created for the Account:

              - For example, suppose the Plan you attach to an Account is configured for
                weekly billing frequency and will apply to the Account from January 1st, 2022
                until June 30th, 2022. If you set a `weekEpoch` date of January 15th, 2022,
                which falls on a Saturday, then the first Bill is created for the Account on
                that date and subsequent Bills are created for the Account on Saturday of each
                week following through to the end of the billing service period.
              - The date is in ISO-8601 format.

          year_epoch: Optional setting that defines the billing cycle date for Accounts that are
              billed yearly. Defines the date of the first Bill and then acts as reference for
              when subsequent Bills are created for the Account:

              - For example, suppose the Plan you attach to an Account is configured for
                yearly billing frequency and will apply to the Account from January 1st, 2022
                until January 15th, 2028. If you set a `yearEpoch` date of January 1st, 2023,
                then the first Bill is created for the Account on that date and subsequent
                Bills are created for the Account on January 1st of each year following
                through to the end of the billing service period - January 1st, 2023, January
                1st, 2024 and so on.
              - The date is in ISO-8601 format.

          auto_approve_bills_grace_period: Grace period before bills are auto-approved. Used in combination with
              `autoApproveBillsGracePeriodUnit` parameter.

              **Note:** When used in combination with `autoApproveBillsGracePeriodUnit`
              enables auto-approval of Bills for Organization, which occurs when the specified
              time period has elapsed after Bill generation.

          auto_approve_bills_grace_period_unit: Time unit of grace period before bills are auto-approved. Used in combination
              with `autoApproveBillsGracePeriod` parameter. Allowed options are MINUTES,
              HOURS, or DAYS.

              **Note:** When used in combination with `autoApproveBillsGracePeriod` enables
              auto-approval of Bills for Organization, which occurs when the specified time
              period has elapsed after Bill generation.

          auto_generate_statement_mode: Specify whether to auto-generate statements once Bills are _approved_ or
              _locked_. It will not auto-generate if a bill is in _pending_ state.

              The default value is **None**.

              - **None**. Statements will not be auto-generated.
              - **JSON**. Statements are auto-generated in JSON format.
              - **JSON and CSV**. Statements are auto-generated in both JSON and CSV formats.

          bill_prefix: Prefix to be used for sequential invoice numbers. This will be combined with the
              `sequenceStartNumber`.

              **NOTES:**

              - If you do not define a `billPrefix`, a default will be used in the Console for
                the Bill **REFERENCE** number. This default will concatenate **INV-** with the
                last four characters of the `billId`.
              - If you do not define a `billPrefix`, the Bill response schema for API calls
                that retrieve Bill data will not contain a `sequentialInvoiceNumber`.

          commitment_fee_bill_in_advance: Boolean setting to specify whether commitments _(prepayments)_ are billed in
              advance at the start of each billing period, or billed in arrears at the end of
              each billing period.

              - **TRUE** - bill in advance _(start of each billing period)_.
              - **FALSE** - bill in arrears _(end of each billing period)_.

          consolidate_bills: Boolean setting to consolidate different billing frequencies onto the same bill.

              - **TRUE** - consolidate different billing frequencies onto the same bill.
              - **FALSE** - bills are not consolidated.

          credit_application_order: Define the order in which any Prepayment or Balance amounts on Accounts are to
              be drawn-down against for billing. Four options:

              - `"PREPAYMENT","BALANCE"`. Draw-down against Prepayment credit before Balance
                credit.
              - `"BALANCE","PREPAYMENT"`. Draw-down against Balance credit before Prepayment
                credit.
              - `"PREPAYMENT"`. Only draw-down against Prepayment credit.
              - `"BALANCE"`. Only draw-down against Balance credit.

              **NOTES:**

              - You can override this Organization-level setting for `creditApplicationOrder`
                at the level of an individual Account.
              - If the Account belongs to a Parent/Child Account hierarchy, then the
                `creditApplicationOrder` settings are not available, and the draw-down order
                defaults always to Prepayment then Balance order.

          currency_conversions:
              Define currency conversion rates from _pricing currency_ to _billing currency_:

              - You can use the `currency` request parameter with this call to define the
                billing currency for your Organization - see above.
              - You can also define a billing currency at the individual Account level and
                this will override the Organization billing currency.
              - A Plan used to set Product consumption charge rates on an Account might use a
                different pricing currency. At billing, charges are calculated in the pricing
                currency and then converted into billing currency amounts to appear on Bills.
                If you haven't defined a currency conversion rate from pricing to billing
                currency, billing will fail for the Account.

          default_statement_definition_id: Organization level default `statementDefinitionId` to be used when there is no
              statement definition linked to the account.

              Statement definitions are used to generate bill statements, which are
              informative backing sheets to invoices.

          external_invoice_date: Date to use for the invoice date. Allowed values are `FIRST_DAY_OF_NEXT_PERIOD`
              or `LAST_DAY_OF_ARREARS`.

          minimum_spend_bill_in_advance: Boolean setting to specify whether minimum spend amounts are billed in advance
              at the start of each billing period, or billed in arrears at the end of each
              billing period.

              - **TRUE** - bill in advance _(start of each billing period)_.
              - **FALSE** - bill in arrears _(end of each billing period)_.

          scheduled_bill_interval: Sets the required interval for updating bills. It is an optional parameter that
              can be set as:

              - **For portions of an hour (minutes)**. Two options: **0.25** (15 minutes) and
                **0.5** (30 minutes).
              - **For full hours.** Enter **1** for every hour, **2** for every two hours, and
                so on. Eight options: **1**, **2**, **3**, **4**, **6**, **8**, **12**, or
                **24**.
              - **Default.** The default is **0**, which disables scheduling.

          sequence_start_number: The starting number to be used for sequential invoice numbers. This will be
              combined with the `billPrefix`.

              For example, if you define `billPrefix` to be **INVOICE-** and you set the
              `seqenceStartNumber` as **100**, the first Bill created after updating your
              Organization Configuration will have a `sequentialInvoiceNumber` assigned of
              **INVOICE-101**. Subsequent Bills created will be numbered in time sequence for
              their initial creation date/time.

          standing_charge_bill_in_advance: Boolean setting to specify whether the standing charge is billed in advance at
              the start of each billing period, or billed in arrears at the end of each
              billing period.

              - **TRUE** - bill in advance _(start of each billing period)_.
              - **FALSE** - bill in arrears _(end of each billing period)_.

          suppressed_empty_bills: Boolean setting that supresses generating bills that have no line items.

              - **TRUE** - prevents generating bills with no line items.
              - **FALSE** - bills are still generated even when they have no line items.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return await self._put(
            f"/organizations/{org_id}/organizationconfig",
            body=await async_maybe_transform(
                {
                    "currency": currency,
                    "day_epoch": day_epoch,
                    "days_before_bill_due": days_before_bill_due,
                    "month_epoch": month_epoch,
                    "timezone": timezone,
                    "week_epoch": week_epoch,
                    "year_epoch": year_epoch,
                    "auto_approve_bills_grace_period": auto_approve_bills_grace_period,
                    "auto_approve_bills_grace_period_unit": auto_approve_bills_grace_period_unit,
                    "auto_generate_statement_mode": auto_generate_statement_mode,
                    "bill_prefix": bill_prefix,
                    "commitment_fee_bill_in_advance": commitment_fee_bill_in_advance,
                    "consolidate_bills": consolidate_bills,
                    "credit_application_order": credit_application_order,
                    "currency_conversions": currency_conversions,
                    "default_statement_definition_id": default_statement_definition_id,
                    "external_invoice_date": external_invoice_date,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "scheduled_bill_interval": scheduled_bill_interval,
                    "sequence_start_number": sequence_start_number,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "suppressed_empty_bills": suppressed_empty_bills,
                    "version": version,
                },
                organization_config_update_params.OrganizationConfigUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationConfigResponse,
        )


class OrganizationConfigResourceWithRawResponse:
    def __init__(self, organization_config: OrganizationConfigResource) -> None:
        self._organization_config = organization_config

        self.retrieve = to_raw_response_wrapper(
            organization_config.retrieve,
        )
        self.update = to_raw_response_wrapper(
            organization_config.update,
        )


class AsyncOrganizationConfigResourceWithRawResponse:
    def __init__(self, organization_config: AsyncOrganizationConfigResource) -> None:
        self._organization_config = organization_config

        self.retrieve = async_to_raw_response_wrapper(
            organization_config.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            organization_config.update,
        )


class OrganizationConfigResourceWithStreamingResponse:
    def __init__(self, organization_config: OrganizationConfigResource) -> None:
        self._organization_config = organization_config

        self.retrieve = to_streamed_response_wrapper(
            organization_config.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            organization_config.update,
        )


class AsyncOrganizationConfigResourceWithStreamingResponse:
    def __init__(self, organization_config: AsyncOrganizationConfigResource) -> None:
        self._organization_config = organization_config

        self.retrieve = async_to_streamed_response_wrapper(
            organization_config.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            organization_config.update,
        )
