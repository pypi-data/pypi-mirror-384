# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["StatementJobCreateParams"]


class StatementJobCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    bill_id: Required[Annotated[str, PropertyInfo(alias="billId")]]
    """The unique identifier (UUID) of the bill associated with the StatementJob."""

    include_csv_format: Annotated[bool, PropertyInfo(alias="includeCsvFormat")]
    """
    A Boolean value indicating whether the generated statement includes a CSV
    format.

    - TRUE - includes the statement in CSV format.
    - FALSE - no CSV format statement.
    """

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
