# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["IntegrationConfigurationUpdateParams", "Credentials"]


class IntegrationConfigurationUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    destination: Required[str]
    """Denotes the integration destination.

    This field identifies the target platform or service for the integration.
    """

    entity_type: Required[Annotated[str, PropertyInfo(alias="entityType")]]
    """
    Specifies the type of entity for which the integration configuration is being
    updated. Must be a valid alphanumeric string.
    """

    config_data: Annotated[Dict[str, object], PropertyInfo(alias="configData")]
    """
    A flexible object to include any additional configuration data specific to the
    integration.
    """

    credentials: Credentials
    """
    Base model for defining integration credentials across different types of
    integrations.
    """

    destination_id: Annotated[str, PropertyInfo(alias="destinationId")]
    """The unique identifier (UUID) for the integration destination."""

    entity_id: Annotated[str, PropertyInfo(alias="entityId")]
    """The unique identifier (UUID) of the entity.

    This field is used to specify which entity's integration configuration you're
    updating.
    """

    integration_credentials_id: Annotated[str, PropertyInfo(alias="integrationCredentialsId")]

    name: str

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """


class Credentials(TypedDict, total=False):
    type: Required[
        Literal[
            "HTTP_BASIC",
            "OAUTH_CLIENT_CREDENTIALS",
            "M3TER_SIGNED_REQUEST",
            "AWS_INTEGRATION",
            "PADDLE_AUTH",
            "NETSUITE_AUTH",
            "CHARGEBEE_AUTH",
            "M3TER_SERVICE_USER",
            "STRIPE_SIGNED_REQUEST",
            "HUBSPOT_ACCESS_TOKEN",
            "HUBSPOT_CLIENT_SECRET",
            "OPSGENIE_KEY",
            "SAP_BYD",
        ]
    ]
    """Specifies the type of authorization required for the integration."""

    destination: Literal[
        "WEBHOOK",
        "NETSUITE",
        "STRIPE",
        "STRIPE_TEST",
        "AWS",
        "PADDLE",
        "PADDLE_SANDBOX",
        "SALESFORCE",
        "XERO",
        "CHARGEBEE",
        "QUICKBOOKS",
        "QUICKBOOKS_SANDBOX",
        "M3TER",
    ]

    empty: bool
    """A flag to indicate whether the credentials are empty.

    - TRUE - empty credentials.
    - FALSE - credential details required.
    """

    name: str
    """The name of the credentials"""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
