# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["EventResponse"]


class EventResponse(BaseModel):
    id: str
    """The uniqie identifier (UUID) of the Event."""

    dt_actioned: datetime = FieldInfo(alias="dtActioned")
    """When an Event was actioned. It follows the ISO 8601 date and time format.

    You can action an Event to indicate that it has been followed up and resolved -
    this is useful when dealing with integration error Events or ingest failure
    Events.
    """

    event_name: str = FieldInfo(alias="eventName")
    """The name of the Event as it is registered in the system.

    This name is used to categorize and trigger associated actions.
    """

    event_time: datetime = FieldInfo(alias="eventTime")
    """The time when the Event was triggered, using the ISO 8601 date and time format."""

    m3ter_event: object = FieldInfo(alias="m3terEvent")
    """The Data Transfer Object (DTO) containing the details of the Event."""
