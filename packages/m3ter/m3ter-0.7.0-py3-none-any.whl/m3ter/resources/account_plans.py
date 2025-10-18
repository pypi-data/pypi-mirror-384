# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from datetime import date, datetime
from typing_extensions import Literal

import httpx

from ..types import account_plan_list_params, account_plan_create_params, account_plan_update_params
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
from ..types.account_plan_response import AccountPlanResponse

__all__ = ["AccountPlansResource", "AsyncAccountPlansResource"]


class AccountPlansResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AccountPlansResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AccountPlansResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AccountPlansResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AccountPlansResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        start_date: Union[str, datetime],
        bill_epoch: Union[str, date] | Omit = omit,
        child_billing_mode: Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"] | Omit = omit,
        code: str | Omit = omit,
        contract_id: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        plan_group_id: str | Omit = omit,
        plan_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountPlanResponse:
        """
        Create a new AccountPlan or AccountPlanGroup.

        This endpoint creates a new AccountPlan or AccountPlanGroup for a specific
        Account in your Organization. The details of the new AccountPlan or
        AccountPlanGroup should be supplied in the request body.

        **Note:** You cannot use this call to create _both_ an AccountPlan and
        AccountPlanGroup for an Account at the same time. If you want to create both for
        an Account, you must submit two separate calls.

        Args:
          account_id: The unique identifier (UUID) for the Account.

          start_date: The start date _(in ISO-8601 format)_ for the AccountPlan or AccountPlanGroup
              becoming active for the Account.

          bill_epoch: Optional setting to define a _billing cycle date_, which acts as a reference for
              when in the applied billing frequency period bills are created:

              - For example, if you attach a Plan to an Account where the Plan is configured
                for monthly billing frequency and you've defined the period the Plan will
                apply to the Account to be from January 1st, 2022 until January 1st, 2023. You
                then set a `billEpoch` date of February 15th, 2022. The first Bill will be
                created for the Account on February 15th, and subsequent Bills created on the
                15th of the months following for the remainder of the billing period - March
                15th, April 15th, and so on.
              - If not defined, then the `billEpoch` date set for the Account will be used
                instead.
              - The date is in ISO-8601 format.

          child_billing_mode: If the Account is either a Parent or a Child Account, this specifies the Account
              hierarchy billing mode. The mode determines how billing will be handled and
              shown on bills for charges due on the Parent Account, and charges due on Child
              Accounts:

              - **Parent Breakdown** - a separate bill line item per Account. Default setting.

              - **Parent Summary** - single bill line item for all Accounts.

              - **Child** - the Child Account is billed.

          code: A unique short code for the AccountPlan or AccountPlanGroup.

          contract_id: The unique identifier (UUID) for a Contract to which you want to add the Plan or
              Plan Group being attached to the Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          end_date: The end date _(in ISO-8601 format)_ for when the AccountPlan or AccountPlanGroup
              ceases to be active for the Account. If not specified, the AccountPlan or
              AccountPlanGroup remains active indefinitely.

          plan_group_id: The unique identifier (UUID) of the PlanGroup to be attached to the Account to
              create an AccountPlanGroup.

              **Note:** Exclusive of the `planId` request parameter - exactly one of `planId`
              or `planGroupId` must be used per call.

          plan_id: The unique identifier (UUID) of the Plan to be attached to the Account to create
              an AccountPlan.

              **Note:** Exclusive of the `planGroupId` request parameter - exactly one of
              `planId` or `planGroupId` must be used per call.

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
            f"/organizations/{org_id}/accountplans",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "start_date": start_date,
                    "bill_epoch": bill_epoch,
                    "child_billing_mode": child_billing_mode,
                    "code": code,
                    "contract_id": contract_id,
                    "custom_fields": custom_fields,
                    "end_date": end_date,
                    "plan_group_id": plan_group_id,
                    "plan_id": plan_id,
                    "version": version,
                },
                account_plan_create_params.AccountPlanCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountPlanResponse,
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
    ) -> AccountPlanResponse:
        """
        Retrieve the AccountPlan or AccountPlanGroup details corresponding to the given
        UUID.

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
            f"/organizations/{org_id}/accountplans/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountPlanResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        start_date: Union[str, datetime],
        bill_epoch: Union[str, date] | Omit = omit,
        child_billing_mode: Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"] | Omit = omit,
        code: str | Omit = omit,
        contract_id: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        plan_group_id: str | Omit = omit,
        plan_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountPlanResponse:
        """
        Update the AccountPlan or AccountPlanGroup with the given UUID.

        This endpoint updates a new AccountPlan or AccountPlanGroup for a specific
        Account in your Organization. The updated information should be provided in the
        request body.

        **Notes:**

        - You cannot use this call to update _both_ an AccountPlan and AccountPlanGroup
          for an Account at the same time. If you want to update an AccounPlan and an
          AccountPlanGroup attached to an Account, you must submit two separate calls.
        - If you have created Custom Fields for an AccountPlan, when you use this
          endpoint to update the AccountPlan use the `customFields` parameter to
          preserve those Custom Fields. If you omit them from the update request, they
          will be lost.

        Args:
          account_id: The unique identifier (UUID) for the Account.

          start_date: The start date _(in ISO-8601 format)_ for the AccountPlan or AccountPlanGroup
              becoming active for the Account.

          bill_epoch: Optional setting to define a _billing cycle date_, which acts as a reference for
              when in the applied billing frequency period bills are created:

              - For example, if you attach a Plan to an Account where the Plan is configured
                for monthly billing frequency and you've defined the period the Plan will
                apply to the Account to be from January 1st, 2022 until January 1st, 2023. You
                then set a `billEpoch` date of February 15th, 2022. The first Bill will be
                created for the Account on February 15th, and subsequent Bills created on the
                15th of the months following for the remainder of the billing period - March
                15th, April 15th, and so on.
              - If not defined, then the `billEpoch` date set for the Account will be used
                instead.
              - The date is in ISO-8601 format.

          child_billing_mode: If the Account is either a Parent or a Child Account, this specifies the Account
              hierarchy billing mode. The mode determines how billing will be handled and
              shown on bills for charges due on the Parent Account, and charges due on Child
              Accounts:

              - **Parent Breakdown** - a separate bill line item per Account. Default setting.

              - **Parent Summary** - single bill line item for all Accounts.

              - **Child** - the Child Account is billed.

          code: A unique short code for the AccountPlan or AccountPlanGroup.

          contract_id: The unique identifier (UUID) for a Contract to which you want to add the Plan or
              Plan Group being attached to the Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          end_date: The end date _(in ISO-8601 format)_ for when the AccountPlan or AccountPlanGroup
              ceases to be active for the Account. If not specified, the AccountPlan or
              AccountPlanGroup remains active indefinitely.

          plan_group_id: The unique identifier (UUID) of the PlanGroup to be attached to the Account to
              create an AccountPlanGroup.

              **Note:** Exclusive of the `planId` request parameter - exactly one of `planId`
              or `planGroupId` must be used per call.

          plan_id: The unique identifier (UUID) of the Plan to be attached to the Account to create
              an AccountPlan.

              **Note:** Exclusive of the `planGroupId` request parameter - exactly one of
              `planId` or `planGroupId` must be used per call.

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
            f"/organizations/{org_id}/accountplans/{id}",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "start_date": start_date,
                    "bill_epoch": bill_epoch,
                    "child_billing_mode": child_billing_mode,
                    "code": code,
                    "contract_id": contract_id,
                    "custom_fields": custom_fields,
                    "end_date": end_date,
                    "plan_group_id": plan_group_id,
                    "plan_id": plan_id,
                    "version": version,
                },
                account_plan_update_params.AccountPlanUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountPlanResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account: str | Omit = omit,
        contract: Optional[str] | Omit = omit,
        date: str | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        includeall: bool | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        plan: str | Omit = omit,
        product: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[AccountPlanResponse]:
        """
        Retrieves a list of AccountPlan and AccountPlanGroup entities for the specified
        Organization. The list can be paginated for easier management, and supports
        filtering with various query parameters.

        Args:
          account: The unique identifier (UUID) for the Account whose AccountPlans and
              AccountPlanGroups you want to retrieve.

              **NOTE:** Only returns the currently active AccountPlans and AccountPlanGroups
              for the specified Account. Use in combination with the `includeall` query
              parameter to return both active and inactive.

          contract: The unique identifier (UUID) of the Contract which the AccountPlans you want to
              retrieve have been linked to.

              **NOTE:** Does not return AccountPlanGroups that have been linked to the
              Contract.

          date: The specific date for which you want to retrieve AccountPlans and
              AccountPlanGroups.

              **NOTE:** Returns both active and inactive AccountPlans and AccountPlanGroups
              for the specified date.

          ids: A list of unique identifiers (UUIDs) for specific AccountPlans and
              AccountPlanGroups you want to retrieve.

          includeall: A Boolean flag that specifies whether to include both active and inactive
              AccountPlans and AccountPlanGroups in the list.

              - **TRUE** - both active and inactive AccountPlans and AccountPlanGroups are
                included in the list.
              - **FALSE** - only active AccountPlans and AccountPlanGroups are retrieved in
                the list.

          next_token: The `nextToken` for retrieving the next page of AccountPlans and
              AccountPlanGroups. It is used to fetch the next page of AccountPlans and
              AccountPlanGroups in a paginated list.

          page_size: The maximum number of AccountPlans and AccountPlanGroups to return per page.

          plan: The unique identifier (UUID) for the Plan whose associated AccountPlans you want
              to retrieve.

              **NOTE:** Does not return AccountPlanGroups if you use a `planGroupId`.

          product: The unique identifier (UUID) for the Product whose associated AccountPlans you
              want to retrieve.

              **NOTE:** You cannot use the `product` query parameter as a single filter
              condition, but must always use it in combination with the `account` query
              parameter.

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
            f"/organizations/{org_id}/accountplans",
            page=SyncCursor[AccountPlanResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account": account,
                        "contract": contract,
                        "date": date,
                        "ids": ids,
                        "includeall": includeall,
                        "next_token": next_token,
                        "page_size": page_size,
                        "plan": plan,
                        "product": product,
                    },
                    account_plan_list_params.AccountPlanListParams,
                ),
            ),
            model=AccountPlanResponse,
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
    ) -> AccountPlanResponse:
        """
        Delete the AccountPlan or AccountPlanGroup with the given UUID.

        This endpoint deletes an AccountPlan or AccountPlanGroup that has been attached
        to a specific Account in your Organization.

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
            f"/organizations/{org_id}/accountplans/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountPlanResponse,
        )


class AsyncAccountPlansResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAccountPlansResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAccountPlansResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAccountPlansResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncAccountPlansResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        start_date: Union[str, datetime],
        bill_epoch: Union[str, date] | Omit = omit,
        child_billing_mode: Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"] | Omit = omit,
        code: str | Omit = omit,
        contract_id: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        plan_group_id: str | Omit = omit,
        plan_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountPlanResponse:
        """
        Create a new AccountPlan or AccountPlanGroup.

        This endpoint creates a new AccountPlan or AccountPlanGroup for a specific
        Account in your Organization. The details of the new AccountPlan or
        AccountPlanGroup should be supplied in the request body.

        **Note:** You cannot use this call to create _both_ an AccountPlan and
        AccountPlanGroup for an Account at the same time. If you want to create both for
        an Account, you must submit two separate calls.

        Args:
          account_id: The unique identifier (UUID) for the Account.

          start_date: The start date _(in ISO-8601 format)_ for the AccountPlan or AccountPlanGroup
              becoming active for the Account.

          bill_epoch: Optional setting to define a _billing cycle date_, which acts as a reference for
              when in the applied billing frequency period bills are created:

              - For example, if you attach a Plan to an Account where the Plan is configured
                for monthly billing frequency and you've defined the period the Plan will
                apply to the Account to be from January 1st, 2022 until January 1st, 2023. You
                then set a `billEpoch` date of February 15th, 2022. The first Bill will be
                created for the Account on February 15th, and subsequent Bills created on the
                15th of the months following for the remainder of the billing period - March
                15th, April 15th, and so on.
              - If not defined, then the `billEpoch` date set for the Account will be used
                instead.
              - The date is in ISO-8601 format.

          child_billing_mode: If the Account is either a Parent or a Child Account, this specifies the Account
              hierarchy billing mode. The mode determines how billing will be handled and
              shown on bills for charges due on the Parent Account, and charges due on Child
              Accounts:

              - **Parent Breakdown** - a separate bill line item per Account. Default setting.

              - **Parent Summary** - single bill line item for all Accounts.

              - **Child** - the Child Account is billed.

          code: A unique short code for the AccountPlan or AccountPlanGroup.

          contract_id: The unique identifier (UUID) for a Contract to which you want to add the Plan or
              Plan Group being attached to the Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          end_date: The end date _(in ISO-8601 format)_ for when the AccountPlan or AccountPlanGroup
              ceases to be active for the Account. If not specified, the AccountPlan or
              AccountPlanGroup remains active indefinitely.

          plan_group_id: The unique identifier (UUID) of the PlanGroup to be attached to the Account to
              create an AccountPlanGroup.

              **Note:** Exclusive of the `planId` request parameter - exactly one of `planId`
              or `planGroupId` must be used per call.

          plan_id: The unique identifier (UUID) of the Plan to be attached to the Account to create
              an AccountPlan.

              **Note:** Exclusive of the `planGroupId` request parameter - exactly one of
              `planId` or `planGroupId` must be used per call.

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
            f"/organizations/{org_id}/accountplans",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "start_date": start_date,
                    "bill_epoch": bill_epoch,
                    "child_billing_mode": child_billing_mode,
                    "code": code,
                    "contract_id": contract_id,
                    "custom_fields": custom_fields,
                    "end_date": end_date,
                    "plan_group_id": plan_group_id,
                    "plan_id": plan_id,
                    "version": version,
                },
                account_plan_create_params.AccountPlanCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountPlanResponse,
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
    ) -> AccountPlanResponse:
        """
        Retrieve the AccountPlan or AccountPlanGroup details corresponding to the given
        UUID.

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
            f"/organizations/{org_id}/accountplans/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountPlanResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        start_date: Union[str, datetime],
        bill_epoch: Union[str, date] | Omit = omit,
        child_billing_mode: Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"] | Omit = omit,
        code: str | Omit = omit,
        contract_id: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        plan_group_id: str | Omit = omit,
        plan_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountPlanResponse:
        """
        Update the AccountPlan or AccountPlanGroup with the given UUID.

        This endpoint updates a new AccountPlan or AccountPlanGroup for a specific
        Account in your Organization. The updated information should be provided in the
        request body.

        **Notes:**

        - You cannot use this call to update _both_ an AccountPlan and AccountPlanGroup
          for an Account at the same time. If you want to update an AccounPlan and an
          AccountPlanGroup attached to an Account, you must submit two separate calls.
        - If you have created Custom Fields for an AccountPlan, when you use this
          endpoint to update the AccountPlan use the `customFields` parameter to
          preserve those Custom Fields. If you omit them from the update request, they
          will be lost.

        Args:
          account_id: The unique identifier (UUID) for the Account.

          start_date: The start date _(in ISO-8601 format)_ for the AccountPlan or AccountPlanGroup
              becoming active for the Account.

          bill_epoch: Optional setting to define a _billing cycle date_, which acts as a reference for
              when in the applied billing frequency period bills are created:

              - For example, if you attach a Plan to an Account where the Plan is configured
                for monthly billing frequency and you've defined the period the Plan will
                apply to the Account to be from January 1st, 2022 until January 1st, 2023. You
                then set a `billEpoch` date of February 15th, 2022. The first Bill will be
                created for the Account on February 15th, and subsequent Bills created on the
                15th of the months following for the remainder of the billing period - March
                15th, April 15th, and so on.
              - If not defined, then the `billEpoch` date set for the Account will be used
                instead.
              - The date is in ISO-8601 format.

          child_billing_mode: If the Account is either a Parent or a Child Account, this specifies the Account
              hierarchy billing mode. The mode determines how billing will be handled and
              shown on bills for charges due on the Parent Account, and charges due on Child
              Accounts:

              - **Parent Breakdown** - a separate bill line item per Account. Default setting.

              - **Parent Summary** - single bill line item for all Accounts.

              - **Child** - the Child Account is billed.

          code: A unique short code for the AccountPlan or AccountPlanGroup.

          contract_id: The unique identifier (UUID) for a Contract to which you want to add the Plan or
              Plan Group being attached to the Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          end_date: The end date _(in ISO-8601 format)_ for when the AccountPlan or AccountPlanGroup
              ceases to be active for the Account. If not specified, the AccountPlan or
              AccountPlanGroup remains active indefinitely.

          plan_group_id: The unique identifier (UUID) of the PlanGroup to be attached to the Account to
              create an AccountPlanGroup.

              **Note:** Exclusive of the `planId` request parameter - exactly one of `planId`
              or `planGroupId` must be used per call.

          plan_id: The unique identifier (UUID) of the Plan to be attached to the Account to create
              an AccountPlan.

              **Note:** Exclusive of the `planGroupId` request parameter - exactly one of
              `planId` or `planGroupId` must be used per call.

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
            f"/organizations/{org_id}/accountplans/{id}",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "start_date": start_date,
                    "bill_epoch": bill_epoch,
                    "child_billing_mode": child_billing_mode,
                    "code": code,
                    "contract_id": contract_id,
                    "custom_fields": custom_fields,
                    "end_date": end_date,
                    "plan_group_id": plan_group_id,
                    "plan_id": plan_id,
                    "version": version,
                },
                account_plan_update_params.AccountPlanUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountPlanResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account: str | Omit = omit,
        contract: Optional[str] | Omit = omit,
        date: str | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        includeall: bool | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        plan: str | Omit = omit,
        product: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[AccountPlanResponse, AsyncCursor[AccountPlanResponse]]:
        """
        Retrieves a list of AccountPlan and AccountPlanGroup entities for the specified
        Organization. The list can be paginated for easier management, and supports
        filtering with various query parameters.

        Args:
          account: The unique identifier (UUID) for the Account whose AccountPlans and
              AccountPlanGroups you want to retrieve.

              **NOTE:** Only returns the currently active AccountPlans and AccountPlanGroups
              for the specified Account. Use in combination with the `includeall` query
              parameter to return both active and inactive.

          contract: The unique identifier (UUID) of the Contract which the AccountPlans you want to
              retrieve have been linked to.

              **NOTE:** Does not return AccountPlanGroups that have been linked to the
              Contract.

          date: The specific date for which you want to retrieve AccountPlans and
              AccountPlanGroups.

              **NOTE:** Returns both active and inactive AccountPlans and AccountPlanGroups
              for the specified date.

          ids: A list of unique identifiers (UUIDs) for specific AccountPlans and
              AccountPlanGroups you want to retrieve.

          includeall: A Boolean flag that specifies whether to include both active and inactive
              AccountPlans and AccountPlanGroups in the list.

              - **TRUE** - both active and inactive AccountPlans and AccountPlanGroups are
                included in the list.
              - **FALSE** - only active AccountPlans and AccountPlanGroups are retrieved in
                the list.

          next_token: The `nextToken` for retrieving the next page of AccountPlans and
              AccountPlanGroups. It is used to fetch the next page of AccountPlans and
              AccountPlanGroups in a paginated list.

          page_size: The maximum number of AccountPlans and AccountPlanGroups to return per page.

          plan: The unique identifier (UUID) for the Plan whose associated AccountPlans you want
              to retrieve.

              **NOTE:** Does not return AccountPlanGroups if you use a `planGroupId`.

          product: The unique identifier (UUID) for the Product whose associated AccountPlans you
              want to retrieve.

              **NOTE:** You cannot use the `product` query parameter as a single filter
              condition, but must always use it in combination with the `account` query
              parameter.

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
            f"/organizations/{org_id}/accountplans",
            page=AsyncCursor[AccountPlanResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account": account,
                        "contract": contract,
                        "date": date,
                        "ids": ids,
                        "includeall": includeall,
                        "next_token": next_token,
                        "page_size": page_size,
                        "plan": plan,
                        "product": product,
                    },
                    account_plan_list_params.AccountPlanListParams,
                ),
            ),
            model=AccountPlanResponse,
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
    ) -> AccountPlanResponse:
        """
        Delete the AccountPlan or AccountPlanGroup with the given UUID.

        This endpoint deletes an AccountPlan or AccountPlanGroup that has been attached
        to a specific Account in your Organization.

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
            f"/organizations/{org_id}/accountplans/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountPlanResponse,
        )


class AccountPlansResourceWithRawResponse:
    def __init__(self, account_plans: AccountPlansResource) -> None:
        self._account_plans = account_plans

        self.create = to_raw_response_wrapper(
            account_plans.create,
        )
        self.retrieve = to_raw_response_wrapper(
            account_plans.retrieve,
        )
        self.update = to_raw_response_wrapper(
            account_plans.update,
        )
        self.list = to_raw_response_wrapper(
            account_plans.list,
        )
        self.delete = to_raw_response_wrapper(
            account_plans.delete,
        )


class AsyncAccountPlansResourceWithRawResponse:
    def __init__(self, account_plans: AsyncAccountPlansResource) -> None:
        self._account_plans = account_plans

        self.create = async_to_raw_response_wrapper(
            account_plans.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            account_plans.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            account_plans.update,
        )
        self.list = async_to_raw_response_wrapper(
            account_plans.list,
        )
        self.delete = async_to_raw_response_wrapper(
            account_plans.delete,
        )


class AccountPlansResourceWithStreamingResponse:
    def __init__(self, account_plans: AccountPlansResource) -> None:
        self._account_plans = account_plans

        self.create = to_streamed_response_wrapper(
            account_plans.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            account_plans.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            account_plans.update,
        )
        self.list = to_streamed_response_wrapper(
            account_plans.list,
        )
        self.delete = to_streamed_response_wrapper(
            account_plans.delete,
        )


class AsyncAccountPlansResourceWithStreamingResponse:
    def __init__(self, account_plans: AsyncAccountPlansResource) -> None:
        self._account_plans = account_plans

        self.create = async_to_streamed_response_wrapper(
            account_plans.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            account_plans.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            account_plans.update,
        )
        self.list = async_to_streamed_response_wrapper(
            account_plans.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            account_plans.delete,
        )
