from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ...common.types import ChatRole, MessageType
from ..config import ConversationConfig
from ..models import Conversation, Message
from .base import StorageAdapter
from .utils import generate_prefixed_id, history_item

__all__ = ["InMemoryAdapter"]


class InMemoryAdapter(StorageAdapter):
    """In-memory implementation for tests and demos."""

    def __init__(self, config: ConversationConfig | None = None) -> None:
        self._config = config or ConversationConfig()
        self._conversations: dict[str, Conversation] = {}
        self._messages: dict[str, Message] = {}

    async def find_recent_conversation(
        self, *, user_id: str, since: datetime
    ) -> Conversation | None:
        candidates = [
            conv
            for conv in self._conversations.values()
            if conv.user_id == user_id and conv.updated_at >= since
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda c: c.updated_at)

    async def create_conversation(self, *, user_id: str) -> Conversation:
        conv_id = generate_prefixed_id(self._config.conversation_id_prefix)
        conv = Conversation(id=conv_id, user_id=user_id)
        self._conversations[conv_id] = conv
        return conv

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self._conversations.get(conversation_id)

    async def update_conversation_timestamp(self, conversation_id: str) -> None:
        conv = self._conversations.get(conversation_id)
        if conv:
            conv.updated_at = datetime.now(UTC)
            self._conversations[conversation_id] = conv

    async def add_message(
        self,
        *,
        message_id: str | None = None,
        conversation_id: str | None = None,
        user_id: str,
        chat_role: ChatRole,
        content: Any,
        message_type: MessageType,
    ) -> Message:
        # Ensure conversation ID exists or create a new conversation for this user
        if conversation_id is None:
            conversation_id = generate_prefixed_id(self._config.conversation_id_prefix)
            self._conversations[conversation_id] = Conversation(
                id=conversation_id, user_id=user_id
            )

        msg_id = message_id or generate_prefixed_id(self._config.message_id_prefix)
        msg = Message(
            id=msg_id,
            conversation_id=conversation_id,
            user_id=user_id,
            chat_role=chat_role,
            content=content,
            message_type=message_type,
        )
        self._messages[msg_id] = msg
        await self.update_conversation_timestamp(conversation_id)
        return msg

    async def get_chat_history(
        self, *, conversation_id: str, limit: int
    ) -> list[dict[str, Any]]:
        filtered = [
            m for m in self._messages.values() if m.conversation_id == conversation_id
        ]
        filtered.sort(key=lambda m: (m.created_at, m.id))
        sliced = filtered[-limit:]
        return [history_item(m.chat_role, m.content) for m in sliced]
