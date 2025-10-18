# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["EventGetFieldsParams"]


class EventGetFieldsParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    event_name: Annotated[str, PropertyInfo(alias="eventName")]
    """
    The name of the specific Event Type to use as a list filter, for example
    `configuration.commitment.created`.
    """
