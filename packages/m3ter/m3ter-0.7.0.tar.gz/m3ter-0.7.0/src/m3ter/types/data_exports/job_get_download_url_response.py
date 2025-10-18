# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["JobGetDownloadURLResponse"]


class JobGetDownloadURLResponse(BaseModel):
    expiration_time: Optional[datetime] = FieldInfo(alias="expirationTime", default=None)
    """The expiration time of the URL"""

    url: Optional[str] = None
    """The presigned download URL"""
