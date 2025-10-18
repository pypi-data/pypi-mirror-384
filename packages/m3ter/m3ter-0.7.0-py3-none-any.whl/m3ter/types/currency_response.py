# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["CurrencyResponse"]


class CurrencyResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    archived: Optional[bool] = None
    """TRUE / FALSE flag indicating whether the data entity is archived.

    An entity can be archived if it is obsolete.
    """

    code: Optional[str] = None
    """The short code of the data entity."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created this Currency."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time _(in ISO-8601 format)_ when the Currency was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The date and time _(in ISO-8601 format)_ when the Currency was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) of the user who last modified this Currency."""

    max_decimal_places: Optional[int] = FieldInfo(alias="maxDecimalPlaces", default=None)
    """This indicates the maximum number of decimal places to use for this Currency."""

    name: Optional[str] = None
    """The name of the data entity."""

    rounding_mode: Optional[
        Literal["UP", "DOWN", "CEILING", "FLOOR", "HALF_UP", "HALF_DOWN", "HALF_EVEN", "UNNECESSARY"]
    ] = FieldInfo(alias="roundingMode", default=None)

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
