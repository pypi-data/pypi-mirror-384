# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["DataExportJobResponse"]


class DataExportJobResponse(BaseModel):
    id: str
    """The id of the Export Job."""

    date_created: Optional[datetime] = FieldInfo(alias="dateCreated", default=None)
    """When the data Export Job was created."""

    schedule_id: Optional[str] = FieldInfo(alias="scheduleId", default=None)
    """The id of the data Export Schedule."""

    source_type: Optional[Literal["USAGE", "OPERATIONAL"]] = FieldInfo(alias="sourceType", default=None)

    started_at: Optional[datetime] = FieldInfo(alias="startedAt", default=None)
    """When the data Export Job started running"""

    status: Optional[Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED"]] = None

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
