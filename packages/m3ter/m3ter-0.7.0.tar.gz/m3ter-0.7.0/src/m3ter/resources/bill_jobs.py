# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import date
from typing_extensions import Literal

import httpx

from ..types import bill_job_list_params, bill_job_create_params, bill_job_recalculate_params
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
from ..types.bill_job_response import BillJobResponse
from ..types.shared_params.currency_conversion import CurrencyConversion

__all__ = ["BillJobsResource", "AsyncBillJobsResource"]


class BillJobsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> BillJobsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return BillJobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BillJobsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return BillJobsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        account_ids: SequenceNotStr[str] | Omit = omit,
        bill_date: Union[str, date] | Omit = omit,
        bill_frequency_interval: int | Omit = omit,
        billing_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC"] | Omit = omit,
        currency_conversions: Iterable[CurrencyConversion] | Omit = omit,
        day_epoch: Union[str, date] | Omit = omit,
        due_date: Union[str, date] | Omit = omit,
        external_invoice_date: Union[str, date] | Omit = omit,
        last_date_in_billing_period: Union[str, date] | Omit = omit,
        month_epoch: Union[str, date] | Omit = omit,
        target_currency: str | Omit = omit,
        timezone: str | Omit = omit,
        version: int | Omit = omit,
        week_epoch: Union[str, date] | Omit = omit,
        year_epoch: Union[str, date] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillJobResponse:
        """
        Create a new BillJob to handle asynchronous bill calculations for a specific
        Organization.

        This operation allows you to initiate the processing of bills according to
        specified parameters. For example, create a BillJob to run only those bills
        where `billingFrequency` is `MONTHLY`. Note that if you want to run a BillJob
        for all billing frequencies, simply omit the `billingFrequency` request
        parameter.

        Once created, the BillJob's progress can be monitored:

        - In the Running Tasks panel in the m3ter Console - for more details, see
          [Running Bills Manually](https://www.m3ter.com/docs/guides/billing-and-usage-data/running-viewing-and-managing-bills/running-bills-and-viewing-bill-details#running-bills-manually)
        - Queried using the
          [List BillJobs](https://www.m3ter.com/docs/api#tag/BillJob/operation/ListBillJobs)
          operation.

        **NOTES:**

        - **Consolidated bills**. If you've already run billing with the Consolidate
          bills option disabled for your Organization but you then enable it, subsequent
          Bills for specific bill dates will now start afresh and not update earlier
          non-consolidated Bills for the same bill date. To avoid any billing conflicts,
          you might want to archive these earlier versions or delete them entirely.
        - **Maximum concurrent BillJobs**. If you already have 10 BillJobs currently
          running, and try to create another one, you'll get an HTTP 429 response (Too
          many requests). When one of the existing BillJobs has completed, you'll be
          able to submit another job

        Args:
          account_ids: An array of UUIDs representing the end customer Accounts associated with the
              BillJob.

          bill_date: The specific billing date _(in ISO 8601 format)_, determining when the Bill was
              generated.

              For example: `"2023-01-24"`.

          bill_frequency_interval: How often Bills are issued - used in conjunction with `billingFrequency`.

              For example, if `billingFrequency` is set to Monthly and `billFrequencyInterval`
              is set to 3, Bills are issued every three months.

          billing_frequency: How often Bills are generated.

              - **Daily**. Starting at midnight each day, covering a twenty-four hour period
                following.

              - **Weekly**. Starting at midnight on a Monday morning covering the seven-day
                period following.

              - **Monthly**. Starting at midnight on the morning of the first day of each
                month covering the entire calendar month following.

              - **Annually**. Starting at midnight on the morning of the first day of each
                year covering the entire calendar year following.

              - **Ad_Hoc**. Use this setting when a custom billing schedule is used for
                billing an Account, such as for billing of Prepayment/Commitment fees using a
                custom billing schedule.

          currency_conversions: An array of currency conversion rates from Bill currency to Organization
              currency. For example, if Account is billed in GBP and Organization is set to
              USD, Bill line items are calculated in GBP and then converted to USD using the
              defined rate.

          day_epoch: The starting date _(epoch)_ for Daily billing frequency _(in ISO 8601 format)_,
              determining the first Bill date for daily Bills.

          due_date: The due date _(in ISO 8601 format)_ for payment of the Bill.

              For example: `"2023-02-24"`.

          external_invoice_date: For accounting purposes, the date set at Organization level to use for external
              invoicing with respect to billing periods - two options:

              - `FIRST_DAY_OF_NEXT_PERIOD` _(Default)_. Used when you want to recognize usage
                revenue in the following period.
              - `LAST_DAY_OF_ARREARS`. Used when you want to recognize usage revenue in the
                same period that it's consumed, instead of in the following period.

              For example, if the retrieved Bill was on a monthly billing frequency and the
              billing period for the Bill is September 2023 and the _External invoice date_ is
              set at `FIRST_DAY_OF_NEXT_PERIOD`, then the `externalInvoiceDate` will be
              `"2023-10-01"`.

              **NOTE:** To change the `externalInvoiceDate` setting for your Organization, you
              can use the
              [Update OrganizationConfig](https://www.m3ter.com/docs/api#tag/OrganizationConfig/operation/GetOrganizationConfig)
              call.

          last_date_in_billing_period: Specifies the date _(in ISO 8601 format)_ of the last day in the billing period,
              defining the time range for the associated Bills.

              For example: `"2023-03-24"`.

          month_epoch: The starting date _(epoch)_ for Monthly billing frequency _(in ISO 8601
              format)_, determining the first Bill date for monthly Bills.

          target_currency: The currency code used for the Bill, such as USD, GBP, or EUR.

          timezone: Specifies the time zone used for the generated Bills, ensuring alignment with
              the local time zone.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          week_epoch: The starting date _(epoch)_ for Weekly billing frequency _(in ISO 8601 format)_,
              determining the first Bill date for weekly Bills.

          year_epoch: The starting date _(epoch)_ for Yearly billing frequency _(in ISO 8601 format)_,
              determining the first Bill date for yearly Bills.

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
            f"/organizations/{org_id}/billjobs",
            body=maybe_transform(
                {
                    "account_ids": account_ids,
                    "bill_date": bill_date,
                    "bill_frequency_interval": bill_frequency_interval,
                    "billing_frequency": billing_frequency,
                    "currency_conversions": currency_conversions,
                    "day_epoch": day_epoch,
                    "due_date": due_date,
                    "external_invoice_date": external_invoice_date,
                    "last_date_in_billing_period": last_date_in_billing_period,
                    "month_epoch": month_epoch,
                    "target_currency": target_currency,
                    "timezone": timezone,
                    "version": version,
                    "week_epoch": week_epoch,
                    "year_epoch": year_epoch,
                },
                bill_job_create_params.BillJobCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillJobResponse,
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
    ) -> BillJobResponse:
        """
        Retrieve a Bill Job for the given UUID.

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
            f"/organizations/{org_id}/billjobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillJobResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        active: str | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        status: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[BillJobResponse]:
        """
        Retrieve a list of BillJobs.

        This endpoint retrieves a list of BillJobs for a specified organization. The
        list can be paginated for easier management, and allows you to query and filter
        based on various parameters, such as BillJob `status` and whether or not BillJob
        remains `active`.

        Args:
          active: Boolean filter to retrieve only active BillJobs and exclude completed or
              cancelled BillJobs from the results.

              - TRUE - only active BillJobs.
              - FALSE - all BillJobs including completed and cancelled BillJobs.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              BillJobs in a paginated list.

          page_size: Specifies the maximum number of BillJobs to retrieve per page.

          status: Filter BillJobs by specific status. Allows for targeted retrieval of BillJobs
              based on their current processing status.

              Possible states are:

              - PENDING
              - INITIALIZING
              - RUNNING
              - COMPLETE
              - CANCELLED

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
            f"/organizations/{org_id}/billjobs",
            page=SyncCursor[BillJobResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "active": active,
                        "next_token": next_token,
                        "page_size": page_size,
                        "status": status,
                    },
                    bill_job_list_params.BillJobListParams,
                ),
            ),
            model=BillJobResponse,
        )

    def cancel(
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
    ) -> BillJobResponse:
        """
        Cancel an ongoing BillJob for the given Organization and BillJob UUID.

        This endpoint allows you to halt the processing of a specific BillJob, which
        might be necessary if there are changes in billing requirements or other
        operational considerations.

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
        return self._post(
            f"/organizations/{org_id}/billjobs/{id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillJobResponse,
        )

    def recalculate(
        self,
        *,
        org_id: str | None = None,
        bill_ids: SequenceNotStr[str],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillJobResponse:
        """
        Create a new BillJob specifically to recalculate existing bills for a given
        Organization.

        This operation is essential when adjustments or corrections are required in
        previously calculated bills. The recalculated bills when the BillJob is complete
        can be checked in the m3ter Console Bill Management page or queried by using the
        [List Bills](https://www.m3ter.com/docs/api#tag/Bill/operation/ListBills)
        operation.

        **NOTE:**

        - **Response Schema**. The response schema for this call is dynamic. This means
          that the response might not contain all of the parameters listed. If set to
          null,the parameter is hidden to help simplify the output as well as to reduce
          its size and improve performance.

        Args:
          bill_ids: The array of unique identifiers (UUIDs) for the Bills which are to be
              recalculated.

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
            f"/organizations/{org_id}/billjobs/recalculate",
            body=maybe_transform(
                {
                    "bill_ids": bill_ids,
                    "version": version,
                },
                bill_job_recalculate_params.BillJobRecalculateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillJobResponse,
        )


class AsyncBillJobsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncBillJobsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncBillJobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBillJobsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncBillJobsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        account_ids: SequenceNotStr[str] | Omit = omit,
        bill_date: Union[str, date] | Omit = omit,
        bill_frequency_interval: int | Omit = omit,
        billing_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC"] | Omit = omit,
        currency_conversions: Iterable[CurrencyConversion] | Omit = omit,
        day_epoch: Union[str, date] | Omit = omit,
        due_date: Union[str, date] | Omit = omit,
        external_invoice_date: Union[str, date] | Omit = omit,
        last_date_in_billing_period: Union[str, date] | Omit = omit,
        month_epoch: Union[str, date] | Omit = omit,
        target_currency: str | Omit = omit,
        timezone: str | Omit = omit,
        version: int | Omit = omit,
        week_epoch: Union[str, date] | Omit = omit,
        year_epoch: Union[str, date] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillJobResponse:
        """
        Create a new BillJob to handle asynchronous bill calculations for a specific
        Organization.

        This operation allows you to initiate the processing of bills according to
        specified parameters. For example, create a BillJob to run only those bills
        where `billingFrequency` is `MONTHLY`. Note that if you want to run a BillJob
        for all billing frequencies, simply omit the `billingFrequency` request
        parameter.

        Once created, the BillJob's progress can be monitored:

        - In the Running Tasks panel in the m3ter Console - for more details, see
          [Running Bills Manually](https://www.m3ter.com/docs/guides/billing-and-usage-data/running-viewing-and-managing-bills/running-bills-and-viewing-bill-details#running-bills-manually)
        - Queried using the
          [List BillJobs](https://www.m3ter.com/docs/api#tag/BillJob/operation/ListBillJobs)
          operation.

        **NOTES:**

        - **Consolidated bills**. If you've already run billing with the Consolidate
          bills option disabled for your Organization but you then enable it, subsequent
          Bills for specific bill dates will now start afresh and not update earlier
          non-consolidated Bills for the same bill date. To avoid any billing conflicts,
          you might want to archive these earlier versions or delete them entirely.
        - **Maximum concurrent BillJobs**. If you already have 10 BillJobs currently
          running, and try to create another one, you'll get an HTTP 429 response (Too
          many requests). When one of the existing BillJobs has completed, you'll be
          able to submit another job

        Args:
          account_ids: An array of UUIDs representing the end customer Accounts associated with the
              BillJob.

          bill_date: The specific billing date _(in ISO 8601 format)_, determining when the Bill was
              generated.

              For example: `"2023-01-24"`.

          bill_frequency_interval: How often Bills are issued - used in conjunction with `billingFrequency`.

              For example, if `billingFrequency` is set to Monthly and `billFrequencyInterval`
              is set to 3, Bills are issued every three months.

          billing_frequency: How often Bills are generated.

              - **Daily**. Starting at midnight each day, covering a twenty-four hour period
                following.

              - **Weekly**. Starting at midnight on a Monday morning covering the seven-day
                period following.

              - **Monthly**. Starting at midnight on the morning of the first day of each
                month covering the entire calendar month following.

              - **Annually**. Starting at midnight on the morning of the first day of each
                year covering the entire calendar year following.

              - **Ad_Hoc**. Use this setting when a custom billing schedule is used for
                billing an Account, such as for billing of Prepayment/Commitment fees using a
                custom billing schedule.

          currency_conversions: An array of currency conversion rates from Bill currency to Organization
              currency. For example, if Account is billed in GBP and Organization is set to
              USD, Bill line items are calculated in GBP and then converted to USD using the
              defined rate.

          day_epoch: The starting date _(epoch)_ for Daily billing frequency _(in ISO 8601 format)_,
              determining the first Bill date for daily Bills.

          due_date: The due date _(in ISO 8601 format)_ for payment of the Bill.

              For example: `"2023-02-24"`.

          external_invoice_date: For accounting purposes, the date set at Organization level to use for external
              invoicing with respect to billing periods - two options:

              - `FIRST_DAY_OF_NEXT_PERIOD` _(Default)_. Used when you want to recognize usage
                revenue in the following period.
              - `LAST_DAY_OF_ARREARS`. Used when you want to recognize usage revenue in the
                same period that it's consumed, instead of in the following period.

              For example, if the retrieved Bill was on a monthly billing frequency and the
              billing period for the Bill is September 2023 and the _External invoice date_ is
              set at `FIRST_DAY_OF_NEXT_PERIOD`, then the `externalInvoiceDate` will be
              `"2023-10-01"`.

              **NOTE:** To change the `externalInvoiceDate` setting for your Organization, you
              can use the
              [Update OrganizationConfig](https://www.m3ter.com/docs/api#tag/OrganizationConfig/operation/GetOrganizationConfig)
              call.

          last_date_in_billing_period: Specifies the date _(in ISO 8601 format)_ of the last day in the billing period,
              defining the time range for the associated Bills.

              For example: `"2023-03-24"`.

          month_epoch: The starting date _(epoch)_ for Monthly billing frequency _(in ISO 8601
              format)_, determining the first Bill date for monthly Bills.

          target_currency: The currency code used for the Bill, such as USD, GBP, or EUR.

          timezone: Specifies the time zone used for the generated Bills, ensuring alignment with
              the local time zone.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          week_epoch: The starting date _(epoch)_ for Weekly billing frequency _(in ISO 8601 format)_,
              determining the first Bill date for weekly Bills.

          year_epoch: The starting date _(epoch)_ for Yearly billing frequency _(in ISO 8601 format)_,
              determining the first Bill date for yearly Bills.

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
            f"/organizations/{org_id}/billjobs",
            body=await async_maybe_transform(
                {
                    "account_ids": account_ids,
                    "bill_date": bill_date,
                    "bill_frequency_interval": bill_frequency_interval,
                    "billing_frequency": billing_frequency,
                    "currency_conversions": currency_conversions,
                    "day_epoch": day_epoch,
                    "due_date": due_date,
                    "external_invoice_date": external_invoice_date,
                    "last_date_in_billing_period": last_date_in_billing_period,
                    "month_epoch": month_epoch,
                    "target_currency": target_currency,
                    "timezone": timezone,
                    "version": version,
                    "week_epoch": week_epoch,
                    "year_epoch": year_epoch,
                },
                bill_job_create_params.BillJobCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillJobResponse,
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
    ) -> BillJobResponse:
        """
        Retrieve a Bill Job for the given UUID.

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
            f"/organizations/{org_id}/billjobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillJobResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        active: str | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        status: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[BillJobResponse, AsyncCursor[BillJobResponse]]:
        """
        Retrieve a list of BillJobs.

        This endpoint retrieves a list of BillJobs for a specified organization. The
        list can be paginated for easier management, and allows you to query and filter
        based on various parameters, such as BillJob `status` and whether or not BillJob
        remains `active`.

        Args:
          active: Boolean filter to retrieve only active BillJobs and exclude completed or
              cancelled BillJobs from the results.

              - TRUE - only active BillJobs.
              - FALSE - all BillJobs including completed and cancelled BillJobs.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              BillJobs in a paginated list.

          page_size: Specifies the maximum number of BillJobs to retrieve per page.

          status: Filter BillJobs by specific status. Allows for targeted retrieval of BillJobs
              based on their current processing status.

              Possible states are:

              - PENDING
              - INITIALIZING
              - RUNNING
              - COMPLETE
              - CANCELLED

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
            f"/organizations/{org_id}/billjobs",
            page=AsyncCursor[BillJobResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "active": active,
                        "next_token": next_token,
                        "page_size": page_size,
                        "status": status,
                    },
                    bill_job_list_params.BillJobListParams,
                ),
            ),
            model=BillJobResponse,
        )

    async def cancel(
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
    ) -> BillJobResponse:
        """
        Cancel an ongoing BillJob for the given Organization and BillJob UUID.

        This endpoint allows you to halt the processing of a specific BillJob, which
        might be necessary if there are changes in billing requirements or other
        operational considerations.

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
        return await self._post(
            f"/organizations/{org_id}/billjobs/{id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillJobResponse,
        )

    async def recalculate(
        self,
        *,
        org_id: str | None = None,
        bill_ids: SequenceNotStr[str],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillJobResponse:
        """
        Create a new BillJob specifically to recalculate existing bills for a given
        Organization.

        This operation is essential when adjustments or corrections are required in
        previously calculated bills. The recalculated bills when the BillJob is complete
        can be checked in the m3ter Console Bill Management page or queried by using the
        [List Bills](https://www.m3ter.com/docs/api#tag/Bill/operation/ListBills)
        operation.

        **NOTE:**

        - **Response Schema**. The response schema for this call is dynamic. This means
          that the response might not contain all of the parameters listed. If set to
          null,the parameter is hidden to help simplify the output as well as to reduce
          its size and improve performance.

        Args:
          bill_ids: The array of unique identifiers (UUIDs) for the Bills which are to be
              recalculated.

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
            f"/organizations/{org_id}/billjobs/recalculate",
            body=await async_maybe_transform(
                {
                    "bill_ids": bill_ids,
                    "version": version,
                },
                bill_job_recalculate_params.BillJobRecalculateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillJobResponse,
        )


class BillJobsResourceWithRawResponse:
    def __init__(self, bill_jobs: BillJobsResource) -> None:
        self._bill_jobs = bill_jobs

        self.create = to_raw_response_wrapper(
            bill_jobs.create,
        )
        self.retrieve = to_raw_response_wrapper(
            bill_jobs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            bill_jobs.list,
        )
        self.cancel = to_raw_response_wrapper(
            bill_jobs.cancel,
        )
        self.recalculate = to_raw_response_wrapper(
            bill_jobs.recalculate,
        )


class AsyncBillJobsResourceWithRawResponse:
    def __init__(self, bill_jobs: AsyncBillJobsResource) -> None:
        self._bill_jobs = bill_jobs

        self.create = async_to_raw_response_wrapper(
            bill_jobs.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            bill_jobs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            bill_jobs.list,
        )
        self.cancel = async_to_raw_response_wrapper(
            bill_jobs.cancel,
        )
        self.recalculate = async_to_raw_response_wrapper(
            bill_jobs.recalculate,
        )


class BillJobsResourceWithStreamingResponse:
    def __init__(self, bill_jobs: BillJobsResource) -> None:
        self._bill_jobs = bill_jobs

        self.create = to_streamed_response_wrapper(
            bill_jobs.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            bill_jobs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            bill_jobs.list,
        )
        self.cancel = to_streamed_response_wrapper(
            bill_jobs.cancel,
        )
        self.recalculate = to_streamed_response_wrapper(
            bill_jobs.recalculate,
        )


class AsyncBillJobsResourceWithStreamingResponse:
    def __init__(self, bill_jobs: AsyncBillJobsResource) -> None:
        self._bill_jobs = bill_jobs

        self.create = async_to_streamed_response_wrapper(
            bill_jobs.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            bill_jobs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            bill_jobs.list,
        )
        self.cancel = async_to_streamed_response_wrapper(
            bill_jobs.cancel,
        )
        self.recalculate = async_to_streamed_response_wrapper(
            bill_jobs.recalculate,
        )
