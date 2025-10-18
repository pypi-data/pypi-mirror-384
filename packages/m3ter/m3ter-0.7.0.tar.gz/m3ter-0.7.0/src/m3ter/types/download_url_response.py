# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["DownloadURLResponse"]


class DownloadURLResponse(BaseModel):
    url: Optional[str] = None
    """The presigned download URL"""
