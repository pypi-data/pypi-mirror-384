# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable
from datetime import datetime
from typing_extensions import Literal, overload

import httpx

from .jobs import (
    JobsResource,
    AsyncJobsResource,
    JobsResourceWithRawResponse,
    AsyncJobsResourceWithRawResponse,
    JobsResourceWithStreamingResponse,
    AsyncJobsResourceWithStreamingResponse,
)
from ...types import data_export_create_adhoc_params
from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import required_args, maybe_transform, async_maybe_transform
from ..._compat import cached_property
from .schedules import (
    SchedulesResource,
    AsyncSchedulesResource,
    SchedulesResourceWithRawResponse,
    AsyncSchedulesResourceWithRawResponse,
    SchedulesResourceWithStreamingResponse,
    AsyncSchedulesResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .destinations import (
    DestinationsResource,
    AsyncDestinationsResource,
    DestinationsResourceWithRawResponse,
    AsyncDestinationsResourceWithRawResponse,
    DestinationsResourceWithStreamingResponse,
    AsyncDestinationsResourceWithStreamingResponse,
)
from ..._base_client import make_request_options
from ...types.ad_hoc_response import AdHocResponse
from ...types.data_explorer_group_param import DataExplorerGroupParam

__all__ = ["DataExportsResource", "AsyncDataExportsResource"]


class DataExportsResource(SyncAPIResource):
    @cached_property
    def destinations(self) -> DestinationsResource:
        return DestinationsResource(self._client)

    @cached_property
    def jobs(self) -> JobsResource:
        return JobsResource(self._client)

    @cached_property
    def schedules(self) -> SchedulesResource:
        return SchedulesResource(self._client)

    @cached_property
    def with_raw_response(self) -> DataExportsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return DataExportsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DataExportsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return DataExportsResourceWithStreamingResponse(self)

    @overload
    def create_adhoc(
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
    ) -> AdHocResponse:
        """Trigger an ad-hoc Data Export.

        Each ad-hoc Export can be configured for
        exporting _only one of_ either Usage or Operational data:

        **Operational Data Exports**.

        - **Entity Types**. Use the `operationalDataTypes` parameter to specify the
          entities whose operational data you want to include in the ad-hoc export.
        - **Export Files**. For each of the entity types you select, when the ad-hoc
          export runs a separate file is compiled containing the operational data for
          all entities of that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          ad-hoc export.
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

        **Date Range for Operational Data Exports**. To restrict the operational data
        included in the ad-hoc export by a date/time range, use the `startDate`
        date/time request parameter to specify the start of the time period. The export
        will include all operational data from the specified `startDate` up until the
        date/time the export job runs.

        **Date Range for Usage Data Exports**. To restrict the usage data included in
        the ad-hoc export by date/time range, use the `startDate` and `endDate`
        date/time parameters:

        - Both `startDate` and `endDate` are required.
        - `endDate` must be after `startDate`.
        - `endDate` cannot be after tomorrow at midnight UTC. For example if today is
          May 20th 2025, you can only choose `endDate` to be equal or before
          2025-05-21T00:00:00.000Z.

        **NOTE:** You can use the ExportJob `id` returned to check the status of the
        triggered ad-hoc export. See the
        [ExportJob](https://www.m3ter.com/docs/api#tag/ExportJob) section of this API
        Reference.

        Args:
          operational_data_types: The list of the operational data types should be exported for.

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
    def create_adhoc(
        self,
        *,
        org_id: str | None = None,
        source_type: Literal["USAGE"],
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[data_export_create_adhoc_params.AdHocUsageDataRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[data_export_create_adhoc_params.AdHocUsageDataRequestDimensionFilter] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AdHocResponse:
        """Trigger an ad-hoc Data Export.

        Each ad-hoc Export can be configured for
        exporting _only one of_ either Usage or Operational data:

        **Operational Data Exports**.

        - **Entity Types**. Use the `operationalDataTypes` parameter to specify the
          entities whose operational data you want to include in the ad-hoc export.
        - **Export Files**. For each of the entity types you select, when the ad-hoc
          export runs a separate file is compiled containing the operational data for
          all entities of that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          ad-hoc export.
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

        **Date Range for Operational Data Exports**. To restrict the operational data
        included in the ad-hoc export by a date/time range, use the `startDate`
        date/time request parameter to specify the start of the time period. The export
        will include all operational data from the specified `startDate` up until the
        date/time the export job runs.

        **Date Range for Usage Data Exports**. To restrict the usage data included in
        the ad-hoc export by date/time range, use the `startDate` and `endDate`
        date/time parameters:

        - Both `startDate` and `endDate` are required.
        - `endDate` must be after `startDate`.
        - `endDate` cannot be after tomorrow at midnight UTC. For example if today is
          May 20th 2025, you can only choose `endDate` to be equal or before
          2025-05-21T00:00:00.000Z.

        **NOTE:** You can use the ExportJob `id` returned to check the status of the
        triggered ad-hoc export. See the
        [ExportJob](https://www.m3ter.com/docs/api#tag/ExportJob) section of this API
        Reference.

        Args:
          source_type: The type of data to export. Possible values are: USAGE

          account_ids: List of account IDs for which the usage data will be exported.

          aggregations: List of aggregations to apply

          dimension_filters: List of dimension filters to apply

          end_date: The exclusive end date for the data export.

          groups: List of groups to apply

          meter_ids: List of meter IDs for which the usage data will be exported.

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

    @required_args(["operational_data_types", "source_type"], ["source_type"])
    def create_adhoc(
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
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[data_export_create_adhoc_params.AdHocUsageDataRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[data_export_create_adhoc_params.AdHocUsageDataRequestDimensionFilter] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AdHocResponse:
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._post(
            f"/organizations/{org_id}/dataexports/adhoc",
            body=maybe_transform(
                {
                    "operational_data_types": operational_data_types,
                    "source_type": source_type,
                    "version": version,
                    "account_ids": account_ids,
                    "aggregations": aggregations,
                    "dimension_filters": dimension_filters,
                    "end_date": end_date,
                    "groups": groups,
                    "meter_ids": meter_ids,
                },
                data_export_create_adhoc_params.DataExportCreateAdhocParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AdHocResponse,
        )


class AsyncDataExportsResource(AsyncAPIResource):
    @cached_property
    def destinations(self) -> AsyncDestinationsResource:
        return AsyncDestinationsResource(self._client)

    @cached_property
    def jobs(self) -> AsyncJobsResource:
        return AsyncJobsResource(self._client)

    @cached_property
    def schedules(self) -> AsyncSchedulesResource:
        return AsyncSchedulesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncDataExportsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncDataExportsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDataExportsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncDataExportsResourceWithStreamingResponse(self)

    @overload
    async def create_adhoc(
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
    ) -> AdHocResponse:
        """Trigger an ad-hoc Data Export.

        Each ad-hoc Export can be configured for
        exporting _only one of_ either Usage or Operational data:

        **Operational Data Exports**.

        - **Entity Types**. Use the `operationalDataTypes` parameter to specify the
          entities whose operational data you want to include in the ad-hoc export.
        - **Export Files**. For each of the entity types you select, when the ad-hoc
          export runs a separate file is compiled containing the operational data for
          all entities of that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          ad-hoc export.
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

        **Date Range for Operational Data Exports**. To restrict the operational data
        included in the ad-hoc export by a date/time range, use the `startDate`
        date/time request parameter to specify the start of the time period. The export
        will include all operational data from the specified `startDate` up until the
        date/time the export job runs.

        **Date Range for Usage Data Exports**. To restrict the usage data included in
        the ad-hoc export by date/time range, use the `startDate` and `endDate`
        date/time parameters:

        - Both `startDate` and `endDate` are required.
        - `endDate` must be after `startDate`.
        - `endDate` cannot be after tomorrow at midnight UTC. For example if today is
          May 20th 2025, you can only choose `endDate` to be equal or before
          2025-05-21T00:00:00.000Z.

        **NOTE:** You can use the ExportJob `id` returned to check the status of the
        triggered ad-hoc export. See the
        [ExportJob](https://www.m3ter.com/docs/api#tag/ExportJob) section of this API
        Reference.

        Args:
          operational_data_types: The list of the operational data types should be exported for.

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
    async def create_adhoc(
        self,
        *,
        org_id: str | None = None,
        source_type: Literal["USAGE"],
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[data_export_create_adhoc_params.AdHocUsageDataRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[data_export_create_adhoc_params.AdHocUsageDataRequestDimensionFilter] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AdHocResponse:
        """Trigger an ad-hoc Data Export.

        Each ad-hoc Export can be configured for
        exporting _only one of_ either Usage or Operational data:

        **Operational Data Exports**.

        - **Entity Types**. Use the `operationalDataTypes` parameter to specify the
          entities whose operational data you want to include in the ad-hoc export.
        - **Export Files**. For each of the entity types you select, when the ad-hoc
          export runs a separate file is compiled containing the operational data for
          all entities of that type that exist in your Organization

        **Usage Data Exports**.

        - Select the Meters and Accounts whose usage data you want to include in the
          ad-hoc export.
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

        **Date Range for Operational Data Exports**. To restrict the operational data
        included in the ad-hoc export by a date/time range, use the `startDate`
        date/time request parameter to specify the start of the time period. The export
        will include all operational data from the specified `startDate` up until the
        date/time the export job runs.

        **Date Range for Usage Data Exports**. To restrict the usage data included in
        the ad-hoc export by date/time range, use the `startDate` and `endDate`
        date/time parameters:

        - Both `startDate` and `endDate` are required.
        - `endDate` must be after `startDate`.
        - `endDate` cannot be after tomorrow at midnight UTC. For example if today is
          May 20th 2025, you can only choose `endDate` to be equal or before
          2025-05-21T00:00:00.000Z.

        **NOTE:** You can use the ExportJob `id` returned to check the status of the
        triggered ad-hoc export. See the
        [ExportJob](https://www.m3ter.com/docs/api#tag/ExportJob) section of this API
        Reference.

        Args:
          source_type: The type of data to export. Possible values are: USAGE

          account_ids: List of account IDs for which the usage data will be exported.

          aggregations: List of aggregations to apply

          dimension_filters: List of dimension filters to apply

          end_date: The exclusive end date for the data export.

          groups: List of groups to apply

          meter_ids: List of meter IDs for which the usage data will be exported.

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

    @required_args(["operational_data_types", "source_type"], ["source_type"])
    async def create_adhoc(
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
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[data_export_create_adhoc_params.AdHocUsageDataRequestAggregation] | Omit = omit,
        dimension_filters: Iterable[data_export_create_adhoc_params.AdHocUsageDataRequestDimensionFilter] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AdHocResponse:
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return await self._post(
            f"/organizations/{org_id}/dataexports/adhoc",
            body=await async_maybe_transform(
                {
                    "operational_data_types": operational_data_types,
                    "source_type": source_type,
                    "version": version,
                    "account_ids": account_ids,
                    "aggregations": aggregations,
                    "dimension_filters": dimension_filters,
                    "end_date": end_date,
                    "groups": groups,
                    "meter_ids": meter_ids,
                },
                data_export_create_adhoc_params.DataExportCreateAdhocParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AdHocResponse,
        )


class DataExportsResourceWithRawResponse:
    def __init__(self, data_exports: DataExportsResource) -> None:
        self._data_exports = data_exports

        self.create_adhoc = to_raw_response_wrapper(
            data_exports.create_adhoc,
        )

    @cached_property
    def destinations(self) -> DestinationsResourceWithRawResponse:
        return DestinationsResourceWithRawResponse(self._data_exports.destinations)

    @cached_property
    def jobs(self) -> JobsResourceWithRawResponse:
        return JobsResourceWithRawResponse(self._data_exports.jobs)

    @cached_property
    def schedules(self) -> SchedulesResourceWithRawResponse:
        return SchedulesResourceWithRawResponse(self._data_exports.schedules)


class AsyncDataExportsResourceWithRawResponse:
    def __init__(self, data_exports: AsyncDataExportsResource) -> None:
        self._data_exports = data_exports

        self.create_adhoc = async_to_raw_response_wrapper(
            data_exports.create_adhoc,
        )

    @cached_property
    def destinations(self) -> AsyncDestinationsResourceWithRawResponse:
        return AsyncDestinationsResourceWithRawResponse(self._data_exports.destinations)

    @cached_property
    def jobs(self) -> AsyncJobsResourceWithRawResponse:
        return AsyncJobsResourceWithRawResponse(self._data_exports.jobs)

    @cached_property
    def schedules(self) -> AsyncSchedulesResourceWithRawResponse:
        return AsyncSchedulesResourceWithRawResponse(self._data_exports.schedules)


class DataExportsResourceWithStreamingResponse:
    def __init__(self, data_exports: DataExportsResource) -> None:
        self._data_exports = data_exports

        self.create_adhoc = to_streamed_response_wrapper(
            data_exports.create_adhoc,
        )

    @cached_property
    def destinations(self) -> DestinationsResourceWithStreamingResponse:
        return DestinationsResourceWithStreamingResponse(self._data_exports.destinations)

    @cached_property
    def jobs(self) -> JobsResourceWithStreamingResponse:
        return JobsResourceWithStreamingResponse(self._data_exports.jobs)

    @cached_property
    def schedules(self) -> SchedulesResourceWithStreamingResponse:
        return SchedulesResourceWithStreamingResponse(self._data_exports.schedules)


class AsyncDataExportsResourceWithStreamingResponse:
    def __init__(self, data_exports: AsyncDataExportsResource) -> None:
        self._data_exports = data_exports

        self.create_adhoc = async_to_streamed_response_wrapper(
            data_exports.create_adhoc,
        )

    @cached_property
    def destinations(self) -> AsyncDestinationsResourceWithStreamingResponse:
        return AsyncDestinationsResourceWithStreamingResponse(self._data_exports.destinations)

    @cached_property
    def jobs(self) -> AsyncJobsResourceWithStreamingResponse:
        return AsyncJobsResourceWithStreamingResponse(self._data_exports.jobs)

    @cached_property
    def schedules(self) -> AsyncSchedulesResourceWithStreamingResponse:
        return AsyncSchedulesResourceWithStreamingResponse(self._data_exports.schedules)
