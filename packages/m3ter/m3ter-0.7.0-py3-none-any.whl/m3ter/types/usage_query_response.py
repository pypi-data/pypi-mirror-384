# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["UsageQueryResponse"]


class UsageQueryResponse(BaseModel):
    data: Optional[List[Dict[str, object]]] = None

    has_more_data: Optional[bool] = FieldInfo(alias="hasMoreData", default=None)
    """
    Boolean flag to indicate whether or not there are more data available for the
    query than are returned:

    - If there are more data, then TRUE.
    - If there are no more data, then FALSE.

    **NOTES:**

    - The limit on the size of the return is 20000 data items. If the query returns
      more than this limit, only 20000 items are returned with most recent first and
      `hasMoreData` will be TRUE.
    - If you have set `limit` in your query request at fewer than the number
      returned by the query, then `hasMoreData` will be TRUE in the response.
    """
