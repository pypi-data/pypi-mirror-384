# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["DataExportDestinationResponse"]


class DataExportDestinationResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    code: Optional[str] = None
    """The code of the data Export Destination."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created the Export Destination."""

    destination_type: Optional[Literal["S3", "GCS"]] = FieldInfo(alias="destinationType", default=None)

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the Export Destination was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the Export Destination was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified the Export Destination."""

    name: Optional[str] = None
    """The name of the data Export Destination."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
