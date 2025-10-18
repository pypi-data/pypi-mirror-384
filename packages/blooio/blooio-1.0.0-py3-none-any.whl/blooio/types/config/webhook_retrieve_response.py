# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["WebhookRetrieveResponse"]


class WebhookRetrieveResponse(BaseModel):
    updated_at: Optional[int] = None
    """Unix timestamp (ms) when the webhook URL was last updated."""

    webhook_url: Optional[str] = None
    """The current webhook URL or null if not set."""
