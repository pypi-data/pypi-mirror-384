# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["MessageRetrieveResponse"]


class MessageRetrieveResponse(BaseModel):
    api_key: Optional[str] = None

    attachments_count: Optional[int] = None

    direction: Optional[Literal["outbound", "inbound"]] = None

    external_id: Optional[str] = None
    """Recipient phone number."""

    message_id: Optional[str] = None

    metadata: Optional[object] = None
    """Original metadata provided plus system generated fields."""

    protocol: Optional[str] = None
    """The protocol used to send the message (e.g., imessage, rcs, sms)."""

    status: Optional[
        Literal["pending", "queued", "sent", "delivered", "failed", "cancelled", "cancellation_requested"]
    ] = None
    """Current delivery status."""

    text_length: Optional[int] = None

    time_sent: Optional[int] = None
    """Unix timestamp (ms) when the message was queued/sent."""
