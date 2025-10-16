from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from ...common.types import ChatRole, MessageType

if TYPE_CHECKING:
    from ..adapters.base import StorageAdapter

__all__ = ["Message"]


class Message(BaseModel):
    """Message model representing a single chat message within a conversation."""

    id: str = Field(..., description="Message identifier (e.g. MSG_<uuid>)")
    conversation_id: str = Field(...)
    user_id: str = Field(...)
    chat_role: ChatRole
    content: Any
    message_type: MessageType
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional application-defined metadata"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    async def create(
        cls,
        *,
        adapter: StorageAdapter,
        conversation_id: str | None = None,
        message_id: str | None = None,
        user_id: str,
        chat_role: ChatRole,
        content: Any,
        message_type: MessageType,
    ) -> Message:
        """Create a new message using the storage adapter."""

        return await adapter.add_message(
            conversation_id=conversation_id,
            message_id=message_id,
            user_id=user_id,
            chat_role=chat_role,
            content=content,
            message_type=message_type,
        )
