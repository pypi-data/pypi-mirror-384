# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["NotificationConfigurationResponse"]


class NotificationConfigurationResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    code: str
    """The short code for the Notification."""

    description: str
    """
    The description for the Notification providing a brief overview of its purpose
    and functionality.
    """

    name: str
    """The name of the Notification."""

    active: Optional[bool] = None
    """A Boolean flag indicating whether or not the Notification is active.

    - **TRUE** - active Notification.
    - **FALSE** - inactive Notification.
    """

    always_fire_event: Optional[bool] = FieldInfo(alias="alwaysFireEvent", default=None)
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

    calculation: Optional[str] = None
    """A logical expression that that is evaluated to a Boolean.

    If it evaluates as `True`, a Notification for the Event is created and sent to
    the configured destination. Calculations can reference numeric, string, and
    boolean Event fields.

    See
    [Creating Calculations](https://www.m3ter.com/docs/guides/utilizing-events-and-notifications/key-concepts-and-relationships#creating-calculations)
    in the m3ter documentation for more information.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created this item."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when this item was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when this item was last modified _(in ISO-8601 format)_."""

    event_name: Optional[str] = FieldInfo(alias="eventName", default=None)
    """The name of the Event that the Notification is based on.

    When this Event occurs and the calculation evaluates to `True`, the Notification
    is triggered.

    **Note:** If the Notification is set to always fire, then the Notification will
    always be sent when the Event it is based on occurs, and without any other
    conditions defined by a calculation having to be met.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified this item."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
