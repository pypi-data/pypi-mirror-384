# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["SubmitMeasurementsResponse"]


class SubmitMeasurementsResponse(BaseModel):
    result: Optional[str] = None
    """`accepted` is returned when successful."""
