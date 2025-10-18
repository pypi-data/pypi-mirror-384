# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["MessageSendParams"]


class MessageSendParams(TypedDict, total=False):
    to: Required[str]
    """Recipient phone number in E.164 format (e.g., +15551234567)"""

    attachments: SequenceNotStr[str]
    """Array of publicly accessible URLs to media attachments."""

    metadata: object
    """Arbitrary key/value pairs to associate with the message."""

    text: str
    """Text body of the message."""

    idempotency_key: Annotated[str, PropertyInfo(alias="Idempotency-Key")]
