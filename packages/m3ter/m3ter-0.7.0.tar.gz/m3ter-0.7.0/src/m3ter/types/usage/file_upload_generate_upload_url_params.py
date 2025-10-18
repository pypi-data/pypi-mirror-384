# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["FileUploadGenerateUploadURLParams"]


class FileUploadGenerateUploadURLParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    content_length: Required[Annotated[int, PropertyInfo(alias="contentLength")]]
    """The size of the body in bytes.

    For example: `"contentLength": 485`, where 485 is the size in bytes of the file
    to upload.

    **NOTE:** Required.
    """

    content_type: Required[Annotated[Literal["application/json", "text/json"], PropertyInfo(alias="contentType")]]
    """
    The media type of the entity body sent, for example:
    `"contentType":"text/json"`.

    **NOTE:** Currently only a JSON formatted file type is supported by the File
    Upload Service.
    """

    file_name: Required[Annotated[str, PropertyInfo(alias="fileName")]]
    """The name of the measurements file to be uploaded."""
