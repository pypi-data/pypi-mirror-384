# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["InvitationCreateParams"]


class InvitationCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    email: Required[str]

    first_name: Required[Annotated[str, PropertyInfo(alias="firstName")]]

    last_name: Required[Annotated[str, PropertyInfo(alias="lastName")]]

    contact_number: Annotated[str, PropertyInfo(alias="contactNumber")]

    dt_end_access: Annotated[Union[str, datetime], PropertyInfo(alias="dtEndAccess", format="iso8601")]
    """The date when access will end for the user _(in ISO-8601 format)_.

    Leave blank for no end date, which gives the user permanent access.
    """

    dt_expiry: Annotated[Union[str, datetime], PropertyInfo(alias="dtExpiry", format="iso8601")]
    """The date when the invite expires _(in ISO-8601 format)_.

    After this date the invited user can no longer accept the invite. By default,
    any invite is valid for 30 days from the date the invite is sent.
    """

    m3ter_user: Annotated[bool, PropertyInfo(alias="m3terUser")]

    permission_policy_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="permissionPolicyIds")]
    """The IDs of the permission policies the invited user has been assigned.

    This controls the access rights and privileges that this user will have when
    working in the m3ter Organization.
    """

    version: int
