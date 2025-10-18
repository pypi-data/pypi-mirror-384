# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["NotificationConfigurationListParams"]


class NotificationConfigurationListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    active: bool
    """
    A Boolean flag indicating whether to retrieve only active or only inactive
    Notifications.

    - **TRUE** - only active Notifications are returned.
    - **FALSE** - only inactive Notifications are returned.
    """

    event_name: Annotated[str, PropertyInfo(alias="eventName")]
    """
    Use this to filter the Notifications returned - only those Notifications that
    are based on the _Event type_ specified by `eventName` are returned.
    """

    ids: SequenceNotStr[str]
    """A list of specific Notification UUIDs to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of Notifications in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of Notifications to retrieve per page."""
