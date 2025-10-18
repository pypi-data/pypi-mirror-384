# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["DataExplorerGroup"]


class DataExplorerGroup(BaseModel):
    group_type: Optional[Literal["ACCOUNT", "DIMENSION", "TIME"]] = FieldInfo(alias="groupType", default=None)
