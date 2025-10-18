# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .bill_response import BillResponse

__all__ = ["BillSearchResponse"]


class BillSearchResponse(BaseModel):
    data: Optional[List[BillResponse]] = None

    next_token: Optional[str] = FieldInfo(alias="nextToken", default=None)
