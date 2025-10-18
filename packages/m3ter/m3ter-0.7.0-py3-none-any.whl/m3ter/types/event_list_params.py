# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["EventListParams"]


class EventListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Annotated[str, PropertyInfo(alias="accountId")]
    """The Account ID associated with the Event to filter the results.

    Returns the Events that have been generated for the Account.
    """

    event_name: Annotated[Optional[str], PropertyInfo(alias="eventName")]

    event_type: Annotated[str, PropertyInfo(alias="eventType")]
    """The category of Events to filter the results by. Options:

    - Notification
    - IntegrationEvent
    - IngestValidationFailure
    - DataExportJobFailure
    """

    ids: SequenceNotStr[str]
    """List of Event UUIDs to filter the results.

    **NOTE:** cannot be used with other filters.
    """

    include_actioned: Annotated[bool, PropertyInfo(alias="includeActioned")]
    """A Boolean flag indicating whether to return Events that have been actioned.

    - **TRUE** - include actioned Events.
    - **FALSE** - exclude actioned Events.
    """

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of Events in a paginated list.
    """

    notification_code: Annotated[str, PropertyInfo(alias="notificationCode")]
    """Short code of the Notification to filter the results.

    Returns the Events that have triggered the Notification.
    """

    notification_id: Annotated[str, PropertyInfo(alias="notificationId")]
    """Notification UUID to filter the results.

    Returns the Events that have triggered the Notification.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """The maximum number of Events to retrieve per page."""

    resource_id: Annotated[Optional[str], PropertyInfo(alias="resourceId")]
