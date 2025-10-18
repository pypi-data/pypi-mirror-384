# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["MessageGetStatusResponse"]


class MessageGetStatusResponse(BaseModel):
    message_id: Optional[str] = None

    status: Optional[
        Literal["pending", "queued", "sent", "delivered", "failed", "cancelled", "cancellation_requested"]
    ] = None
