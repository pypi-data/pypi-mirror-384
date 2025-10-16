from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from ...common.types import ChatRole, MessageType
from ..models import Conversation, Message


class StorageAdapter(Protocol):
    """Persistence abstraction for conversations and messages."""

    async def find_recent_conversation(
        self, *, user_id: str, since: datetime
    ) -> Conversation | None: ...

    async def create_conversation(self, *, user_id: str) -> Conversation: ...

    async def get_conversation(self, conversation_id: str) -> Conversation | None: ...

    async def update_conversation_timestamp(self, conversation_id: str) -> None: ...

    async def add_message(
        self,
        *,
        message_id: str | None = None,
        conversation_id: str | None = None,
        user_id: str,
        chat_role: ChatRole,
        content: Any,
        message_type: MessageType,
    ) -> Message: ...

    async def get_chat_history(
        self, *, conversation_id: str, limit: int
    ) -> list[dict[str, Any]]: ...
