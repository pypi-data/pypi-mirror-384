# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Union, Optional
from datetime import date, datetime
from typing_extensions import Literal

import httpx

from ..types import (
    account_list_params,
    account_create_params,
    account_search_params,
    account_update_params,
    account_get_children_params,
    account_end_date_billing_entities_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncCursor, AsyncCursor
from .._base_client import AsyncPaginator, make_request_options
from ..types.address_param import AddressParam
from ..types.account_response import AccountResponse
from ..types.account_search_response import AccountSearchResponse
from ..types.account_end_date_billing_entities_response import AccountEndDateBillingEntitiesResponse

__all__ = ["AccountsResource", "AsyncAccountsResource"]


class AccountsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AccountsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AccountsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AccountsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AccountsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        code: str,
        email_address: str,
        name: str,
        address: AddressParam | Omit = omit,
        auto_generate_statement_mode: Literal["NONE", "JSON", "JSON_AND_CSV"] | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        config_data: Dict[str, object] | Omit = omit,
        credit_application_order: List[Literal["PREPAYMENT", "BALANCE"]] | Omit = omit,
        currency: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        days_before_bill_due: int | Omit = omit,
        parent_account_id: str | Omit = omit,
        purchase_order_number: str | Omit = omit,
        statement_definition_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountResponse:
        """Create a new Account within the Organization.

        Args:
          code: Code of the Account.

        This is a unique short code used for the Account.

          email_address: Contact email for the Account.

          name: Name of the Account.

          address: Contact address.

          auto_generate_statement_mode: Specify whether to auto-generate statements once Bills are approved or locked.

              - **None**. Statements will not be auto-generated.
              - **JSON**. Statements are auto-generated in JSON format.
              - **JSON and CSV**. Statements are auto-generated in both JSON and CSV formats.

          bill_epoch: Optional setting to define a _billing cycle date_, which sets the date of the
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

          config_data:
              Configuration data for the Account Supported settings:

              - SendBillsToThirdParties ("true"/"false")

          credit_application_order: Define the order in which any Prepayment or Balance amounts on the Account are
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

          currency:
              Account level billing currency, such as USD or GBP. Optional attribute:

              - If you define an Account currency, this will be used for bills.
              - If you do not define a currency, the billing currency defined at
                Organizational level will be used.

              **Note:** If you've attached a Plan to the Account that uses a different
              currency to the billing currency, then you must add the relevant currency
              conversion rate at Organization level to ensure the billing process can convert
              line items calculated using the Plan currency into the selected billing
              currency. If you don't add these conversion rates, then bills will fail for the
              Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          days_before_bill_due: Enter the number of days after the Bill generation date that you want to show on
              Bills as the due date.

              **Note:** If you define `daysBeforeBillDue` at individual Account level, this
              will take precedence over any `daysBeforeBillDue` setting defined at
              Organization level.

          parent_account_id: Parent Account ID, or null if this Account does not have a parent.

          purchase_order_number: Purchase Order Number of the Account.

              Optional attribute - allows you to set a purchase order number that comes
              through into invoicing. For example, your financial systems might require this
              as a reference for clearing payments.

          statement_definition_id: The UUID of the statement definition used when Bill statements are generated for
              the Account. If no statement definition is specified for the Account, the
              statement definition specified at Organizational level is used.

              Bill statements can be used as informative backing sheets to invoices. Based on
              the usage breakdown defined in the statement definition, generated statements
              give a breakdown of usage charges on Account Bills, which helps customers better
              understand usage charges incurred over the billing period.

              See
              [Working with Bill Statements](https://www.m3ter.com/docs/guides/running-viewing-and-managing-bills/working-with-bill-statements)
              in the m3ter documentation for more details.

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
        return self._post(
            f"/organizations/{org_id}/accounts",
            body=maybe_transform(
                {
                    "code": code,
                    "email_address": email_address,
                    "name": name,
                    "address": address,
                    "auto_generate_statement_mode": auto_generate_statement_mode,
                    "bill_epoch": bill_epoch,
                    "config_data": config_data,
                    "credit_application_order": credit_application_order,
                    "currency": currency,
                    "custom_fields": custom_fields,
                    "days_before_bill_due": days_before_bill_due,
                    "parent_account_id": parent_account_id,
                    "purchase_order_number": purchase_order_number,
                    "statement_definition_id": statement_definition_id,
                    "version": version,
                },
                account_create_params.AccountCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountResponse:
        """
        Retrieve the Account with the given Account UUID.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/organizations/{org_id}/accounts/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        code: str,
        email_address: str,
        name: str,
        address: AddressParam | Omit = omit,
        auto_generate_statement_mode: Literal["NONE", "JSON", "JSON_AND_CSV"] | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        config_data: Dict[str, object] | Omit = omit,
        credit_application_order: List[Literal["PREPAYMENT", "BALANCE"]] | Omit = omit,
        currency: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        days_before_bill_due: int | Omit = omit,
        parent_account_id: str | Omit = omit,
        purchase_order_number: str | Omit = omit,
        statement_definition_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountResponse:
        """
        Update the Account with the given Account UUID.

        **Note:** If you have created Custom Fields for an Account, when you use this
        endpoint to update the Account, use the `customFields` parameter to preserve
        those Custom Fields. If you omit them from the update request, they will be
        lost.

        Args:
          code: Code of the Account. This is a unique short code used for the Account.

          email_address: Contact email for the Account.

          name: Name of the Account.

          address: Contact address.

          auto_generate_statement_mode: Specify whether to auto-generate statements once Bills are approved or locked.

              - **None**. Statements will not be auto-generated.
              - **JSON**. Statements are auto-generated in JSON format.
              - **JSON and CSV**. Statements are auto-generated in both JSON and CSV formats.

          bill_epoch: Optional setting to define a _billing cycle date_, which sets the date of the
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

          config_data:
              Configuration data for the Account Supported settings:

              - SendBillsToThirdParties ("true"/"false")

          credit_application_order: Define the order in which any Prepayment or Balance amounts on the Account are
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

          currency:
              Account level billing currency, such as USD or GBP. Optional attribute:

              - If you define an Account currency, this will be used for bills.
              - If you do not define a currency, the billing currency defined at
                Organizational level will be used.

              **Note:** If you've attached a Plan to the Account that uses a different
              currency to the billing currency, then you must add the relevant currency
              conversion rate at Organization level to ensure the billing process can convert
              line items calculated using the Plan currency into the selected billing
              currency. If you don't add these conversion rates, then bills will fail for the
              Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          days_before_bill_due: Enter the number of days after the Bill generation date that you want to show on
              Bills as the due date.

              **Note:** If you define `daysBeforeBillDue` at individual Account level, this
              will take precedence over any `daysBeforeBillDue` setting defined at
              Organization level.

          parent_account_id: Parent Account ID, or null if this Account does not have a parent.

          purchase_order_number: Purchase Order Number of the Account.

              Optional attribute - allows you to set a purchase order number that comes
              through into invoicing. For example, your financial systems might require this
              as a reference for clearing payments.

          statement_definition_id: The UUID of the statement definition used when Bill statements are generated for
              the Account. If no statement definition is specified for the Account, the
              statement definition specified at Organizational level is used.

              Bill statements can be used as informative backing sheets to invoices. Based on
              the usage breakdown defined in the statement definition, generated statements
              give a breakdown of usage charges on Account Bills, which helps customers better
              understand usage charges incurred over the billing period.

              See
              [Working with Bill Statements](https://www.m3ter.com/docs/guides/running-viewing-and-managing-bills/working-with-bill-statements)
              in the m3ter documentation for more details.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/organizations/{org_id}/accounts/{id}",
            body=maybe_transform(
                {
                    "code": code,
                    "email_address": email_address,
                    "name": name,
                    "address": address,
                    "auto_generate_statement_mode": auto_generate_statement_mode,
                    "bill_epoch": bill_epoch,
                    "config_data": config_data,
                    "credit_application_order": credit_application_order,
                    "currency": currency,
                    "custom_fields": custom_fields,
                    "days_before_bill_due": days_before_bill_due,
                    "parent_account_id": parent_account_id,
                    "purchase_order_number": purchase_order_number,
                    "statement_definition_id": statement_definition_id,
                    "version": version,
                },
                account_update_params.AccountUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        codes: SequenceNotStr[str] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[AccountResponse]:
        """
        Retrieve a list of Accounts that can be filtered by Account ID or Account Code.

        Args:
          codes: List of Account Codes to retrieve. These are unique short codes for each
              Account.

          ids: List of Account IDs to retrieve.

          next_token: `nextToken` for multi-page retrievals.

          page_size: Number of accounts to retrieve per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/accounts",
            page=SyncCursor[AccountResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "codes": codes,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    account_list_params.AccountListParams,
                ),
            ),
            model=AccountResponse,
        )

    def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountResponse:
        """Delete the Account with the given UUID.

        This may fail if there are any
        AccountPlans that reference the Account being deleted.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/organizations/{org_id}/accounts/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountResponse,
        )

    def end_date_billing_entities(
        self,
        id: str,
        *,
        org_id: str | None = None,
        billing_entities: List[Literal["CONTRACT", "ACCOUNTPLAN", "PREPAYMENT", "PRICINGS", "COUNTER_PRICINGS"]],
        end_date: Union[str, datetime],
        apply_to_children: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountEndDateBillingEntitiesResponse:
        """
        Apply the specified end-date to billing entities associated with an Account.

        **NOTE:**

        - When you successfully end-date billing entities, the version number of each
          entity is incremented.

        Args:
          billing_entities: Defines which billing entities associated with the Account will have the
              specified end-date applied. For example, if you want the specified end-date to
              be applied to all Prepayments/Commitments created for the Account use
              `"PREPAYMENT"`.

          end_date: The end date and time applied to the specified billing entities _(in ISO 8601
              format)_.

          apply_to_children: A Boolean TRUE/FALSE flag. For Parent Accounts, set to TRUE if you want the
              specified end-date to be applied to any billing entities associated with Child
              Accounts. _(Optional)_

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/organizations/{org_id}/accounts/{id}/enddatebillingentities",
            body=maybe_transform(
                {
                    "billing_entities": billing_entities,
                    "end_date": end_date,
                    "apply_to_children": apply_to_children,
                },
                account_end_date_billing_entities_params.AccountEndDateBillingEntitiesParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountEndDateBillingEntitiesResponse,
        )

    def get_children(
        self,
        id: str,
        *,
        org_id: str | None = None,
        next_token: Optional[str] | Omit = omit,
        page_size: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountResponse:
        """
        Retrieve a list of Accounts that are children of the specified Account.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/organizations/{org_id}/accounts/{id}/children",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    account_get_children_params.AccountGetChildrenParams,
                ),
            ),
            cast_to=AccountResponse,
        )

    def search(
        self,
        *,
        org_id: str | None = None,
        from_document: int | Omit = omit,
        operator: Literal["AND", "OR"] | Omit = omit,
        page_size: int | Omit = omit,
        search_query: str | Omit = omit,
        sort_by: str | Omit = omit,
        sort_order: Literal["ASC", "DESC"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountSearchResponse:
        """
        Search for Account entities.

        This endpoint executes a search query for Accounts based on the user specified
        search criteria. The search query is customizable, allowing for complex nested
        conditions and sorting. The returned list of Accounts can be paginated for
        easier management.

        Args:
          from_document: `fromDocument` for multi page retrievals.

          operator: Search Operator to be used while querying search.

          page_size: Number of Accounts to retrieve per page.

              **NOTE:** If not defined, default is 10.

          search_query:
              Query for data using special syntax:

              - Query parameters should be delimited using the $ (dollar sign).
              - Allowed comparators are:
                - (greater than) >
                - (greater than or equal to) >=
                - (equal to) :
                - (less than) <
                - (less than or equal to) <=
                - (match phrase/prefix) ~
              - Allowed parameters are: name, code, currency, purchaseOrderNumber,
                parentAccountId, codes, id, createdBy, dtCreated, lastModifiedBy, ids.
              - Query example:
                - searchQuery=name~Premium On$currency:USD.
                - This query is translated into: find accounts whose name contains the
                  phrase/prefix 'Premium On' AND the account currency is USD.

              **Note:** Using the ~ match phrase/prefix comparator. For best results, we
              recommend treating this as a "starts with" comparator for your search query.

          sort_by: Name of the parameter on which sorting is performed. Use any field available on
              the Account entity to sort by, such as `name`, `code`, and so on.

          sort_order: Sorting order.

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
            f"/organizations/{org_id}/accounts/search",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "from_document": from_document,
                        "operator": operator,
                        "page_size": page_size,
                        "search_query": search_query,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                    },
                    account_search_params.AccountSearchParams,
                ),
            ),
            cast_to=AccountSearchResponse,
        )


class AsyncAccountsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAccountsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAccountsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAccountsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncAccountsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        code: str,
        email_address: str,
        name: str,
        address: AddressParam | Omit = omit,
        auto_generate_statement_mode: Literal["NONE", "JSON", "JSON_AND_CSV"] | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        config_data: Dict[str, object] | Omit = omit,
        credit_application_order: List[Literal["PREPAYMENT", "BALANCE"]] | Omit = omit,
        currency: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        days_before_bill_due: int | Omit = omit,
        parent_account_id: str | Omit = omit,
        purchase_order_number: str | Omit = omit,
        statement_definition_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountResponse:
        """Create a new Account within the Organization.

        Args:
          code: Code of the Account.

        This is a unique short code used for the Account.

          email_address: Contact email for the Account.

          name: Name of the Account.

          address: Contact address.

          auto_generate_statement_mode: Specify whether to auto-generate statements once Bills are approved or locked.

              - **None**. Statements will not be auto-generated.
              - **JSON**. Statements are auto-generated in JSON format.
              - **JSON and CSV**. Statements are auto-generated in both JSON and CSV formats.

          bill_epoch: Optional setting to define a _billing cycle date_, which sets the date of the
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

          config_data:
              Configuration data for the Account Supported settings:

              - SendBillsToThirdParties ("true"/"false")

          credit_application_order: Define the order in which any Prepayment or Balance amounts on the Account are
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

          currency:
              Account level billing currency, such as USD or GBP. Optional attribute:

              - If you define an Account currency, this will be used for bills.
              - If you do not define a currency, the billing currency defined at
                Organizational level will be used.

              **Note:** If you've attached a Plan to the Account that uses a different
              currency to the billing currency, then you must add the relevant currency
              conversion rate at Organization level to ensure the billing process can convert
              line items calculated using the Plan currency into the selected billing
              currency. If you don't add these conversion rates, then bills will fail for the
              Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          days_before_bill_due: Enter the number of days after the Bill generation date that you want to show on
              Bills as the due date.

              **Note:** If you define `daysBeforeBillDue` at individual Account level, this
              will take precedence over any `daysBeforeBillDue` setting defined at
              Organization level.

          parent_account_id: Parent Account ID, or null if this Account does not have a parent.

          purchase_order_number: Purchase Order Number of the Account.

              Optional attribute - allows you to set a purchase order number that comes
              through into invoicing. For example, your financial systems might require this
              as a reference for clearing payments.

          statement_definition_id: The UUID of the statement definition used when Bill statements are generated for
              the Account. If no statement definition is specified for the Account, the
              statement definition specified at Organizational level is used.

              Bill statements can be used as informative backing sheets to invoices. Based on
              the usage breakdown defined in the statement definition, generated statements
              give a breakdown of usage charges on Account Bills, which helps customers better
              understand usage charges incurred over the billing period.

              See
              [Working with Bill Statements](https://www.m3ter.com/docs/guides/running-viewing-and-managing-bills/working-with-bill-statements)
              in the m3ter documentation for more details.

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
        return await self._post(
            f"/organizations/{org_id}/accounts",
            body=await async_maybe_transform(
                {
                    "code": code,
                    "email_address": email_address,
                    "name": name,
                    "address": address,
                    "auto_generate_statement_mode": auto_generate_statement_mode,
                    "bill_epoch": bill_epoch,
                    "config_data": config_data,
                    "credit_application_order": credit_application_order,
                    "currency": currency,
                    "custom_fields": custom_fields,
                    "days_before_bill_due": days_before_bill_due,
                    "parent_account_id": parent_account_id,
                    "purchase_order_number": purchase_order_number,
                    "statement_definition_id": statement_definition_id,
                    "version": version,
                },
                account_create_params.AccountCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountResponse:
        """
        Retrieve the Account with the given Account UUID.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/organizations/{org_id}/accounts/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        code: str,
        email_address: str,
        name: str,
        address: AddressParam | Omit = omit,
        auto_generate_statement_mode: Literal["NONE", "JSON", "JSON_AND_CSV"] | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        config_data: Dict[str, object] | Omit = omit,
        credit_application_order: List[Literal["PREPAYMENT", "BALANCE"]] | Omit = omit,
        currency: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        days_before_bill_due: int | Omit = omit,
        parent_account_id: str | Omit = omit,
        purchase_order_number: str | Omit = omit,
        statement_definition_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountResponse:
        """
        Update the Account with the given Account UUID.

        **Note:** If you have created Custom Fields for an Account, when you use this
        endpoint to update the Account, use the `customFields` parameter to preserve
        those Custom Fields. If you omit them from the update request, they will be
        lost.

        Args:
          code: Code of the Account. This is a unique short code used for the Account.

          email_address: Contact email for the Account.

          name: Name of the Account.

          address: Contact address.

          auto_generate_statement_mode: Specify whether to auto-generate statements once Bills are approved or locked.

              - **None**. Statements will not be auto-generated.
              - **JSON**. Statements are auto-generated in JSON format.
              - **JSON and CSV**. Statements are auto-generated in both JSON and CSV formats.

          bill_epoch: Optional setting to define a _billing cycle date_, which sets the date of the
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

          config_data:
              Configuration data for the Account Supported settings:

              - SendBillsToThirdParties ("true"/"false")

          credit_application_order: Define the order in which any Prepayment or Balance amounts on the Account are
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

          currency:
              Account level billing currency, such as USD or GBP. Optional attribute:

              - If you define an Account currency, this will be used for bills.
              - If you do not define a currency, the billing currency defined at
                Organizational level will be used.

              **Note:** If you've attached a Plan to the Account that uses a different
              currency to the billing currency, then you must add the relevant currency
              conversion rate at Organization level to ensure the billing process can convert
              line items calculated using the Plan currency into the selected billing
              currency. If you don't add these conversion rates, then bills will fail for the
              Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          days_before_bill_due: Enter the number of days after the Bill generation date that you want to show on
              Bills as the due date.

              **Note:** If you define `daysBeforeBillDue` at individual Account level, this
              will take precedence over any `daysBeforeBillDue` setting defined at
              Organization level.

          parent_account_id: Parent Account ID, or null if this Account does not have a parent.

          purchase_order_number: Purchase Order Number of the Account.

              Optional attribute - allows you to set a purchase order number that comes
              through into invoicing. For example, your financial systems might require this
              as a reference for clearing payments.

          statement_definition_id: The UUID of the statement definition used when Bill statements are generated for
              the Account. If no statement definition is specified for the Account, the
              statement definition specified at Organizational level is used.

              Bill statements can be used as informative backing sheets to invoices. Based on
              the usage breakdown defined in the statement definition, generated statements
              give a breakdown of usage charges on Account Bills, which helps customers better
              understand usage charges incurred over the billing period.

              See
              [Working with Bill Statements](https://www.m3ter.com/docs/guides/running-viewing-and-managing-bills/working-with-bill-statements)
              in the m3ter documentation for more details.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/organizations/{org_id}/accounts/{id}",
            body=await async_maybe_transform(
                {
                    "code": code,
                    "email_address": email_address,
                    "name": name,
                    "address": address,
                    "auto_generate_statement_mode": auto_generate_statement_mode,
                    "bill_epoch": bill_epoch,
                    "config_data": config_data,
                    "credit_application_order": credit_application_order,
                    "currency": currency,
                    "custom_fields": custom_fields,
                    "days_before_bill_due": days_before_bill_due,
                    "parent_account_id": parent_account_id,
                    "purchase_order_number": purchase_order_number,
                    "statement_definition_id": statement_definition_id,
                    "version": version,
                },
                account_update_params.AccountUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        codes: SequenceNotStr[str] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[AccountResponse, AsyncCursor[AccountResponse]]:
        """
        Retrieve a list of Accounts that can be filtered by Account ID or Account Code.

        Args:
          codes: List of Account Codes to retrieve. These are unique short codes for each
              Account.

          ids: List of Account IDs to retrieve.

          next_token: `nextToken` for multi-page retrievals.

          page_size: Number of accounts to retrieve per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/accounts",
            page=AsyncCursor[AccountResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "codes": codes,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    account_list_params.AccountListParams,
                ),
            ),
            model=AccountResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountResponse:
        """Delete the Account with the given UUID.

        This may fail if there are any
        AccountPlans that reference the Account being deleted.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/organizations/{org_id}/accounts/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountResponse,
        )

    async def end_date_billing_entities(
        self,
        id: str,
        *,
        org_id: str | None = None,
        billing_entities: List[Literal["CONTRACT", "ACCOUNTPLAN", "PREPAYMENT", "PRICINGS", "COUNTER_PRICINGS"]],
        end_date: Union[str, datetime],
        apply_to_children: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountEndDateBillingEntitiesResponse:
        """
        Apply the specified end-date to billing entities associated with an Account.

        **NOTE:**

        - When you successfully end-date billing entities, the version number of each
          entity is incremented.

        Args:
          billing_entities: Defines which billing entities associated with the Account will have the
              specified end-date applied. For example, if you want the specified end-date to
              be applied to all Prepayments/Commitments created for the Account use
              `"PREPAYMENT"`.

          end_date: The end date and time applied to the specified billing entities _(in ISO 8601
              format)_.

          apply_to_children: A Boolean TRUE/FALSE flag. For Parent Accounts, set to TRUE if you want the
              specified end-date to be applied to any billing entities associated with Child
              Accounts. _(Optional)_

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/organizations/{org_id}/accounts/{id}/enddatebillingentities",
            body=await async_maybe_transform(
                {
                    "billing_entities": billing_entities,
                    "end_date": end_date,
                    "apply_to_children": apply_to_children,
                },
                account_end_date_billing_entities_params.AccountEndDateBillingEntitiesParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountEndDateBillingEntitiesResponse,
        )

    async def get_children(
        self,
        id: str,
        *,
        org_id: str | None = None,
        next_token: Optional[str] | Omit = omit,
        page_size: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountResponse:
        """
        Retrieve a list of Accounts that are children of the specified Account.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/organizations/{org_id}/accounts/{id}/children",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    account_get_children_params.AccountGetChildrenParams,
                ),
            ),
            cast_to=AccountResponse,
        )

    async def search(
        self,
        *,
        org_id: str | None = None,
        from_document: int | Omit = omit,
        operator: Literal["AND", "OR"] | Omit = omit,
        page_size: int | Omit = omit,
        search_query: str | Omit = omit,
        sort_by: str | Omit = omit,
        sort_order: Literal["ASC", "DESC"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountSearchResponse:
        """
        Search for Account entities.

        This endpoint executes a search query for Accounts based on the user specified
        search criteria. The search query is customizable, allowing for complex nested
        conditions and sorting. The returned list of Accounts can be paginated for
        easier management.

        Args:
          from_document: `fromDocument` for multi page retrievals.

          operator: Search Operator to be used while querying search.

          page_size: Number of Accounts to retrieve per page.

              **NOTE:** If not defined, default is 10.

          search_query:
              Query for data using special syntax:

              - Query parameters should be delimited using the $ (dollar sign).
              - Allowed comparators are:
                - (greater than) >
                - (greater than or equal to) >=
                - (equal to) :
                - (less than) <
                - (less than or equal to) <=
                - (match phrase/prefix) ~
              - Allowed parameters are: name, code, currency, purchaseOrderNumber,
                parentAccountId, codes, id, createdBy, dtCreated, lastModifiedBy, ids.
              - Query example:
                - searchQuery=name~Premium On$currency:USD.
                - This query is translated into: find accounts whose name contains the
                  phrase/prefix 'Premium On' AND the account currency is USD.

              **Note:** Using the ~ match phrase/prefix comparator. For best results, we
              recommend treating this as a "starts with" comparator for your search query.

          sort_by: Name of the parameter on which sorting is performed. Use any field available on
              the Account entity to sort by, such as `name`, `code`, and so on.

          sort_order: Sorting order.

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
            f"/organizations/{org_id}/accounts/search",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "from_document": from_document,
                        "operator": operator,
                        "page_size": page_size,
                        "search_query": search_query,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                    },
                    account_search_params.AccountSearchParams,
                ),
            ),
            cast_to=AccountSearchResponse,
        )


class AccountsResourceWithRawResponse:
    def __init__(self, accounts: AccountsResource) -> None:
        self._accounts = accounts

        self.create = to_raw_response_wrapper(
            accounts.create,
        )
        self.retrieve = to_raw_response_wrapper(
            accounts.retrieve,
        )
        self.update = to_raw_response_wrapper(
            accounts.update,
        )
        self.list = to_raw_response_wrapper(
            accounts.list,
        )
        self.delete = to_raw_response_wrapper(
            accounts.delete,
        )
        self.end_date_billing_entities = to_raw_response_wrapper(
            accounts.end_date_billing_entities,
        )
        self.get_children = to_raw_response_wrapper(
            accounts.get_children,
        )
        self.search = to_raw_response_wrapper(
            accounts.search,
        )


class AsyncAccountsResourceWithRawResponse:
    def __init__(self, accounts: AsyncAccountsResource) -> None:
        self._accounts = accounts

        self.create = async_to_raw_response_wrapper(
            accounts.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            accounts.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            accounts.update,
        )
        self.list = async_to_raw_response_wrapper(
            accounts.list,
        )
        self.delete = async_to_raw_response_wrapper(
            accounts.delete,
        )
        self.end_date_billing_entities = async_to_raw_response_wrapper(
            accounts.end_date_billing_entities,
        )
        self.get_children = async_to_raw_response_wrapper(
            accounts.get_children,
        )
        self.search = async_to_raw_response_wrapper(
            accounts.search,
        )


class AccountsResourceWithStreamingResponse:
    def __init__(self, accounts: AccountsResource) -> None:
        self._accounts = accounts

        self.create = to_streamed_response_wrapper(
            accounts.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            accounts.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            accounts.update,
        )
        self.list = to_streamed_response_wrapper(
            accounts.list,
        )
        self.delete = to_streamed_response_wrapper(
            accounts.delete,
        )
        self.end_date_billing_entities = to_streamed_response_wrapper(
            accounts.end_date_billing_entities,
        )
        self.get_children = to_streamed_response_wrapper(
            accounts.get_children,
        )
        self.search = to_streamed_response_wrapper(
            accounts.search,
        )


class AsyncAccountsResourceWithStreamingResponse:
    def __init__(self, accounts: AsyncAccountsResource) -> None:
        self._accounts = accounts

        self.create = async_to_streamed_response_wrapper(
            accounts.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            accounts.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            accounts.update,
        )
        self.list = async_to_streamed_response_wrapper(
            accounts.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            accounts.delete,
        )
        self.end_date_billing_entities = async_to_streamed_response_wrapper(
            accounts.end_date_billing_entities,
        )
        self.get_children = async_to_streamed_response_wrapper(
            accounts.get_children,
        )
        self.search = async_to_streamed_response_wrapper(
            accounts.search,
        )
