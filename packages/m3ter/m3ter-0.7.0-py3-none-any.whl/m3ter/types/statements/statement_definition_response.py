# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["StatementDefinitionResponse", "Dimension", "Measure"]


class Dimension(BaseModel):
    filter: List[str]
    """The value of a Dimension to use as a filter.

    Use "\\**" as a wildcard to filter on all Dimension values.
    """

    name: str
    """The name of the Dimension to target in the Meter."""

    attributes: Optional[List[str]] = None
    """The Dimension attribute to target."""

    meter_id: Optional[str] = FieldInfo(alias="meterId", default=None)
    """The unique identifier (UUID) of the Meter containing this Dimension."""


class Measure(BaseModel):
    aggregations: Optional[List[Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE", "CUSTOM_SQL"]]] = None
    """A list of Aggregations to apply to the Measure."""

    meter_id: Optional[str] = FieldInfo(alias="meterId", default=None)
    """The unique identifier (UUID) of the Meter containing this Measure."""

    name: Optional[str] = None
    """The name of a Measure data field \\**(or blank to indicate a wildcard, i.e.

    all fields)\\**. Default value is blank.
    """


class StatementDefinitionResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    aggregation_frequency: Optional[Literal["DAY", "WEEK", "MONTH", "QUARTER", "YEAR", "WHOLE_PERIOD"]] = FieldInfo(
        alias="aggregationFrequency", default=None
    )
    """This specifies how often the Statement should aggregate data."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created this StatementDefinition."""

    dimensions: Optional[List[Dimension]] = None
    """
    An array of objects, each representing a Dimension data field from a Meter _(for
    Meters that have Dimensions setup)_.
    """

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """
    The date and time _(in ISO-8601 format)_ when the StatementDefinition was
    created.
    """

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The date and time _(in ISO-8601 format)_ when the StatementDefinition was last
    modified.
    """

    generate_slim_statements: Optional[bool] = FieldInfo(alias="generateSlimStatements", default=None)

    include_price_per_unit: Optional[bool] = FieldInfo(alias="includePricePerUnit", default=None)
    """A Boolean indicating whether to include the price per unit in the Statement.

    - TRUE - includes the price per unit.
    - FALSE - excludes the price per unit.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """
    The unique identifier (UUID) of the user who last modified this
    StatementDefinition.
    """

    measures: Optional[List[Measure]] = None
    """An array of objects, each representing a Measure data field from a Meter."""

    name: Optional[str] = None
    """Descriptive name for the StatementDefinition providing context and information."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
