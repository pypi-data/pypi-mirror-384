# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["CompoundAggregationUpdateParams"]


class CompoundAggregationUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    calculation: Required[str]
    """String that represents the formula for the calculation.

    This formula determines how the CompoundAggregation value is calculated. The
    calculation can reference simple Aggregations or Custom Fields. This field is
    required when creating or updating a CompoundAggregation.

    **NOTE:** If a simple Aggregation referenced by a Compound Aggregation has a
    **Quantity per unit** defined or a **Rounding** defined, these will not be
    factored into the value used by the calculation. For example, if the simple
    Aggregation referenced has a base value of 100 and has **Quantity per unit** set
    at 10, the Compound Aggregation calculation _will use the base value of 100 not
    10_.
    """

    name: Required[str]
    """Descriptive name for the Aggregation."""

    quantity_per_unit: Required[Annotated[float, PropertyInfo(alias="quantityPerUnit")]]
    """Defines how much of a quantity equates to 1 unit.

    Used when setting the price per unit for billing purposes - if charging for
    kilobytes per second (KiBy/s) at rate of $0.25 per 500 KiBy/s, then set
    quantityPerUnit to 500 and price Plan at $0.25 per unit.

    **Note:** If `quantityPerUnit` is set to a value other than one, `rounding` is
    typically set to `"UP"`.
    """

    rounding: Required[Literal["UP", "DOWN", "NEAREST", "NONE"]]
    """
    Specifies how you want to deal with non-integer, fractional number Aggregation
    values.

    **NOTES:**

    - **NEAREST** rounds to the nearest half: 5.1 is rounded to 5, and 3.5 is
      rounded to 4.
    - Also used in combination with `quantityPerUnit`. Rounds the number of units
      after `quantityPerUnit` is applied. If you set `quantityPerUnit` to a value
      other than one, you would typically set Rounding to **UP**. For example,
      suppose you charge by kilobytes per second (KiBy/s), set `quantityPerUnit` =
      500, and set charge rate at $0.25 per unit used. If your customer used 48,900
      KiBy/s in a billing period, the charge would be 48,900 / 500 = 97.8 rounded up
      to 98 \\** 0.25 = $2.45.

    Enum: ???UP??? ???DOWN??? ???NEAREST??? ???NONE???
    """

    unit: Required[str]
    """
    User defined label for units shown for Bill line items, indicating to your
    customers what they are being charged for.
    """

    accounting_product_id: Annotated[str, PropertyInfo(alias="accountingProductId")]
    """
    Optional Product ID this Aggregation should be attributed to for accounting
    purposes
    """

    code: str
    """Code of the new Aggregation. A unique short code to identify the Aggregation."""

    custom_fields: Annotated[Dict[str, Union[str, float]], PropertyInfo(alias="customFields")]

    evaluate_null_aggregations: Annotated[bool, PropertyInfo(alias="evaluateNullAggregations")]
    """Boolean True / False flag:

    - **TRUE** - set to TRUE if you want to allow null values from the simple
      Aggregations referenced in the Compound Aggregation to be passed in. Simple
      Aggregations based on Meter Target Fields where no usage data is available
      will have null values.
    - **FALSE** Default.

    **Note:** If any of the simple Aggregations you reference in a Compound
    Aggregation calculation might have null values, you must set their Default Value
    to 0. This ensures that any null values passed into the Compound Aggregation are
    passed in correctly with value = 0.
    """

    product_id: Annotated[str, PropertyInfo(alias="productId")]
    """Unique identifier (UUID) of the Product the CompoundAggregation belongs to.

    **Note:** Omit this parameter if you want to create a _Global_
    CompoundAggregation.
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
