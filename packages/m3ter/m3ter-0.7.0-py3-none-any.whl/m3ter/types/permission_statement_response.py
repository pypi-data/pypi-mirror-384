# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["PermissionStatementResponse"]


class PermissionStatementResponse(BaseModel):
    action: List[
        Literal[
            "ALL",
            "CONFIG_CREATE",
            "CONFIG_RETRIEVE",
            "CONFIG_UPDATE",
            "CONFIG_DELETE",
            "CONFIG_EXPORT",
            "ANALYTICS_QUERY",
            "MEASUREMENTS_UPLOAD",
            "MEASUREMENTS_FILEUPLOAD",
            "MEASUREMENTS_RETRIEVE",
            "MEASUREMENTS_EXPORT",
            "FORECAST_RETRIEVE",
            "HEALTHSCORES_RETRIEVE",
            "ANOMALIES_RETRIEVE",
            "EXPORTS_DOWNLOAD",
            "MARKETPLACE_USAGE_CREATE",
            "MARKETPLACE_USAGE_RETRIEVE",
        ]
    ]
    """
    The actions available to users who are assigned the Permission Policy - what
    they can do or cannot do with respect to the specified resource.

    **NOTE:** Use lower case and a colon-separated format, for example, if you want
    to confer full CRUD, use:

    ```
    "config:create",
    "config:delete",
    "config:retrieve",
    "config:update"
    ```
    """

    effect: Literal["ALLOW", "DENY"]
    """
    Specifies whether or not the user is allowed to perform the action on the
    resource.

    **NOTE:** Use lower case, for example: `"allow"`. If you use upper case, you'll
    receive an error.
    """

    resource: List[str]
    """
    See
    [Statements - Available Resources](https://www.m3ter.com/docs/guides/managing-organization-and-users/creating-and-managing-permissions#statements---available-resources)
    for a listing of available resources for Permission Policy statements.
    """
