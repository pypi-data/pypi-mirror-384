# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["UserMeResponse", "Organization", "ServiceUser", "User"]


class Organization(BaseModel):
    id: str
    """The UUID of the entity."""

    address_line1: Optional[str] = FieldInfo(alias="addressLine1", default=None)

    address_line2: Optional[str] = FieldInfo(alias="addressLine2", default=None)

    address_line3: Optional[str] = FieldInfo(alias="addressLine3", default=None)

    address_line4: Optional[str] = FieldInfo(alias="addressLine4", default=None)

    billing_contact_user_id1: Optional[str] = FieldInfo(alias="billingContactUserId1", default=None)

    billing_contact_user_id2: Optional[str] = FieldInfo(alias="billingContactUserId2", default=None)

    billing_contact_user_id3: Optional[str] = FieldInfo(alias="billingContactUserId3", default=None)

    country: Optional[str] = None

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this organization."""

    customer_id: Optional[str] = FieldInfo(alias="customerId", default=None)

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the organization was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the organization was last modified."""

    invoice_general_reference: Optional[str] = FieldInfo(alias="invoiceGeneralReference", default=None)

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this organization."""

    locality: Optional[str] = None

    organization_name: Optional[str] = FieldInfo(alias="organizationName", default=None)

    org_id: Optional[str] = FieldInfo(alias="orgId", default=None)

    post_code: Optional[str] = FieldInfo(alias="postCode", default=None)

    purchase_order_number: Optional[str] = FieldInfo(alias="purchaseOrderNumber", default=None)

    region: Optional[str] = None

    short_name: Optional[str] = FieldInfo(alias="shortName", default=None)

    status: Optional[Literal["ACTIVE", "ARCHIVED"]] = None

    tax_id: Optional[str] = FieldInfo(alias="taxId", default=None)

    type: Optional[Literal["PRODUCTION", "SANDBOX"]] = None

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """


class ServiceUser(BaseModel):
    id: Optional[str] = None

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this service user."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the service user was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the service user was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this service user."""

    name: Optional[str] = None

    version: Optional[int] = None


class User(BaseModel):
    id: Optional[str] = None
    """The unique identifier (UUID) of this user."""

    contact_number: Optional[str] = FieldInfo(alias="contactNumber", default=None)
    """The user's contact telephone number."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The user who created this user."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time _(in ISO-8601 format)_ when the user was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The date and time _(in ISO-8601 format)_ when the user was last modified."""

    email: Optional[str] = None
    """The email address for this user."""

    first_accepted_terms_and_conditions: Optional[datetime] = FieldInfo(
        alias="firstAcceptedTermsAndConditions", default=None
    )
    """
    The date and time _(in ISO 8601 format)_ when this user first accepted the the
    m3ter terms and conditions.
    """

    first_name: Optional[str] = FieldInfo(alias="firstName", default=None)
    """The first name of the user."""

    last_accepted_terms_and_conditions: Optional[datetime] = FieldInfo(
        alias="lastAcceptedTermsAndConditions", default=None
    )
    """
    The date and time _(in ISO 8601 format)_ when this user last accepted the the
    m3ter terms and conditions.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) of the user who last modified this user record."""

    last_name: Optional[str] = FieldInfo(alias="lastName", default=None)
    """The surname of the user."""

    organizations: Optional[List[str]] = None
    """An array listing the Organizations where this user has access."""

    support_user: Optional[bool] = FieldInfo(alias="supportUser", default=None)
    """Indicates whether this is a m3ter Support user."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """


class UserMeResponse(BaseModel):
    organization: Optional[Organization] = None

    service_user: Optional[ServiceUser] = FieldInfo(alias="serviceUser", default=None)

    user: Optional[User] = None
