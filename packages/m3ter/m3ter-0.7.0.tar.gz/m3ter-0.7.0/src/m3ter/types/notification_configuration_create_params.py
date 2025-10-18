# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["NotificationConfigurationCreateParams"]


class NotificationConfigurationCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    code: Required[str]
    """The short code for the Notification."""

    description: Required[str]
    """
    The description for the Notification providing a brief overview of its purpose
    and functionality.
    """

    event_name: Required[Annotated[str, PropertyInfo(alias="eventName")]]
    """The name of the _Event type_ that the Notification is based on.

    When an Event of this type occurs and any calculation built into the
    Notification evaluates to `True`, the Notification is triggered.

    **Note:** If the Notification is set to always fire, then the Notification will
    always be sent when the Event of the type it is based on occurs, and without any
    other conditions defined by a calculation having to be met.
    """

    name: Required[str]
    """The name of the Notification."""

    active: bool
    """Boolean flag that sets the Notification as active or inactive.

    Only active Notifications are sent when triggered by the Event they are based
    on:

    - **TRUE** - set Notification as active.
    - **FALSE** - set Notification as inactive.
    """

    always_fire_event: Annotated[bool, PropertyInfo(alias="alwaysFireEvent")]
    """
    A Boolean flag indicating whether the Notification is always triggered,
    regardless of other conditions and omitting reference to any calculation. This
    means the Notification will be triggered simply by the Event it is based on
    occurring and with no further conditions having to be met.

    - **TRUE** - the Notification is always triggered and omits any reference to the
      calculation to check for other conditions being true before triggering the
      Notification.
    - **FALSE** - the Notification is only triggered when the Event it is based on
      occurs and any calculation is checked and all conditions defined by the
      calculation are met.
    """

    calculation: str
    """A logical expression that that is evaluated to a Boolean.

    If it evaluates as `True`, a Notification for the Event is created and sent to
    the configured destination. Calculations can reference numeric, string, and
    boolean Event fields.

    See
    [Creating Calculations](https://www.m3ter.com/docs/guides/utilizing-events-and-notifications/key-concepts-and-relationships#creating-calculations)
    in the m3ter documentation for more information.
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
