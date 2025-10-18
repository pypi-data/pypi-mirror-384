# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["FileUploadJobResponse"]


class FileUploadJobResponse(BaseModel):
    id: Optional[str] = None
    """UUID of the file upload job."""

    content_length: Optional[int] = FieldInfo(alias="contentLength", default=None)
    """The size of the body in bytes.

    For example: `"contentLength": 485`, where 485 is the size in bytes of the file
    uploaded.
    """

    failed_rows: Optional[int] = FieldInfo(alias="failedRows", default=None)
    """The number of rows that failed processing during ingest."""

    file_name: Optional[str] = FieldInfo(alias="fileName", default=None)
    """The name of the measurements file for the upload job."""

    processed_rows: Optional[int] = FieldInfo(alias="processedRows", default=None)
    """The number of rows that were processed during ingest."""

    status: Optional[Literal["notUploaded", "running", "failed", "succeeded"]] = None
    """The status of the file upload job."""

    total_rows: Optional[int] = FieldInfo(alias="totalRows", default=None)
    """The total number of rows in the file."""

    upload_date: Optional[str] = FieldInfo(alias="uploadDate", default=None)
    """The upload date for the upload job _(in ISO-8601 format)_."""

    version: Optional[int] = None
    """The version number. Default value when newly created is one."""
