# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ObjectURLResponse"]


class ObjectURLResponse(BaseModel):
    download_url: Optional[str] = FieldInfo(alias="downloadUrl", default=None)
    """The pre-signed download URL."""
