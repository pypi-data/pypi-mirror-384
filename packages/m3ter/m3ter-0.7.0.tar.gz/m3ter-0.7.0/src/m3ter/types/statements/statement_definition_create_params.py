# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["StatementDefinitionCreateParams", "Dimension", "Measure"]


class StatementDefinitionCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    aggregation_frequency: Required[
        Annotated[
            Literal["DAY", "WEEK", "MONTH", "QUARTER", "YEAR", "WHOLE_PERIOD"],
            PropertyInfo(alias="aggregationFrequency"),
        ]
    ]
    """This specifies how often the Statement should aggregate data."""

    dimensions: Iterable[Dimension]
    """
    An array of objects, each representing a Dimension data field from a Meter _(for
    Meters that have Dimensions setup)_.
    """

    generate_slim_statements: Annotated[bool, PropertyInfo(alias="generateSlimStatements")]

    include_price_per_unit: Annotated[bool, PropertyInfo(alias="includePricePerUnit")]
    """A Boolean indicating whether to include the price per unit in the Statement.

    - TRUE - includes the price per unit.
    - FALSE - excludes the price per unit.
    """

    measures: Iterable[Measure]
    """An array of objects, each representing a Measure data field from a Meter."""

    name: str
    """Descriptive name for the StatementDefinition providing context and information."""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """


class Dimension(TypedDict, total=False):
    filter: Required[SequenceNotStr[str]]
    """The value of a Dimension to use as a filter.

    Use "\\**" as a wildcard to filter on all Dimension values.
    """

    name: Required[str]
    """The name of the Dimension to target in the Meter."""

    attributes: SequenceNotStr[str]
    """The Dimension attribute to target."""

    meter_id: Annotated[str, PropertyInfo(alias="meterId")]
    """The unique identifier (UUID) of the Meter containing this Dimension."""


class Measure(TypedDict, total=False):
    aggregations: List[Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE", "CUSTOM_SQL"]]
    """A list of Aggregations to apply to the Measure."""

    meter_id: Annotated[str, PropertyInfo(alias="meterId")]
    """The unique identifier (UUID) of the Meter containing this Measure."""

    name: str
    """The name of a Measure data field \\**(or blank to indicate a wildcard, i.e.

    all fields)\\**. Default value is blank.
    """
