# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["EventGetTypesResponse"]


class EventGetTypesResponse(BaseModel):
    events: Optional[List[str]] = None
    """
    An array containing a list of all Event Types for which Notification rules can
    be configured. Each Event Type is represented by a string.
    """
