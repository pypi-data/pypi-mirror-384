# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["BillApproveResponse"]


class BillApproveResponse(BaseModel):
    message: Optional[str] = None
    """
    A message indicating the success or failure of the Bills' approval, along with
    relevant details.
    """
