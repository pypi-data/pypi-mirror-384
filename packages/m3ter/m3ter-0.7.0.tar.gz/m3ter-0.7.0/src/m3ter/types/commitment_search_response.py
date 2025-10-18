# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .commitment_response import CommitmentResponse

__all__ = ["CommitmentSearchResponse"]


class CommitmentSearchResponse(BaseModel):
    data: Optional[List[CommitmentResponse]] = None

    next_token: Optional[str] = FieldInfo(alias="nextToken", default=None)
