"""Embeddings service for memory and vector search management."""

from __future__ import annotations

from typing import Any

from .adapters.base import MemoryAdapter
from .adapters.types import MessageInput

__all__ = ["Embeddings"]


class Embeddings:
    """Embeddings service for memory and vector search management."""

    def __init__(self, adapter: MemoryAdapter) -> None:
        """Initialize the embeddings service with a memory adapter."""
        self._adapter = adapter

    async def remember(
        self,
        messages: MessageInput,
        *,
        user_id: str,
        conversation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Process and store content as a memory."""
        return await self._adapter.add_memory(
            messages=messages,
            user_id=user_id,
            conversation_id=conversation_id,
            metadata=metadata,
        )

    async def store_embedding(
        self,
        content: str,
        *,
        user_id: str,
        conversation_id: str | None = None,
        message_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store raw content as embedding for vector search."""
        return await self._adapter.add_embedding(
            content=content,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            metadata=metadata,
        )

    async def recall(
        self,
        query: str,
        *,
        user_id: str,
        conversation_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant memories for a query."""
        return await self._adapter.search_memories(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            limit=limit,
        )

    async def search_embeddings(
        self,
        query: str,
        *,
        user_id: str,
        conversation_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for similar content using vector similarity."""
        return await self._adapter.search_embeddings(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            limit=limit,
        )

    async def forget(
        self,
        *,
        user_id: str,
        conversation_id: str | None = None,
        memory_ids: list[str] | None = None,
    ) -> int:
        """Delete memories based on filters."""
        return await self._adapter.delete_memories(
            user_id=user_id,
            conversation_id=conversation_id,
            memory_ids=memory_ids,
        )
