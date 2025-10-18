# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from .._models import BaseModel

__all__ = ["EventGetFieldsResponse"]


class EventGetFieldsResponse(BaseModel):
    events: Optional[Dict[str, Dict[str, str]]] = None
    """An object containing the list of Fields for the queried Event Type.

    See the 200 Response sample where we have queried to get the Fields for the
    `configuration.commitment.created` Event Type.

    **Note:** `new` represents the attributes the newly created object has.
    """
