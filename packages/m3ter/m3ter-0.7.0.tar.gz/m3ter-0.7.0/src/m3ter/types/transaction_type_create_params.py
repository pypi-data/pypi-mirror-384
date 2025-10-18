# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["TransactionTypeCreateParams"]


class TransactionTypeCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    name: Required[str]
    """The name of the entity."""

    archived: bool
    """A Boolean TRUE / FALSE flag indicating whether the entity is archived.

    An entity can be archived if it is obsolete.

    - TRUE - the entity is in the archived state.
    - FALSE - the entity is not in the archived state.
    """

    code: str
    """The short code for the entity."""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
