# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["WebhookSetActiveParams"]


class WebhookSetActiveParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    active: bool
    """active status of the webhook"""
