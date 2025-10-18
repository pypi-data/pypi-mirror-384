# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["InvitationResponse"]


class InvitationResponse(BaseModel):
    id: str
    """The UUID of the invitation."""

    accepted: bool
    """Boolean indicating whether the user has accepted the invitation.

    - TRUE - the invite has been accepted.
    - FALSE - the invite has not yet been accepted.
    """

    dt_end_access: datetime = FieldInfo(alias="dtEndAccess")
    """The date that access will end for the user _(in ISO-8601 format)_.

    If this is blank, there is no end date meaning that the user has permanent
    access.
    """

    dt_expiry: datetime = FieldInfo(alias="dtExpiry")
    """The date when the invite expires _(in ISO-8601 format)_.

    After this date the invited user can no longer accept the invite. By default,
    any invite is valid for 30 days from the date the invite is sent.
    """

    email: str
    """The email address of the invitee.

    The invitation will be sent to this email address.
    """

    first_name: str = FieldInfo(alias="firstName")
    """The first name of the invitee."""

    inviting_principal_id: str = FieldInfo(alias="invitingPrincipalId")
    """The UUID of the user who sent the invite."""

    last_name: str = FieldInfo(alias="lastName")
    """The surname of the invitee."""

    permission_policy_ids: List[str] = FieldInfo(alias="permissionPolicyIds")
    """The IDs of the permission policies the invited user has been assigned.

    This controls the access rights and privileges that this user will have when
    working in the m3ter Organization.
    """

    version: int
    """The version number. Default value when newly created is one."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The UUID of the user who created the invitation."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the invitation was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the invitation was last modified _(in ISO-8601 format)_."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The UUID of the user who last modified the invitation."""
