# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["MessageCancelResponse"]


class MessageCancelResponse(BaseModel):
    cancelled: Optional[bool] = None
    """True if cancellation was successful, false otherwise."""

    current_status: Optional[str] = None
    """The current status if cancellation failed (deprecated, use 'status' instead)."""

    message: Optional[str] = None
    """Human-readable message about the cancellation result."""

    message_id: Optional[str] = None

    status: Optional[str] = None
    """The current status of the message."""
