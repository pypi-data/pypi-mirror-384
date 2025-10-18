# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Any, List, Iterable, cast
from typing_extensions import Literal, overload

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import required_args, maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...pagination import SyncCursor, AsyncCursor
from ..._base_client import AsyncPaginator, make_request_options
from ...types.data_exports import schedule_list_params, schedule_create_params, schedule_update_params
from ...types.data_explorer_group_param import DataExplorerGroupParam
from ...types.data_exports.schedule_list_response import ScheduleListResponse
from ...types.data_exports.schedule_create_response import ScheduleCreateResponse
from ...types.data_exports.schedule_delete_response import ScheduleDeleteResponse
from ...types.data_exports.schedule_update_response import ScheduleUpdateResponse
from ...types.data_exports.schedule_retrieve_response import ScheduleRetrieveResponse

__all__ = ["SchedulesResource", "AsyncSchedulesResource"]


class SchedulesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SchedulesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return SchedulesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SchedulesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return SchedulesResourceWithStreamingResponse(self)

    @overload
    def create(
        self,
        *,
        org_id: str | None = None,
        operational_data_types: List[
            Literal[
                "BILLS",
                "COMMITMENTS",
                "ACCOUNTS",
                "BALANCES",
                "CONTRACTS",
                "ACCOUNT_PLANS",
                "AGGREGATIONS",
                "PLANS",
                "PRICING",
                "PRICING_BANDS",
                "BILL_LINE_ITEMS",
                "METERS",
                "PRODUCTS",
                "COMPOUND_AGGREGATIONS",
                "PLAN_GROUPS",
                "PLAN_GROUP_LINKS",
                "PLAN_TEMPLATES",
                "BALANCE_TRANSACTIONS",
                "TRANSACTION_TYPES",
            ]
        ],
        source_type: Literal["OPERATIONAL"],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleCreateResponse:
        """Create a new Data Export Schedule.

        Each Schedule can be configured for exporting
        _only one_ of either Usage or Operational data:

        **Operational Data Exports**.

        - Use the `operationalDataTypes` parameter to specify the entities whose
          operational data you want to include in the export each time the Export
          Schedule runs.
        - For each of the entity types you select, each time the Export Schedule runs a
          separate file is compiled containing the operational data for all entities of
          that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          export each time the Export Schedule runs.
        - You can use the `dimensionFilters` parameter to filter the usage data returned
          for export by adding specific values of non-numeric Dimension data fields on
          included Meters. Only the data collected for the values you've added for the
          selected Dimension fields will be included in the export.
        - You can use the `aggregations` to apply aggregation methods the usage data
          returned for export. This restricts the range of usage data returned for
          export to only the data collected by aggregated fields on selected Meters.
          Nothing is returned for any non-aggregated fields on Meters. The usage data
          for Meter fields is returned as the values resulting from applying the
          selected aggregation method. See the
          [Aggregations for Queries - Options and Consequences](https://www.m3ter.com/docs/guides/data-explorer/usage-data-explorer-v2#aggregations-for-queries---understanding-options-and-consequences)
          for more details.
        - If you've applied `aggregations` to the usage returned for export, you can
          then use the `groups` parameter to group the data by _Account_, _Dimension_,
          or _Time_.

        Request and Response schema:

        - Use the selector under the `sourceType` parameter to expose the relevant
          request and response schema for the source data type.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for source data type.

        Args:
          operational_data_types: A list of the entities whose operational data is included in the data export.

          source_type: The type of data to export. Possible values are: OPERATIONAL

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
        ...

    @overload
    def create(
        self,
        *,
        org_id: str | None = None,
        source_type: Literal["USAGE"],
        time_period: Literal[
            "TODAY",
            "YESTERDAY",
            "WEEK_TO_DATE",
            "MONTH_TO_DATE",
            "YEAR_TO_DATE",
            "PREVIOUS_WEEK",
            "PREVIOUS_MONTH",
            "PREVIOUS_QUARTER",
            "PREVIOUS_YEAR",
            "LAST_12_HOURS",
            "LAST_7_DAYS",
            "LAST_30_DAYS",
            "LAST_35_DAYS",
            "LAST_90_DAYS",
            "LAST_120_DAYS",
            "LAST_YEAR",
        ],
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[schedule_create_params.UsageDataExportScheduleRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[schedule_create_params.UsageDataExportScheduleRequestDimensionFilter] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleCreateResponse:
        """Create a new Data Export Schedule.

        Each Schedule can be configured for exporting
        _only one_ of either Usage or Operational data:

        **Operational Data Exports**.

        - Use the `operationalDataTypes` parameter to specify the entities whose
          operational data you want to include in the export each time the Export
          Schedule runs.
        - For each of the entity types you select, each time the Export Schedule runs a
          separate file is compiled containing the operational data for all entities of
          that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          export each time the Export Schedule runs.
        - You can use the `dimensionFilters` parameter to filter the usage data returned
          for export by adding specific values of non-numeric Dimension data fields on
          included Meters. Only the data collected for the values you've added for the
          selected Dimension fields will be included in the export.
        - You can use the `aggregations` to apply aggregation methods the usage data
          returned for export. This restricts the range of usage data returned for
          export to only the data collected by aggregated fields on selected Meters.
          Nothing is returned for any non-aggregated fields on Meters. The usage data
          for Meter fields is returned as the values resulting from applying the
          selected aggregation method. See the
          [Aggregations for Queries - Options and Consequences](https://www.m3ter.com/docs/guides/data-explorer/usage-data-explorer-v2#aggregations-for-queries---understanding-options-and-consequences)
          for more details.
        - If you've applied `aggregations` to the usage returned for export, you can
          then use the `groups` parameter to group the data by _Account_, _Dimension_,
          or _Time_.

        Request and Response schema:

        - Use the selector under the `sourceType` parameter to expose the relevant
          request and response schema for the source data type.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for source data type.

        Args:
          source_type: The type of data to export. Possible values are: USAGE

          time_period: Define a time period to control the range of usage data you want the data export
              to contain when it runs:

              - **TODAY**. Data collected for the current day up until the time the export is
                scheduled to run.
              - **YESTERDAY**. Data collected for the day before the export runs under the
                schedule - that is, the 24 hour period from midnight to midnight of the day
                before.
              - **PREVIOUS_WEEK**, **PREVIOUS_MONTH**, **PREVIOUS_QUARTER**,
                **PREVIOUS_YEAR**. Data collected for the previous full week, month, quarter,
                or year period. For example if **PREVIOUS_WEEK**, weeks run Monday to Monday -
                if the export is scheduled to run on June 12th 2024, which is a Wednesday, the
                export will contain data for the period running from Monday, June 3rd 2024 to
                midnight on Sunday, June 9th 2024.
              - **WEEK_TO_DATE**, **MONTH_TO_DATE**, or **YEAR_TO_DATE**. Data collected for
                the period covering the current week, month, or year period. For example if
                **WEEK_TO_DATE**, weeks run Monday to Monday - if the Export is scheduled to
                run at 10 a.m. UTC on October 16th 2024, which is a Wednesday, it will contain
                all usage data collected starting Monday October 14th 2024 through to the
                Wednesday at 10 a.m. UTC of the current week.
              - **LAST_12_HOURS**. Data collected for the twelve hour period up to the start
                of the hour in which the export is scheduled to run.
              - **LAST_7_DAYS**, **LAST_30_DAYS**, **LAST_35_DAYS**, **LAST_90_DAYS**,
                **LAST_120_DAYS** **LAST_YEAR**. Data collected for the selected period prior
                to the date the export is scheduled to run. For example if **LAST_30_DAYS**
                and the export is scheduled to run for any time on June 15th 2024, it will
                contain usage data collected for the previous 30 days - starting May 16th 2024
                through to midnight on June 14th 2024

              For more details and examples, see the
              [Time Period](https://www.m3ter.com/docs/guides/data-exports/creating-export-schedules#time-period)
              section in our main User Documentation.

          account_ids: List of account IDs to export

          aggregations: List of aggregations to apply

          dimension_filters: List of dimension filters to apply

          groups: List of groups to apply

          meter_ids: List of meter IDs to export

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
        ...

    @required_args(["operational_data_types", "source_type"], ["source_type", "time_period"])
    def create(
        self,
        *,
        org_id: str | None = None,
        operational_data_types: List[
            Literal[
                "BILLS",
                "COMMITMENTS",
                "ACCOUNTS",
                "BALANCES",
                "CONTRACTS",
                "ACCOUNT_PLANS",
                "AGGREGATIONS",
                "PLANS",
                "PRICING",
                "PRICING_BANDS",
                "BILL_LINE_ITEMS",
                "METERS",
                "PRODUCTS",
                "COMPOUND_AGGREGATIONS",
                "PLAN_GROUPS",
                "PLAN_GROUP_LINKS",
                "PLAN_TEMPLATES",
                "BALANCE_TRANSACTIONS",
                "TRANSACTION_TYPES",
            ]
        ]
        | Omit = omit,
        source_type: Literal["OPERATIONAL"] | Literal["USAGE"],
        version: int | Omit = omit,
        time_period: Literal[
            "TODAY",
            "YESTERDAY",
            "WEEK_TO_DATE",
            "MONTH_TO_DATE",
            "YEAR_TO_DATE",
            "PREVIOUS_WEEK",
            "PREVIOUS_MONTH",
            "PREVIOUS_QUARTER",
            "PREVIOUS_YEAR",
            "LAST_12_HOURS",
            "LAST_7_DAYS",
            "LAST_30_DAYS",
            "LAST_35_DAYS",
            "LAST_90_DAYS",
            "LAST_120_DAYS",
            "LAST_YEAR",
        ]
        | Omit = omit,
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[schedule_create_params.UsageDataExportScheduleRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[schedule_create_params.UsageDataExportScheduleRequestDimensionFilter] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleCreateResponse:
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return cast(
            ScheduleCreateResponse,
            self._post(
                f"/organizations/{org_id}/dataexports/schedules",
                body=maybe_transform(
                    {
                        "operational_data_types": operational_data_types,
                        "source_type": source_type,
                        "version": version,
                        "time_period": time_period,
                        "account_ids": account_ids,
                        "aggregations": aggregations,
                        "dimension_filters": dimension_filters,
                        "groups": groups,
                        "meter_ids": meter_ids,
                    },
                    schedule_create_params.ScheduleCreateParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ScheduleCreateResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
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
    ) -> ScheduleRetrieveResponse:
        """Retrieve a Data Export Schedule for the given UUID.

        Each Schedule can be
        configured for exporting _only one_ of either Usage or Operational data.

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
        return cast(
            ScheduleRetrieveResponse,
            self._get(
                f"/organizations/{org_id}/dataexports/schedules/{id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ScheduleRetrieveResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    @overload
    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        operational_data_types: List[
            Literal[
                "BILLS",
                "COMMITMENTS",
                "ACCOUNTS",
                "BALANCES",
                "CONTRACTS",
                "ACCOUNT_PLANS",
                "AGGREGATIONS",
                "PLANS",
                "PRICING",
                "PRICING_BANDS",
                "BILL_LINE_ITEMS",
                "METERS",
                "PRODUCTS",
                "COMPOUND_AGGREGATIONS",
                "PLAN_GROUPS",
                "PLAN_GROUP_LINKS",
                "PLAN_TEMPLATES",
                "BALANCE_TRANSACTIONS",
                "TRANSACTION_TYPES",
            ]
        ],
        source_type: Literal["OPERATIONAL"],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleUpdateResponse:
        """Update a Data Export Schedule for the given UUID.

        Each Schedule can be
        configured for exporting _only one_ of either Usage or Operational data:

        **Operational Data Exports**.

        - Use the `operationalDataTypes` parameter to specify the entities whose
          operational data you want to include in the export each time the Export
          Schedule runs.
        - For each of the entity types you select, each time the Export Schedule runs a
          separate file is compiled containing the operational data for all entities of
          that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          export each time the Export Schedule runs.
        - You can use the `dimensionFilters` parameter to filter the usage data returned
          for export by adding specific values of non-numeric Dimension data fields on
          included Meters. Only the data collected for the values you've added for the
          selected Dimension fields will be included in the export.
        - You can use the `aggregations` to apply aggregation methods the usage data
          returned for export. This restricts the range of usage data returned for
          export to only the data collected by aggregated fields on selected Meters.
          Nothing is returned for any non-aggregated fields on Meters. The usage data
          for Meter fields is returned as the values resulting from applying the
          selected aggregation method. See the
          [Aggregations for Queries - Options and Consequences](https://www.m3ter.com/docs/guides/data-explorer/usage-data-explorer-v2#aggregations-for-queries---understanding-options-and-consequences)
          for more details.
        - If you've applied `aggregations` to the usage returned for export, you can
          then use the `groups` parameter to group the data by _Account_, _Dimension_,
          or _Time_.

        Args:
          operational_data_types: A list of the entities whose operational data is included in the data export.

          source_type: The type of data to export. Possible values are: OPERATIONAL

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
        ...

    @overload
    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        source_type: Literal["USAGE"],
        time_period: Literal[
            "TODAY",
            "YESTERDAY",
            "WEEK_TO_DATE",
            "MONTH_TO_DATE",
            "YEAR_TO_DATE",
            "PREVIOUS_WEEK",
            "PREVIOUS_MONTH",
            "PREVIOUS_QUARTER",
            "PREVIOUS_YEAR",
            "LAST_12_HOURS",
            "LAST_7_DAYS",
            "LAST_30_DAYS",
            "LAST_35_DAYS",
            "LAST_90_DAYS",
            "LAST_120_DAYS",
            "LAST_YEAR",
        ],
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[schedule_update_params.UsageDataExportScheduleRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[schedule_update_params.UsageDataExportScheduleRequestDimensionFilter] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleUpdateResponse:
        """Update a Data Export Schedule for the given UUID.

        Each Schedule can be
        configured for exporting _only one_ of either Usage or Operational data:

        **Operational Data Exports**.

        - Use the `operationalDataTypes` parameter to specify the entities whose
          operational data you want to include in the export each time the Export
          Schedule runs.
        - For each of the entity types you select, each time the Export Schedule runs a
          separate file is compiled containing the operational data for all entities of
          that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          export each time the Export Schedule runs.
        - You can use the `dimensionFilters` parameter to filter the usage data returned
          for export by adding specific values of non-numeric Dimension data fields on
          included Meters. Only the data collected for the values you've added for the
          selected Dimension fields will be included in the export.
        - You can use the `aggregations` to apply aggregation methods the usage data
          returned for export. This restricts the range of usage data returned for
          export to only the data collected by aggregated fields on selected Meters.
          Nothing is returned for any non-aggregated fields on Meters. The usage data
          for Meter fields is returned as the values resulting from applying the
          selected aggregation method. See the
          [Aggregations for Queries - Options and Consequences](https://www.m3ter.com/docs/guides/data-explorer/usage-data-explorer-v2#aggregations-for-queries---understanding-options-and-consequences)
          for more details.
        - If you've applied `aggregations` to the usage returned for export, you can
          then use the `groups` parameter to group the data by _Account_, _Dimension_,
          or _Time_.

        Args:
          source_type: The type of data to export. Possible values are: USAGE

          time_period: Define a time period to control the range of usage data you want the data export
              to contain when it runs:

              - **TODAY**. Data collected for the current day up until the time the export is
                scheduled to run.
              - **YESTERDAY**. Data collected for the day before the export runs under the
                schedule - that is, the 24 hour period from midnight to midnight of the day
                before.
              - **PREVIOUS_WEEK**, **PREVIOUS_MONTH**, **PREVIOUS_QUARTER**,
                **PREVIOUS_YEAR**. Data collected for the previous full week, month, quarter,
                or year period. For example if **PREVIOUS_WEEK**, weeks run Monday to Monday -
                if the export is scheduled to run on June 12th 2024, which is a Wednesday, the
                export will contain data for the period running from Monday, June 3rd 2024 to
                midnight on Sunday, June 9th 2024.
              - **WEEK_TO_DATE**, **MONTH_TO_DATE**, or **YEAR_TO_DATE**. Data collected for
                the period covering the current week, month, or year period. For example if
                **WEEK_TO_DATE**, weeks run Monday to Monday - if the Export is scheduled to
                run at 10 a.m. UTC on October 16th 2024, which is a Wednesday, it will contain
                all usage data collected starting Monday October 14th 2024 through to the
                Wednesday at 10 a.m. UTC of the current week.
              - **LAST_12_HOURS**. Data collected for the twelve hour period up to the start
                of the hour in which the export is scheduled to run.
              - **LAST_7_DAYS**, **LAST_30_DAYS**, **LAST_35_DAYS**, **LAST_90_DAYS**,
                **LAST_120_DAYS** **LAST_YEAR**. Data collected for the selected period prior
                to the date the export is scheduled to run. For example if **LAST_30_DAYS**
                and the export is scheduled to run for any time on June 15th 2024, it will
                contain usage data collected for the previous 30 days - starting May 16th 2024
                through to midnight on June 14th 2024

              For more details and examples, see the
              [Time Period](https://www.m3ter.com/docs/guides/data-exports/creating-export-schedules#time-period)
              section in our main User Documentation.

          account_ids: List of account IDs to export

          aggregations: List of aggregations to apply

          dimension_filters: List of dimension filters to apply

          groups: List of groups to apply

          meter_ids: List of meter IDs to export

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
        ...

    @required_args(["operational_data_types", "source_type"], ["source_type", "time_period"])
    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        operational_data_types: List[
            Literal[
                "BILLS",
                "COMMITMENTS",
                "ACCOUNTS",
                "BALANCES",
                "CONTRACTS",
                "ACCOUNT_PLANS",
                "AGGREGATIONS",
                "PLANS",
                "PRICING",
                "PRICING_BANDS",
                "BILL_LINE_ITEMS",
                "METERS",
                "PRODUCTS",
                "COMPOUND_AGGREGATIONS",
                "PLAN_GROUPS",
                "PLAN_GROUP_LINKS",
                "PLAN_TEMPLATES",
                "BALANCE_TRANSACTIONS",
                "TRANSACTION_TYPES",
            ]
        ]
        | Omit = omit,
        source_type: Literal["OPERATIONAL"] | Literal["USAGE"],
        version: int | Omit = omit,
        time_period: Literal[
            "TODAY",
            "YESTERDAY",
            "WEEK_TO_DATE",
            "MONTH_TO_DATE",
            "YEAR_TO_DATE",
            "PREVIOUS_WEEK",
            "PREVIOUS_MONTH",
            "PREVIOUS_QUARTER",
            "PREVIOUS_YEAR",
            "LAST_12_HOURS",
            "LAST_7_DAYS",
            "LAST_30_DAYS",
            "LAST_35_DAYS",
            "LAST_90_DAYS",
            "LAST_120_DAYS",
            "LAST_YEAR",
        ]
        | Omit = omit,
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[schedule_update_params.UsageDataExportScheduleRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[schedule_update_params.UsageDataExportScheduleRequestDimensionFilter] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleUpdateResponse:
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return cast(
            ScheduleUpdateResponse,
            self._put(
                f"/organizations/{org_id}/dataexports/schedules/{id}",
                body=maybe_transform(
                    {
                        "operational_data_types": operational_data_types,
                        "source_type": source_type,
                        "version": version,
                        "time_period": time_period,
                        "account_ids": account_ids,
                        "aggregations": aggregations,
                        "dimension_filters": dimension_filters,
                        "groups": groups,
                        "meter_ids": meter_ids,
                    },
                    schedule_update_params.ScheduleUpdateParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ScheduleUpdateResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[ScheduleListResponse]:
        """Retrieve a list of Data Export Schedules created for your Organization.

        You can
        filter the response by Schedules `ids`.

        The response will contain an array for both the operational and usage Data
        Export Schedules in your Organization.

        Args:
          ids: Data Export Schedule IDs to filter the returned list by.

          next_token: `nextToken` for multi page retrievals

          page_size: Number of schedules to retrieve per page

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
            f"/organizations/{org_id}/dataexports/schedules",
            page=SyncCursor[ScheduleListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    schedule_list_params.ScheduleListParams,
                ),
            ),
            model=ScheduleListResponse,
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
    ) -> ScheduleDeleteResponse:
        """Delete the Data Export Schedule for the given UUID.

        Each Schedule can be
        configured for exporting _only one_ of either Usage or Operational data.

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
        return cast(
            ScheduleDeleteResponse,
            self._delete(
                f"/organizations/{org_id}/dataexports/schedules/{id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ScheduleDeleteResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )


class AsyncSchedulesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSchedulesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSchedulesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSchedulesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncSchedulesResourceWithStreamingResponse(self)

    @overload
    async def create(
        self,
        *,
        org_id: str | None = None,
        operational_data_types: List[
            Literal[
                "BILLS",
                "COMMITMENTS",
                "ACCOUNTS",
                "BALANCES",
                "CONTRACTS",
                "ACCOUNT_PLANS",
                "AGGREGATIONS",
                "PLANS",
                "PRICING",
                "PRICING_BANDS",
                "BILL_LINE_ITEMS",
                "METERS",
                "PRODUCTS",
                "COMPOUND_AGGREGATIONS",
                "PLAN_GROUPS",
                "PLAN_GROUP_LINKS",
                "PLAN_TEMPLATES",
                "BALANCE_TRANSACTIONS",
                "TRANSACTION_TYPES",
            ]
        ],
        source_type: Literal["OPERATIONAL"],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleCreateResponse:
        """Create a new Data Export Schedule.

        Each Schedule can be configured for exporting
        _only one_ of either Usage or Operational data:

        **Operational Data Exports**.

        - Use the `operationalDataTypes` parameter to specify the entities whose
          operational data you want to include in the export each time the Export
          Schedule runs.
        - For each of the entity types you select, each time the Export Schedule runs a
          separate file is compiled containing the operational data for all entities of
          that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          export each time the Export Schedule runs.
        - You can use the `dimensionFilters` parameter to filter the usage data returned
          for export by adding specific values of non-numeric Dimension data fields on
          included Meters. Only the data collected for the values you've added for the
          selected Dimension fields will be included in the export.
        - You can use the `aggregations` to apply aggregation methods the usage data
          returned for export. This restricts the range of usage data returned for
          export to only the data collected by aggregated fields on selected Meters.
          Nothing is returned for any non-aggregated fields on Meters. The usage data
          for Meter fields is returned as the values resulting from applying the
          selected aggregation method. See the
          [Aggregations for Queries - Options and Consequences](https://www.m3ter.com/docs/guides/data-explorer/usage-data-explorer-v2#aggregations-for-queries---understanding-options-and-consequences)
          for more details.
        - If you've applied `aggregations` to the usage returned for export, you can
          then use the `groups` parameter to group the data by _Account_, _Dimension_,
          or _Time_.

        Request and Response schema:

        - Use the selector under the `sourceType` parameter to expose the relevant
          request and response schema for the source data type.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for source data type.

        Args:
          operational_data_types: A list of the entities whose operational data is included in the data export.

          source_type: The type of data to export. Possible values are: OPERATIONAL

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
        ...

    @overload
    async def create(
        self,
        *,
        org_id: str | None = None,
        source_type: Literal["USAGE"],
        time_period: Literal[
            "TODAY",
            "YESTERDAY",
            "WEEK_TO_DATE",
            "MONTH_TO_DATE",
            "YEAR_TO_DATE",
            "PREVIOUS_WEEK",
            "PREVIOUS_MONTH",
            "PREVIOUS_QUARTER",
            "PREVIOUS_YEAR",
            "LAST_12_HOURS",
            "LAST_7_DAYS",
            "LAST_30_DAYS",
            "LAST_35_DAYS",
            "LAST_90_DAYS",
            "LAST_120_DAYS",
            "LAST_YEAR",
        ],
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[schedule_create_params.UsageDataExportScheduleRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[schedule_create_params.UsageDataExportScheduleRequestDimensionFilter] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleCreateResponse:
        """Create a new Data Export Schedule.

        Each Schedule can be configured for exporting
        _only one_ of either Usage or Operational data:

        **Operational Data Exports**.

        - Use the `operationalDataTypes` parameter to specify the entities whose
          operational data you want to include in the export each time the Export
          Schedule runs.
        - For each of the entity types you select, each time the Export Schedule runs a
          separate file is compiled containing the operational data for all entities of
          that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          export each time the Export Schedule runs.
        - You can use the `dimensionFilters` parameter to filter the usage data returned
          for export by adding specific values of non-numeric Dimension data fields on
          included Meters. Only the data collected for the values you've added for the
          selected Dimension fields will be included in the export.
        - You can use the `aggregations` to apply aggregation methods the usage data
          returned for export. This restricts the range of usage data returned for
          export to only the data collected by aggregated fields on selected Meters.
          Nothing is returned for any non-aggregated fields on Meters. The usage data
          for Meter fields is returned as the values resulting from applying the
          selected aggregation method. See the
          [Aggregations for Queries - Options and Consequences](https://www.m3ter.com/docs/guides/data-explorer/usage-data-explorer-v2#aggregations-for-queries---understanding-options-and-consequences)
          for more details.
        - If you've applied `aggregations` to the usage returned for export, you can
          then use the `groups` parameter to group the data by _Account_, _Dimension_,
          or _Time_.

        Request and Response schema:

        - Use the selector under the `sourceType` parameter to expose the relevant
          request and response schema for the source data type.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for source data type.

        Args:
          source_type: The type of data to export. Possible values are: USAGE

          time_period: Define a time period to control the range of usage data you want the data export
              to contain when it runs:

              - **TODAY**. Data collected for the current day up until the time the export is
                scheduled to run.
              - **YESTERDAY**. Data collected for the day before the export runs under the
                schedule - that is, the 24 hour period from midnight to midnight of the day
                before.
              - **PREVIOUS_WEEK**, **PREVIOUS_MONTH**, **PREVIOUS_QUARTER**,
                **PREVIOUS_YEAR**. Data collected for the previous full week, month, quarter,
                or year period. For example if **PREVIOUS_WEEK**, weeks run Monday to Monday -
                if the export is scheduled to run on June 12th 2024, which is a Wednesday, the
                export will contain data for the period running from Monday, June 3rd 2024 to
                midnight on Sunday, June 9th 2024.
              - **WEEK_TO_DATE**, **MONTH_TO_DATE**, or **YEAR_TO_DATE**. Data collected for
                the period covering the current week, month, or year period. For example if
                **WEEK_TO_DATE**, weeks run Monday to Monday - if the Export is scheduled to
                run at 10 a.m. UTC on October 16th 2024, which is a Wednesday, it will contain
                all usage data collected starting Monday October 14th 2024 through to the
                Wednesday at 10 a.m. UTC of the current week.
              - **LAST_12_HOURS**. Data collected for the twelve hour period up to the start
                of the hour in which the export is scheduled to run.
              - **LAST_7_DAYS**, **LAST_30_DAYS**, **LAST_35_DAYS**, **LAST_90_DAYS**,
                **LAST_120_DAYS** **LAST_YEAR**. Data collected for the selected period prior
                to the date the export is scheduled to run. For example if **LAST_30_DAYS**
                and the export is scheduled to run for any time on June 15th 2024, it will
                contain usage data collected for the previous 30 days - starting May 16th 2024
                through to midnight on June 14th 2024

              For more details and examples, see the
              [Time Period](https://www.m3ter.com/docs/guides/data-exports/creating-export-schedules#time-period)
              section in our main User Documentation.

          account_ids: List of account IDs to export

          aggregations: List of aggregations to apply

          dimension_filters: List of dimension filters to apply

          groups: List of groups to apply

          meter_ids: List of meter IDs to export

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
        ...

    @required_args(["operational_data_types", "source_type"], ["source_type", "time_period"])
    async def create(
        self,
        *,
        org_id: str | None = None,
        operational_data_types: List[
            Literal[
                "BILLS",
                "COMMITMENTS",
                "ACCOUNTS",
                "BALANCES",
                "CONTRACTS",
                "ACCOUNT_PLANS",
                "AGGREGATIONS",
                "PLANS",
                "PRICING",
                "PRICING_BANDS",
                "BILL_LINE_ITEMS",
                "METERS",
                "PRODUCTS",
                "COMPOUND_AGGREGATIONS",
                "PLAN_GROUPS",
                "PLAN_GROUP_LINKS",
                "PLAN_TEMPLATES",
                "BALANCE_TRANSACTIONS",
                "TRANSACTION_TYPES",
            ]
        ]
        | Omit = omit,
        source_type: Literal["OPERATIONAL"] | Literal["USAGE"],
        version: int | Omit = omit,
        time_period: Literal[
            "TODAY",
            "YESTERDAY",
            "WEEK_TO_DATE",
            "MONTH_TO_DATE",
            "YEAR_TO_DATE",
            "PREVIOUS_WEEK",
            "PREVIOUS_MONTH",
            "PREVIOUS_QUARTER",
            "PREVIOUS_YEAR",
            "LAST_12_HOURS",
            "LAST_7_DAYS",
            "LAST_30_DAYS",
            "LAST_35_DAYS",
            "LAST_90_DAYS",
            "LAST_120_DAYS",
            "LAST_YEAR",
        ]
        | Omit = omit,
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[schedule_create_params.UsageDataExportScheduleRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[schedule_create_params.UsageDataExportScheduleRequestDimensionFilter] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleCreateResponse:
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return cast(
            ScheduleCreateResponse,
            await self._post(
                f"/organizations/{org_id}/dataexports/schedules",
                body=await async_maybe_transform(
                    {
                        "operational_data_types": operational_data_types,
                        "source_type": source_type,
                        "version": version,
                        "time_period": time_period,
                        "account_ids": account_ids,
                        "aggregations": aggregations,
                        "dimension_filters": dimension_filters,
                        "groups": groups,
                        "meter_ids": meter_ids,
                    },
                    schedule_create_params.ScheduleCreateParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ScheduleCreateResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
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
    ) -> ScheduleRetrieveResponse:
        """Retrieve a Data Export Schedule for the given UUID.

        Each Schedule can be
        configured for exporting _only one_ of either Usage or Operational data.

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
        return cast(
            ScheduleRetrieveResponse,
            await self._get(
                f"/organizations/{org_id}/dataexports/schedules/{id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ScheduleRetrieveResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    @overload
    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        operational_data_types: List[
            Literal[
                "BILLS",
                "COMMITMENTS",
                "ACCOUNTS",
                "BALANCES",
                "CONTRACTS",
                "ACCOUNT_PLANS",
                "AGGREGATIONS",
                "PLANS",
                "PRICING",
                "PRICING_BANDS",
                "BILL_LINE_ITEMS",
                "METERS",
                "PRODUCTS",
                "COMPOUND_AGGREGATIONS",
                "PLAN_GROUPS",
                "PLAN_GROUP_LINKS",
                "PLAN_TEMPLATES",
                "BALANCE_TRANSACTIONS",
                "TRANSACTION_TYPES",
            ]
        ],
        source_type: Literal["OPERATIONAL"],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleUpdateResponse:
        """Update a Data Export Schedule for the given UUID.

        Each Schedule can be
        configured for exporting _only one_ of either Usage or Operational data:

        **Operational Data Exports**.

        - Use the `operationalDataTypes` parameter to specify the entities whose
          operational data you want to include in the export each time the Export
          Schedule runs.
        - For each of the entity types you select, each time the Export Schedule runs a
          separate file is compiled containing the operational data for all entities of
          that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          export each time the Export Schedule runs.
        - You can use the `dimensionFilters` parameter to filter the usage data returned
          for export by adding specific values of non-numeric Dimension data fields on
          included Meters. Only the data collected for the values you've added for the
          selected Dimension fields will be included in the export.
        - You can use the `aggregations` to apply aggregation methods the usage data
          returned for export. This restricts the range of usage data returned for
          export to only the data collected by aggregated fields on selected Meters.
          Nothing is returned for any non-aggregated fields on Meters. The usage data
          for Meter fields is returned as the values resulting from applying the
          selected aggregation method. See the
          [Aggregations for Queries - Options and Consequences](https://www.m3ter.com/docs/guides/data-explorer/usage-data-explorer-v2#aggregations-for-queries---understanding-options-and-consequences)
          for more details.
        - If you've applied `aggregations` to the usage returned for export, you can
          then use the `groups` parameter to group the data by _Account_, _Dimension_,
          or _Time_.

        Args:
          operational_data_types: A list of the entities whose operational data is included in the data export.

          source_type: The type of data to export. Possible values are: OPERATIONAL

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
        ...

    @overload
    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        source_type: Literal["USAGE"],
        time_period: Literal[
            "TODAY",
            "YESTERDAY",
            "WEEK_TO_DATE",
            "MONTH_TO_DATE",
            "YEAR_TO_DATE",
            "PREVIOUS_WEEK",
            "PREVIOUS_MONTH",
            "PREVIOUS_QUARTER",
            "PREVIOUS_YEAR",
            "LAST_12_HOURS",
            "LAST_7_DAYS",
            "LAST_30_DAYS",
            "LAST_35_DAYS",
            "LAST_90_DAYS",
            "LAST_120_DAYS",
            "LAST_YEAR",
        ],
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[schedule_update_params.UsageDataExportScheduleRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[schedule_update_params.UsageDataExportScheduleRequestDimensionFilter] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleUpdateResponse:
        """Update a Data Export Schedule for the given UUID.

        Each Schedule can be
        configured for exporting _only one_ of either Usage or Operational data:

        **Operational Data Exports**.

        - Use the `operationalDataTypes` parameter to specify the entities whose
          operational data you want to include in the export each time the Export
          Schedule runs.
        - For each of the entity types you select, each time the Export Schedule runs a
          separate file is compiled containing the operational data for all entities of
          that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          export each time the Export Schedule runs.
        - You can use the `dimensionFilters` parameter to filter the usage data returned
          for export by adding specific values of non-numeric Dimension data fields on
          included Meters. Only the data collected for the values you've added for the
          selected Dimension fields will be included in the export.
        - You can use the `aggregations` to apply aggregation methods the usage data
          returned for export. This restricts the range of usage data returned for
          export to only the data collected by aggregated fields on selected Meters.
          Nothing is returned for any non-aggregated fields on Meters. The usage data
          for Meter fields is returned as the values resulting from applying the
          selected aggregation method. See the
          [Aggregations for Queries - Options and Consequences](https://www.m3ter.com/docs/guides/data-explorer/usage-data-explorer-v2#aggregations-for-queries---understanding-options-and-consequences)
          for more details.
        - If you've applied `aggregations` to the usage returned for export, you can
          then use the `groups` parameter to group the data by _Account_, _Dimension_,
          or _Time_.

        Args:
          source_type: The type of data to export. Possible values are: USAGE

          time_period: Define a time period to control the range of usage data you want the data export
              to contain when it runs:

              - **TODAY**. Data collected for the current day up until the time the export is
                scheduled to run.
              - **YESTERDAY**. Data collected for the day before the export runs under the
                schedule - that is, the 24 hour period from midnight to midnight of the day
                before.
              - **PREVIOUS_WEEK**, **PREVIOUS_MONTH**, **PREVIOUS_QUARTER**,
                **PREVIOUS_YEAR**. Data collected for the previous full week, month, quarter,
                or year period. For example if **PREVIOUS_WEEK**, weeks run Monday to Monday -
                if the export is scheduled to run on June 12th 2024, which is a Wednesday, the
                export will contain data for the period running from Monday, June 3rd 2024 to
                midnight on Sunday, June 9th 2024.
              - **WEEK_TO_DATE**, **MONTH_TO_DATE**, or **YEAR_TO_DATE**. Data collected for
                the period covering the current week, month, or year period. For example if
                **WEEK_TO_DATE**, weeks run Monday to Monday - if the Export is scheduled to
                run at 10 a.m. UTC on October 16th 2024, which is a Wednesday, it will contain
                all usage data collected starting Monday October 14th 2024 through to the
                Wednesday at 10 a.m. UTC of the current week.
              - **LAST_12_HOURS**. Data collected for the twelve hour period up to the start
                of the hour in which the export is scheduled to run.
              - **LAST_7_DAYS**, **LAST_30_DAYS**, **LAST_35_DAYS**, **LAST_90_DAYS**,
                **LAST_120_DAYS** **LAST_YEAR**. Data collected for the selected period prior
                to the date the export is scheduled to run. For example if **LAST_30_DAYS**
                and the export is scheduled to run for any time on June 15th 2024, it will
                contain usage data collected for the previous 30 days - starting May 16th 2024
                through to midnight on June 14th 2024

              For more details and examples, see the
              [Time Period](https://www.m3ter.com/docs/guides/data-exports/creating-export-schedules#time-period)
              section in our main User Documentation.

          account_ids: List of account IDs to export

          aggregations: List of aggregations to apply

          dimension_filters: List of dimension filters to apply

          groups: List of groups to apply

          meter_ids: List of meter IDs to export

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
        ...

    @required_args(["operational_data_types", "source_type"], ["source_type", "time_period"])
    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        operational_data_types: List[
            Literal[
                "BILLS",
                "COMMITMENTS",
                "ACCOUNTS",
                "BALANCES",
                "CONTRACTS",
                "ACCOUNT_PLANS",
                "AGGREGATIONS",
                "PLANS",
                "PRICING",
                "PRICING_BANDS",
                "BILL_LINE_ITEMS",
                "METERS",
                "PRODUCTS",
                "COMPOUND_AGGREGATIONS",
                "PLAN_GROUPS",
                "PLAN_GROUP_LINKS",
                "PLAN_TEMPLATES",
                "BALANCE_TRANSACTIONS",
                "TRANSACTION_TYPES",
            ]
        ]
        | Omit = omit,
        source_type: Literal["OPERATIONAL"] | Literal["USAGE"],
        version: int | Omit = omit,
        time_period: Literal[
            "TODAY",
            "YESTERDAY",
            "WEEK_TO_DATE",
            "MONTH_TO_DATE",
            "YEAR_TO_DATE",
            "PREVIOUS_WEEK",
            "PREVIOUS_MONTH",
            "PREVIOUS_QUARTER",
            "PREVIOUS_YEAR",
            "LAST_12_HOURS",
            "LAST_7_DAYS",
            "LAST_30_DAYS",
            "LAST_35_DAYS",
            "LAST_90_DAYS",
            "LAST_120_DAYS",
            "LAST_YEAR",
        ]
        | Omit = omit,
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[schedule_update_params.UsageDataExportScheduleRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[schedule_update_params.UsageDataExportScheduleRequestDimensionFilter] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduleUpdateResponse:
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return cast(
            ScheduleUpdateResponse,
            await self._put(
                f"/organizations/{org_id}/dataexports/schedules/{id}",
                body=await async_maybe_transform(
                    {
                        "operational_data_types": operational_data_types,
                        "source_type": source_type,
                        "version": version,
                        "time_period": time_period,
                        "account_ids": account_ids,
                        "aggregations": aggregations,
                        "dimension_filters": dimension_filters,
                        "groups": groups,
                        "meter_ids": meter_ids,
                    },
                    schedule_update_params.ScheduleUpdateParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ScheduleUpdateResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[ScheduleListResponse, AsyncCursor[ScheduleListResponse]]:
        """Retrieve a list of Data Export Schedules created for your Organization.

        You can
        filter the response by Schedules `ids`.

        The response will contain an array for both the operational and usage Data
        Export Schedules in your Organization.

        Args:
          ids: Data Export Schedule IDs to filter the returned list by.

          next_token: `nextToken` for multi page retrievals

          page_size: Number of schedules to retrieve per page

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
            f"/organizations/{org_id}/dataexports/schedules",
            page=AsyncCursor[ScheduleListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    schedule_list_params.ScheduleListParams,
                ),
            ),
            model=ScheduleListResponse,
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
    ) -> ScheduleDeleteResponse:
        """Delete the Data Export Schedule for the given UUID.

        Each Schedule can be
        configured for exporting _only one_ of either Usage or Operational data.

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
        return cast(
            ScheduleDeleteResponse,
            await self._delete(
                f"/organizations/{org_id}/dataexports/schedules/{id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ScheduleDeleteResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )


class SchedulesResourceWithRawResponse:
    def __init__(self, schedules: SchedulesResource) -> None:
        self._schedules = schedules

        self.create = to_raw_response_wrapper(
            schedules.create,
        )
        self.retrieve = to_raw_response_wrapper(
            schedules.retrieve,
        )
        self.update = to_raw_response_wrapper(
            schedules.update,
        )
        self.list = to_raw_response_wrapper(
            schedules.list,
        )
        self.delete = to_raw_response_wrapper(
            schedules.delete,
        )


class AsyncSchedulesResourceWithRawResponse:
    def __init__(self, schedules: AsyncSchedulesResource) -> None:
        self._schedules = schedules

        self.create = async_to_raw_response_wrapper(
            schedules.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            schedules.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            schedules.update,
        )
        self.list = async_to_raw_response_wrapper(
            schedules.list,
        )
        self.delete = async_to_raw_response_wrapper(
            schedules.delete,
        )


class SchedulesResourceWithStreamingResponse:
    def __init__(self, schedules: SchedulesResource) -> None:
        self._schedules = schedules

        self.create = to_streamed_response_wrapper(
            schedules.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            schedules.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            schedules.update,
        )
        self.list = to_streamed_response_wrapper(
            schedules.list,
        )
        self.delete = to_streamed_response_wrapper(
            schedules.delete,
        )


class AsyncSchedulesResourceWithStreamingResponse:
    def __init__(self, schedules: AsyncSchedulesResource) -> None:
        self._schedules = schedules

        self.create = async_to_streamed_response_wrapper(
            schedules.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            schedules.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            schedules.update,
        )
        self.list = async_to_streamed_response_wrapper(
            schedules.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            schedules.delete,
        )
