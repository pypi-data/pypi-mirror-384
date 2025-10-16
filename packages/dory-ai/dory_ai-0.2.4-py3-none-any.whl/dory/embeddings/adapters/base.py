"""Base protocol for memory and embeddings adapters."""

from __future__ import annotations

from typing import Any, Protocol

from .types import MessageInput

__all__ = ["MemoryAdapter"]


class MemoryAdapter(Protocol):
    """Protocol for memory and embeddings storage."""

    async def add_memory(
        self,
        *,
        messages: MessageInput,
        user_id: str,
        conversation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add a memory to the store and return its ID."""
        ...

    async def search_memories(
        self,
        *,
        query: str,
        user_id: str,
        conversation_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for relevant memories matching the query."""
        ...

    async def delete_memories(
        self,
        *,
        user_id: str,
        conversation_id: str | None = None,
        memory_ids: list[str] | None = None,
    ) -> int:
        """Delete memories based on filters and return count."""
        ...

    async def add_embedding(
        self,
        *,
        content: str,
        user_id: str,
        conversation_id: str | None = None,
        message_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store raw content as embedding for vector search."""
        ...

    async def search_embeddings(
        self,
        *,
        query: str,
        user_id: str,
        conversation_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for similar embeddings using vector similarity."""
        ...
