# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ScheduleListResponse"]


class ScheduleListResponse(BaseModel):
    id: str
    """The id of the Data Export Schedule."""

    code: Optional[str] = None
    """Unique short code of the Data Export Schedule."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this Schedule."""

    destination_ids: Optional[List[str]] = FieldInfo(alias="destinationIds", default=None)
    """The Export Destination ids."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the Data Export Schedule was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the Schedule was last modified."""

    export_file_format: Optional[Literal["CSV", "JSON", "JSONL"]] = FieldInfo(alias="exportFileFormat", default=None)

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this Data Export Schedule."""

    name: Optional[str] = None
    """The name of the Data Export Schedule."""

    period: Optional[int] = None
    """
    Defines the Schedule frequency for the Data Export to run in Hours, Days, or
    Minutes. Used in conjunction with the `scheduleType` parameter.
    """

    schedule_type: Optional[Literal["HOUR", "DAY", "MINUTE", "AD_HOC"]] = FieldInfo(alias="scheduleType", default=None)

    source_type: Optional[Literal["USAGE", "OPERATIONAL"]] = FieldInfo(alias="sourceType", default=None)

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
