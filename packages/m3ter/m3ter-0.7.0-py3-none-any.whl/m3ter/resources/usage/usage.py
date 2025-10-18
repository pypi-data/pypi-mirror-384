# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, AsyncIterable
from datetime import datetime

import httpx

from ...types import usage_query_params, usage_submit_params, usage_get_failed_ingest_download_url_params
from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from .file_uploads.file_uploads import (
    FileUploadsResource,
    AsyncFileUploadsResource,
    FileUploadsResourceWithRawResponse,
    AsyncFileUploadsResourceWithRawResponse,
    FileUploadsResourceWithStreamingResponse,
    AsyncFileUploadsResourceWithStreamingResponse,
)
from ...types.usage_query_response import UsageQueryResponse
from ...types.download_url_response import DownloadURLResponse
from ...types.data_explorer_group_param import DataExplorerGroupParam
from ...types.measurement_request_param import MeasurementRequestParam
from ...types.submit_measurements_response import SubmitMeasurementsResponse

__all__ = ["UsageResource", "AsyncUsageResource"]


def chunk_measurements(
    iterable: Iterable[MeasurementRequestParam], chunk_size: int = 1000
) -> Iterable[Iterable[MeasurementRequestParam]]:
    it = iter(iterable)
    while True:
        chunk: list[MeasurementRequestParam] = []
        try:
            for _ in range(chunk_size):
                chunk.append(next(it))
        except StopIteration:
            if chunk:
                yield chunk
            break
        yield chunk


class UsageResource(SyncAPIResource):
    @cached_property
    def file_uploads(self) -> FileUploadsResource:
        return FileUploadsResource(self._client)

    @cached_property
    def with_raw_response(self) -> UsageResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return UsageResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UsageResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return UsageResourceWithStreamingResponse(self)

    def get_failed_ingest_download_url(
        self,
        *,
        org_id: str | None = None,
        file: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DownloadURLResponse:
        """
        Returns a presigned download URL for failed ingest file download based on the
        file path provided.

        If a usage data ingest measurement you submit to the m3ter platform fails, an
        `ingest.validation.failure` Event is generated. Use this call to obtain a
        download URL which you can then use to download a file containing details of
        what went wrong with the attempted usage data measurement ingest, and allowing
        you to follow-up and resolve the issue.

        To obtain the `file` query parameter:

        - Use the
          [List Events](https://www.m3ter.com/docs/api#tag/Events/operation/ListEventFields)
          call with the `ingest.validation.failure` for the `eventName` query parameter.
        - The response contains a `getDownloadUrl` response parameter and this contains
          the file path you can use to obtain the failed ingest file download URL.

        **Notes:**

        - The presigned Url returned to use for failed ingest file download is
          time-bound and expires after 5 minutes.
        - If you make a List Events call for `ingest.validation.failure` Events in your
          Organization, then you can perform this **GET** call using the full URL
          returned for any ingest failure Event to obtain a failed ingest file download
          URL for the Event.

        Args:
          file: The file path

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
            f"/organizations/{org_id}/measurements/failedIngest/getDownloadUrl",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"file": file}, usage_get_failed_ingest_download_url_params.UsageGetFailedIngestDownloadURLParams
                ),
            ),
            cast_to=DownloadURLResponse,
        )

    def query(
        self,
        *,
        org_id: str | None = None,
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[usage_query_params.Aggregation] | Omit = omit,
        dimension_filters: Iterable[usage_query_params.DimensionFilter] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        limit: int | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UsageQueryResponse:
        """
        Query and filter usage data collected for your Organization.

        You can use several parameters to filter the range of usage data returned:

        - **Time period.** Use `startDate` and `endDate` to define a period. The query
          references the `timestamp` values of usage data submissions for applying the
          defined time period, and not the time submissions were `receivedAt` by the
          platform. Only usage data with a `timestamp` that falls in the defined time
          period are returned.(Required)
        - **Meters.** Specify the Meters you want the query to return data for.
        - **Accounts.** Specify the Accounts you want the query to return data for.
        - **Dimension Filters.** Specify values for Dimension data fields on included
          Meters. Only data that match the specified Dimension field values will be
          returned for the query.

        You can apply Aggregations functions to the usage data returned for the query.
        If you apply Aggregations, you can select to group the data by:

        - **Account**
        - **Time**
        - **Dimension**

        Args:
          account_ids: Specify the Accounts you want the query to return usage data for.

          aggregations: Define the Aggregation functions you want to apply to data fields on included
              Meters:

              - **SUM**. Adds the values.
              - **MIN**. Uses the minimum value.
              - **MAX**. Uses the maximum value.
              - **COUNT**. Counts the number of values.
              - **LATEST**. Uses the most recent value.
              - **MEAN**. Uses the arithmetic mean of the values.
              - **UNIQUE**. Uses a count of the number of unique values.

              **NOTE!** The Aggregation functions that can be applied depend on the data field
              type:

              - **Measure** fields. `SUM`, `MIN`, `MAX`, `COUNT`, `LATEST`, or `MEAN`
                functions can be applied.
              - **Dimension** field. `COUNT` or `UNIQUE` functions can be applied.

          dimension_filters: Define Dimension filters you want to apply for the query.

              Specify values for Dimension data fields on included Meters. Only data that
              match the specified Dimension field values will be returned for the query.

          end_date: The exclusive end date to define a time period to filter by. (_ISO 8601
              formatted_)

          groups: If you've applied Aggregations for your query, specify any grouping you want to
              impose on the returned data:

              - **Account**
              - **Time** - group by frequency. Five options: `DAY`, `HOUR`, `WEEK`, `MONTH`,
                or `QUARTER`.
              - **Dimension** - group by Meter and data field.

              **NOTE:** If you attempt to impose grouping for a query that doesn't apply
              Aggregations, you'll receive an error.

          limit: Define a limit for the number of usage data items you want the query to return,
              starting with the most recently received data item.

          meter_ids: Specify the Meters you want the query to return usage data for.

          start_date: The inclusive start date to define a time period to filter by. (_ISO 8601
              formatted_)

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
            f"/organizations/{org_id}/usage/query",
            body=maybe_transform(
                {
                    "account_ids": account_ids,
                    "aggregations": aggregations,
                    "dimension_filters": dimension_filters,
                    "end_date": end_date,
                    "groups": groups,
                    "limit": limit,
                    "meter_ids": meter_ids,
                    "start_date": start_date,
                },
                usage_query_params.UsageQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UsageQueryResponse,
        )

    def submit(
        self,
        *,
        org_id: str | None = None,
        measurements: Iterable[MeasurementRequestParam],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SubmitMeasurementsResponse:
        """Submit a measurement or multiple measurements to the m3ter platform.

        The maximum
        size of the payload needs to be less than 512,000 bytes.

        **NOTES:**

        - **Non-existent Accounts.** The `account` request parameter is required.
          However, if you want to submit a usage data measurement for an Account which
          does not yet exist in your Organization, you can use an `account` code for a
          non-existent Account. A new skeleton Account will be automatically created.
          The usage data measurement is accepted and ingested as data belonging to the
          new auto-created Account. At a later date, you can edit the Account's
          Code,??Name, and??e-mail address. For more details, see
          [Submitting Usage Data for Non-Existent Accounts](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/submitting-usage-data-for-non-existent-accounts)
          in our main documentation.
        - **Usage Data Adjustments.** If you need to make corrections for billing
          retrospectively against an Account, you can use date/time values in the past
          for the `ts` (timestamp) request parameter to submit positive or negative
          usage data amounts to correct and reconcile earlier billing anomalies. For
          more details, see
          [Submitting Usage Data Adjustments Using Timestamp](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/submitting-usage-data-adjustments-using-timestamp)
          in our main documentation.
        - **Ingest Validation Failure Events.** After the intial submission of a usage
          data measurement to the Ingest API, a data enrichment stage is performed to
          check for any errors in the usage data measurement, such as a missing field.
          If an error is identified, this might result in the submission being rejected.
          In these cases, an _ingest validation failure_ Event is generated, which you
          can review on the
          [Ingest Events](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/reviewing-and-resolving-ingest-events)
          page in the Console. See also the
          [Events](https://www.m3ter.com/docs/api#tag/Events) section in this API
          Reference.

        **IMPORTANT! - Use of PII:** The use of any of your end-customers' Personally
        Identifiable Information (PII) in m3ter is restricted to a few fields on the
        **Account** entity. Please ensure that any measurements you submit do not
        contain any end-customer PII data. See the
        [Introduction section](https://www.m3ter.com/docs/api#section/Introduction)
        above for more details.

        Args:
          measurements: Request containing the usage data measurements for submission.

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
            f"/organizations/{org_id}/measurements"
            if self._client._base_url_overridden
            else f"https://ingest.m3ter.com/organizations/{org_id}/measurements",
            body=maybe_transform({"measurements": measurements}, usage_submit_params.UsageSubmitParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SubmitMeasurementsResponse,
        )

    def submit_all(
        self,
        *,
        org_id: str | None = None,
        measurements: Iterable[MeasurementRequestParam],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Iterable[SubmitMeasurementsResponse]:
        """Submit a measurement or multiple measurements to the m3ter platform.

        **Automatically chunks the supplied measurements into lots of 1000 (the maximum in one batch)**

        The maximum
        size of the payload needs to be less than 512,000 bytes.

        **NOTES:**

        - **Non-existent Accounts.** The `account` request parameter is required.
          However, if you want to submit a usage data measurement for an Account which
          does not yet exist in your Organization, you can use an `account` code for a
          non-existent Account. A new skeleton Account will be automatically created.
          The usage data measurement is accepted and ingested as data belonging to the
          new auto-created Account. At a later date, you can edit the Account's
          Code,??Name, and??e-mail address. For more details, see
          [Submitting Usage Data for Non-Existent Accounts](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/submitting-usage-data-for-non-existent-accounts)
          in our main documentation.
        - **Usage Data Adjustments.** If you need to make corrections for billing
          retrospectively against an Account, you can use date/time values in the past
          for the `ts` (timestamp) request parameter to submit positive or negative
          usage data amounts to correct and reconcile earlier billing anomalies. For
          more details, see
          [Submitting Usage Data Adjustments Using Timestamp](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/submitting-usage-data-adjustments-using-timestamp)
          in our main documentation.
        - **Ingest Validation Failure Events.** After the intial submission of a usage
          data measurement to the Ingest API, a data enrichment stage is performed to
          check for any errors in the usage data measurement, such as a missing field.
          If an error is identified, this might result in the submission being rejected.
          In these cases, an _ingest validation failure_ Event is generated, which you
          can review on the
          [Ingest Events](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/reviewing-and-resolving-ingest-events)
          page in the Console. See also the
          [Events](https://www.m3ter.com/docs/api#tag/Events) section in this API
          Reference.

        **IMPORTANT! - Use of PII:** The use of any of your end-customers' Personally
        Identifiable Information (PII) in m3ter is restricted to a few fields on the
        **Account** entity. Please ensure that any measurements you submit do not
        contain any end-customer PII data. See the
        [Introduction section](https://www.m3ter.com/docs/api#section/Introduction)
        above for more details.

        Args:
          measurements: Request containing the usage data measurements for submission.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")

        # This endpoint exists on a different domain: ingest.m3ter.com in production
        base_url = str(self._client.base_url)
        ingest_url = base_url.replace("api.", "ingest.")

        for chunk in chunk_measurements(measurements):
            yield self._post(
                f"{ingest_url}/organizations/{org_id}/measurements",
                body=maybe_transform({"measurements": chunk}, usage_submit_params.UsageSubmitParams),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=SubmitMeasurementsResponse,
            )


class AsyncUsageResource(AsyncAPIResource):
    @cached_property
    def file_uploads(self) -> AsyncFileUploadsResource:
        return AsyncFileUploadsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncUsageResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncUsageResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUsageResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncUsageResourceWithStreamingResponse(self)

    async def get_failed_ingest_download_url(
        self,
        *,
        org_id: str | None = None,
        file: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DownloadURLResponse:
        """
        Returns a presigned download URL for failed ingest file download based on the
        file path provided.

        If a usage data ingest measurement you submit to the m3ter platform fails, an
        `ingest.validation.failure` Event is generated. Use this call to obtain a
        download URL which you can then use to download a file containing details of
        what went wrong with the attempted usage data measurement ingest, and allowing
        you to follow-up and resolve the issue.

        To obtain the `file` query parameter:

        - Use the
          [List Events](https://www.m3ter.com/docs/api#tag/Events/operation/ListEventFields)
          call with the `ingest.validation.failure` for the `eventName` query parameter.
        - The response contains a `getDownloadUrl` response parameter and this contains
          the file path you can use to obtain the failed ingest file download URL.

        **Notes:**

        - The presigned Url returned to use for failed ingest file download is
          time-bound and expires after 5 minutes.
        - If you make a List Events call for `ingest.validation.failure` Events in your
          Organization, then you can perform this **GET** call using the full URL
          returned for any ingest failure Event to obtain a failed ingest file download
          URL for the Event.

        Args:
          file: The file path

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
            f"/organizations/{org_id}/measurements/failedIngest/getDownloadUrl",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"file": file}, usage_get_failed_ingest_download_url_params.UsageGetFailedIngestDownloadURLParams
                ),
            ),
            cast_to=DownloadURLResponse,
        )

    async def query(
        self,
        *,
        org_id: str | None = None,
        account_ids: SequenceNotStr[str] | Omit = omit,
        aggregations: Iterable[usage_query_params.Aggregation] | Omit = omit,
        dimension_filters: Iterable[usage_query_params.DimensionFilter] | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        groups: Iterable[DataExplorerGroupParam] | Omit = omit,
        limit: int | Omit = omit,
        meter_ids: SequenceNotStr[str] | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UsageQueryResponse:
        """
        Query and filter usage data collected for your Organization.

        You can use several parameters to filter the range of usage data returned:

        - **Time period.** Use `startDate` and `endDate` to define a period. The query
          references the `timestamp` values of usage data submissions for applying the
          defined time period, and not the time submissions were `receivedAt` by the
          platform. Only usage data with a `timestamp` that falls in the defined time
          period are returned.(Required)
        - **Meters.** Specify the Meters you want the query to return data for.
        - **Accounts.** Specify the Accounts you want the query to return data for.
        - **Dimension Filters.** Specify values for Dimension data fields on included
          Meters. Only data that match the specified Dimension field values will be
          returned for the query.

        You can apply Aggregations functions to the usage data returned for the query.
        If you apply Aggregations, you can select to group the data by:

        - **Account**
        - **Time**
        - **Dimension**

        Args:
          account_ids: Specify the Accounts you want the query to return usage data for.

          aggregations: Define the Aggregation functions you want to apply to data fields on included
              Meters:

              - **SUM**. Adds the values.
              - **MIN**. Uses the minimum value.
              - **MAX**. Uses the maximum value.
              - **COUNT**. Counts the number of values.
              - **LATEST**. Uses the most recent value.
              - **MEAN**. Uses the arithmetic mean of the values.
              - **UNIQUE**. Uses a count of the number of unique values.

              **NOTE!** The Aggregation functions that can be applied depend on the data field
              type:

              - **Measure** fields. `SUM`, `MIN`, `MAX`, `COUNT`, `LATEST`, or `MEAN`
                functions can be applied.
              - **Dimension** field. `COUNT` or `UNIQUE` functions can be applied.

          dimension_filters: Define Dimension filters you want to apply for the query.

              Specify values for Dimension data fields on included Meters. Only data that
              match the specified Dimension field values will be returned for the query.

          end_date: The exclusive end date to define a time period to filter by. (_ISO 8601
              formatted_)

          groups: If you've applied Aggregations for your query, specify any grouping you want to
              impose on the returned data:

              - **Account**
              - **Time** - group by frequency. Five options: `DAY`, `HOUR`, `WEEK`, `MONTH`,
                or `QUARTER`.
              - **Dimension** - group by Meter and data field.

              **NOTE:** If you attempt to impose grouping for a query that doesn't apply
              Aggregations, you'll receive an error.

          limit: Define a limit for the number of usage data items you want the query to return,
              starting with the most recently received data item.

          meter_ids: Specify the Meters you want the query to return usage data for.

          start_date: The inclusive start date to define a time period to filter by. (_ISO 8601
              formatted_)

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
            f"/organizations/{org_id}/usage/query",
            body=await async_maybe_transform(
                {
                    "account_ids": account_ids,
                    "aggregations": aggregations,
                    "dimension_filters": dimension_filters,
                    "end_date": end_date,
                    "groups": groups,
                    "limit": limit,
                    "meter_ids": meter_ids,
                    "start_date": start_date,
                },
                usage_query_params.UsageQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UsageQueryResponse,
        )

    async def submit(
        self,
        *,
        org_id: str | None = None,
        measurements: Iterable[MeasurementRequestParam],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SubmitMeasurementsResponse:
        """Submit a measurement or multiple measurements to the m3ter platform.

        The maximum
        size of the payload needs to be less than 512,000 bytes.

        **NOTES:**

        - **Non-existent Accounts.** The `account` request parameter is required.
          However, if you want to submit a usage data measurement for an Account which
          does not yet exist in your Organization, you can use an `account` code for a
          non-existent Account. A new skeleton Account will be automatically created.
          The usage data measurement is accepted and ingested as data belonging to the
          new auto-created Account. At a later date, you can edit the Account's
          Code,??Name, and??e-mail address. For more details, see
          [Submitting Usage Data for Non-Existent Accounts](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/submitting-usage-data-for-non-existent-accounts)
          in our main documentation.
        - **Usage Data Adjustments.** If you need to make corrections for billing
          retrospectively against an Account, you can use date/time values in the past
          for the `ts` (timestamp) request parameter to submit positive or negative
          usage data amounts to correct and reconcile earlier billing anomalies. For
          more details, see
          [Submitting Usage Data Adjustments Using Timestamp](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/submitting-usage-data-adjustments-using-timestamp)
          in our main documentation.
        - **Ingest Validation Failure Events.** After the intial submission of a usage
          data measurement to the Ingest API, a data enrichment stage is performed to
          check for any errors in the usage data measurement, such as a missing field.
          If an error is identified, this might result in the submission being rejected.
          In these cases, an _ingest validation failure_ Event is generated, which you
          can review on the
          [Ingest Events](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/reviewing-and-resolving-ingest-events)
          page in the Console. See also the
          [Events](https://www.m3ter.com/docs/api#tag/Events) section in this API
          Reference.

        **IMPORTANT! - Use of PII:** The use of any of your end-customers' Personally
        Identifiable Information (PII) in m3ter is restricted to a few fields on the
        **Account** entity. Please ensure that any measurements you submit do not
        contain any end-customer PII data. See the
        [Introduction section](https://www.m3ter.com/docs/api#section/Introduction)
        above for more details.

        Args:
          measurements: Request containing the usage data measurements for submission.

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
            f"/organizations/{org_id}/measurements"
            if self._client._base_url_overridden
            else f"https://ingest.m3ter.com/organizations/{org_id}/measurements",
            body=await async_maybe_transform({"measurements": measurements}, usage_submit_params.UsageSubmitParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SubmitMeasurementsResponse,
        )

    async def submit_all(
        self,
        *,
        org_id: str | None = None,
        measurements: Iterable[MeasurementRequestParam],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncIterable[SubmitMeasurementsResponse]:
        """Submit a measurement or multiple measurements to the m3ter platform.

        **Automatically chunks the supplied measurements into lots of 1000 (the maximum in one batch)**

        The maximum
        size of the payload needs to be less than 512,000 bytes.

        **NOTES:**

        - **Non-existent Accounts.** The `account` request parameter is required.
          However, if you want to submit a usage data measurement for an Account which
          does not yet exist in your Organization, you can use an `account` code for a
          non-existent Account. A new skeleton Account will be automatically created.
          The usage data measurement is accepted and ingested as data belonging to the
          new auto-created Account. At a later date, you can edit the Account's
          Code,??Name, and??e-mail address. For more details, see
          [Submitting Usage Data for Non-Existent Accounts](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/submitting-usage-data-for-non-existent-accounts)
          in our main documentation.
        - **Usage Data Adjustments.** If you need to make corrections for billing
          retrospectively against an Account, you can use date/time values in the past
          for the `ts` (timestamp) request parameter to submit positive or negative
          usage data amounts to correct and reconcile earlier billing anomalies. For
          more details, see
          [Submitting Usage Data Adjustments Using Timestamp](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/submitting-usage-data-adjustments-using-timestamp)
          in our main documentation.
        - **Ingest Validation Failure Events.** After the intial submission of a usage
          data measurement to the Ingest API, a data enrichment stage is performed to
          check for any errors in the usage data measurement, such as a missing field.
          If an error is identified, this might result in the submission being rejected.
          In these cases, an _ingest validation failure_ Event is generated, which you
          can review on the
          [Ingest Events](https://www.m3ter.com/docs/guides/billing-and-usage-data/submitting-usage-data/reviewing-and-resolving-ingest-events)
          page in the Console. See also the
          [Events](https://www.m3ter.com/docs/api#tag/Events) section in this API
          Reference.

        **IMPORTANT! - Use of PII:** The use of any of your end-customers' Personally
        Identifiable Information (PII) in m3ter is restricted to a few fields on the
        **Account** entity. Please ensure that any measurements you submit do not
        contain any end-customer PII data. See the
        [Introduction section](https://www.m3ter.com/docs/api#section/Introduction)
        above for more details.

        Args:
          measurements: Request containing the usage data measurements for submission.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")

        # This endpoint exists on a different domain: ingest.m3ter.com in production
        base_url = str(self._client.base_url)
        ingest_url = base_url.replace("api.", "ingest.")

        for chunk in chunk_measurements(measurements):
            yield await self._post(
                f"{ingest_url}/organizations/{org_id}/measurements",
                body=maybe_transform({"measurements": chunk}, usage_submit_params.UsageSubmitParams),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=SubmitMeasurementsResponse,
            )


class UsageResourceWithRawResponse:
    def __init__(self, usage: UsageResource) -> None:
        self._usage = usage

        self.get_failed_ingest_download_url = to_raw_response_wrapper(
            usage.get_failed_ingest_download_url,
        )
        self.query = to_raw_response_wrapper(
            usage.query,
        )
        self.submit = to_raw_response_wrapper(
            usage.submit,
        )

    @cached_property
    def file_uploads(self) -> FileUploadsResourceWithRawResponse:
        return FileUploadsResourceWithRawResponse(self._usage.file_uploads)


class AsyncUsageResourceWithRawResponse:
    def __init__(self, usage: AsyncUsageResource) -> None:
        self._usage = usage

        self.get_failed_ingest_download_url = async_to_raw_response_wrapper(
            usage.get_failed_ingest_download_url,
        )
        self.query = async_to_raw_response_wrapper(
            usage.query,
        )
        self.submit = async_to_raw_response_wrapper(
            usage.submit,
        )

    @cached_property
    def file_uploads(self) -> AsyncFileUploadsResourceWithRawResponse:
        return AsyncFileUploadsResourceWithRawResponse(self._usage.file_uploads)


class UsageResourceWithStreamingResponse:
    def __init__(self, usage: UsageResource) -> None:
        self._usage = usage

        self.get_failed_ingest_download_url = to_streamed_response_wrapper(
            usage.get_failed_ingest_download_url,
        )
        self.query = to_streamed_response_wrapper(
            usage.query,
        )
        self.submit = to_streamed_response_wrapper(
            usage.submit,
        )

    @cached_property
    def file_uploads(self) -> FileUploadsResourceWithStreamingResponse:
        return FileUploadsResourceWithStreamingResponse(self._usage.file_uploads)


class AsyncUsageResourceWithStreamingResponse:
    def __init__(self, usage: AsyncUsageResource) -> None:
        self._usage = usage

        self.get_failed_ingest_download_url = async_to_streamed_response_wrapper(
            usage.get_failed_ingest_download_url,
        )
        self.query = async_to_streamed_response_wrapper(
            usage.query,
        )
        self.submit = async_to_streamed_response_wrapper(
            usage.submit,
        )

    @cached_property
    def file_uploads(self) -> AsyncFileUploadsResourceWithStreamingResponse:
        return AsyncFileUploadsResourceWithStreamingResponse(self._usage.file_uploads)
