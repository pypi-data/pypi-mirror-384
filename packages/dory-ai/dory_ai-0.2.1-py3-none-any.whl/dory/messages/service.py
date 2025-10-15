from __future__ import annotations

from typing import Any

from ..common.types import ChatRole, MessageType
from .adapters.base import StorageAdapter
from .config import ConversationConfig
from .models import Conversation, Message

__all__ = ["Messages"]


class Messages:
    """High-level API used by applications."""

    def __init__(
        self, adapter: StorageAdapter, config: ConversationConfig | None = None
    ) -> None:
        self._adapter = adapter
        self._config = config or ConversationConfig()

    async def get_or_create_conversation(self, *, user_id: str) -> Conversation:
        """Get a recent conversation or create a new one."""
        return await Conversation.get_or_create(
            user_id=user_id,
            adapter=self._adapter,
            config=self._config,
        )

    async def get_conversation(self, *, conversation_id: str) -> Conversation:
        """Fetch a conversation or raise if it does not exist."""
        return await Conversation.get_by_id(
            conversation_id=conversation_id,
            adapter=self._adapter,
        )

    async def add_message(
        self,
        *,
        conversation_id: str | None = None,
        message_id: str | None = None,
        user_id: str,
        chat_role: ChatRole,
        content: Any,
        message_type: MessageType,
    ) -> Message:
        """Add a new message to a conversation."""
        return await Message.create(
            adapter=self._adapter,
            conversation_id=conversation_id,
            message_id=message_id,
            user_id=user_id,
            chat_role=chat_role,
            content=content,
            message_type=message_type,
        )

    async def get_chat_history(
        self, *, conversation_id: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Get the chat history for a conversation."""
        conversation = await self.get_conversation(conversation_id=conversation_id)
        effective_limit = limit if (limit is not None) else self._config.history_limit
        return await conversation.get_chat_history(
            adapter=self._adapter,
            limit=effective_limit,
        )
