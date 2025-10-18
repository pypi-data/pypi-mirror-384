# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["MeRetrieveResponse", "Device", "IntegrationDetails", "Usage"]


class Device(BaseModel):
    device_hash: Optional[str] = None
    """Hashed device identifier."""

    is_active: Optional[bool] = None
    """Whether the device is currently active."""

    last_active: Optional[int] = None
    """Unix timestamp (ms) of last device activity."""


class IntegrationDetails(BaseModel):
    customer_webhook_url: Optional[str] = None
    """Webhook URL for API integrations."""

    metadata: Optional[object] = None
    """Integration-specific metadata."""

    name: Optional[str] = None
    """Name of the integration (GHL only)."""


class Usage(BaseModel):
    inbound_messages: Optional[int] = None
    """Total number of inbound messages."""

    last_message_sent: Optional[int] = None
    """Unix timestamp (ms) of the last message sent."""

    outbound_messages: Optional[int] = None
    """Total number of outbound messages."""


class MeRetrieveResponse(BaseModel):
    api_key: Optional[str] = None
    """The API key used for authentication."""

    devices: Optional[List[Device]] = None
    """List of devices associated with this API key."""

    integration_details: Optional[IntegrationDetails] = None
    """Integration-specific details (GHL or API integration)."""

    metadata: Optional[object] = None
    """Custom metadata associated with the API key."""

    plan: Optional[str] = None
    """The plan associated with this API key."""

    usage: Optional[Usage] = None
    """Usage statistics for this API key."""

    valid: Optional[bool] = None
    """Whether the API key is valid."""
