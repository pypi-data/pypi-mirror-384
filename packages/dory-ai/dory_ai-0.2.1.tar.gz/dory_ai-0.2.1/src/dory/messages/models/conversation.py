from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from ...common.exceptions import ConversationNotFoundError

if TYPE_CHECKING:
    from ..adapters.base import StorageAdapter
    from ..config import ConversationConfig

__all__ = ["Conversation"]


class Conversation(BaseModel):
    """Conversation model representing a chat session between a user and the system."""

    id: str = Field(..., description="Conversation identifier (e.g. CONV_<uuid>)")
    user_id: str = Field(..., description="User who owns the conversation")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional application-defined metadata"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    async def get_or_create(
        cls,
        *,
        user_id: str,
        adapter: StorageAdapter,
        config: ConversationConfig,
    ) -> Conversation:
        """Finds the most recent conversation for the user within the reuse window."""

        # Determine the earliest timestamp that still falls inside the
        # inactivity window. Any conversation whose `updated_at` is older than
        # this value is considered stale and will not be reused.
        reuse_since = datetime.now(UTC) - timedelta(days=config.reuse_window_days)

        if conversation := await adapter.find_recent_conversation(
            user_id=user_id, since=reuse_since
        ):
            return conversation

        return await adapter.create_conversation(user_id=user_id)

    @classmethod
    async def get_by_id(
        cls,
        *,
        conversation_id: str,
        adapter: StorageAdapter,
    ) -> Conversation:
        """Fetch a conversation by ID or raise if it does not exist."""

        if conversation := await adapter.get_conversation(conversation_id):
            return conversation

        raise ConversationNotFoundError(conversation_id)

    async def get_chat_history(
        self,
        *,
        adapter: StorageAdapter,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Get the chat history for this conversation."""

        return await adapter.get_chat_history(
            conversation_id=self.id,
            limit=limit,
        )
