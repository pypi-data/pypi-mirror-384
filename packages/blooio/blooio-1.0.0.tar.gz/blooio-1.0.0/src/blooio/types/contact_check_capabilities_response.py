# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ContactCheckCapabilitiesResponse", "Capabilities"]


class Capabilities(BaseModel):
    imessage: Optional[bool] = None
    """Whether this contact supports iMessage."""

    sms: Optional[bool] = None
    """
    Whether this contact supports SMS (always true for phone numbers, false for
    emails).
    """


class ContactCheckCapabilitiesResponse(BaseModel):
    capabilities: Optional[Capabilities] = None
    """Messaging capabilities for this contact."""

    contact: Optional[str] = None
    """The contact identifier (phone number or email)."""

    last_checked: Optional[datetime] = FieldInfo(alias="lastChecked", default=None)
    """ISO 8601 timestamp of when capabilities were last checked."""

    type: Optional[Literal["phone", "email"]] = None
    """Type of contact identifier."""
