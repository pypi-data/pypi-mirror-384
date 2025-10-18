# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["StatementJobResponse"]


class StatementJobResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    bill_id: Optional[str] = FieldInfo(alias="billId", default=None)
    """The unique identifier (UUID) of the bill associated with the StatementJob."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created this StatementJob."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time _(in ISO-8601 format)_ when the StatementJob was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The date and time _(in ISO-8601 format)_ when the StatementJob was last
    modified.
    """

    include_csv_format: Optional[bool] = FieldInfo(alias="includeCsvFormat", default=None)
    """
    A Boolean value indicating whether the generated statement includes a CSV
    format.

    - TRUE - includes the statement in CSV format.
    - FALSE - no CSV format statement.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) of the user who last modified this StatementJob."""

    org_id: Optional[str] = FieldInfo(alias="orgId", default=None)
    """The unique identifier (UUID) of your Organization.

    The Organization represents your company as a direct customer of our service.
    """

    presigned_json_statement_url: Optional[str] = FieldInfo(alias="presignedJsonStatementUrl", default=None)
    """The URL to access the generated statement in JSON format.

    This URL is temporary and has a limited lifetime.
    """

    statement_job_status: Optional[Literal["PENDING", "RUNNING", "COMPLETE", "CANCELLED", "FAILED"]] = FieldInfo(
        alias="statementJobStatus", default=None
    )
    """The current status of the StatementJob.

    The status helps track the progress and outcome of a StatementJob.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
