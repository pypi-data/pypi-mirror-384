"""Mem0 adapter implementation for memory and embeddings storage."""

from __future__ import annotations

from typing import Any, cast

from mem0 import Memory

from ..config import EmbeddingsConfig
from .base import MemoryAdapter
from .types import Mem0Message, MessageInput

__all__ = ["Mem0Adapter"]


class Mem0Adapter(MemoryAdapter):
    """Adapter that wraps mem0 for both memories and embeddings."""

    def __init__(self, config: EmbeddingsConfig, memory: Memory) -> None:
        """Initialize the Mem0 adapter with dependencies."""

        self._config = config
        self._memory = memory
        self._embeddings_cache: dict[str, str] = {}

    def _extract_results_list(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract the results list from Mem0's response dictionary."""

        if not isinstance(response, dict):
            return []
        from typing import cast

        return cast(list[dict[str, Any]], response.get("results", []))

    def _result_to_dict(self, item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a Mem0 result dict."""

        return {
            "id": item.get("id", ""),
            "memory": item.get("memory", ""),
            "score": item.get("score", 0.0),
            "metadata": item.get("metadata") or {},
            "created_at": item.get("created_at"),
        }

    def _extract_id_from_result(self, result: dict[str, Any]) -> str:
        """Extract ID from Mem0's add() response."""

        results = result.get("results", [])
        if results and isinstance(results, list) and results[0].get("id"):
            return str(results[0]["id"])

        raise ValueError(f"Mem0 did not return a valid ID. Response: {result}")

    def _messages_to_mem0_format(
        self, messages: MessageInput
    ) -> str | list[dict[str, str]]:
        if isinstance(messages, str):
            return messages

        if isinstance(messages, list):
            if not messages:
                raise ValueError("Messages list cannot be empty")

            first_item = messages[0]
            if isinstance(first_item, dict):
                return cast(list[dict[str, str]], messages)

            converted_messages: list[dict[str, str]] = []
            for msg in messages:
                if isinstance(msg, Mem0Message):
                    converted_messages.append(
                        {"role": msg.role, "content": msg.content}
                    )
            return converted_messages

        raise ValueError(f"Invalid messages format: {type(messages)}")

    async def add_memory(
        self,
        *,
        messages: MessageInput,
        user_id: str,
        conversation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add a memory to the store and return its ID."""

        mem0_metadata = metadata or {}
        if conversation_id:
            mem0_metadata["conversation_id"] = conversation_id

        formatted_messages = self._messages_to_mem0_format(messages)

        result = self._memory.add(
            messages=formatted_messages,
            user_id=user_id,
            metadata=mem0_metadata,
        )

        return self._extract_id_from_result(result)

    async def search_memories(
        self,
        *,
        query: str,
        user_id: str,
        conversation_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for relevant memories matching the query."""

        raw_results = self._memory.search(
            query=query,
            user_id=user_id,
            limit=limit,
        )

        results_list = self._extract_results_list(raw_results)
        memories = [self._result_to_dict(r) for r in results_list]

        filtered_results = self._apply_memory_filters(
            memories,
            conversation_id=conversation_id,
        )

        return self._format_memory_results(filtered_results)

    def _apply_memory_filters(
        self,
        results: list[dict[str, Any]],
        conversation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Apply filters to memory search results."""

        filtered = [
            result
            for result in results
            if result and result.get("metadata", {}).get("type") != "raw_embedding"
        ]

        if conversation_id:
            filtered = [
                result
                for result in filtered
                if result.get("metadata", {}).get("conversation_id") == conversation_id
            ]

        return filtered

    def _format_memory_results(
        self, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Format memory results for output."""

        return [
            {
                "id": result.get("id", ""),
                "content": result.get("memory", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {}),
            }
            for result in results
        ]

    async def delete_memories(
        self,
        *,
        user_id: str,
        conversation_id: str | None = None,
        memory_ids: list[str] | None = None,
    ) -> int:
        """Delete memories based on filters and return count."""

        deleted_count = 0

        if memory_ids:
            for memory_id in memory_ids:
                self._memory.delete(memory_id=memory_id)
                deleted_count += 1
        else:
            all_memories = self._memory.get_all(user_id=user_id)

            for memory in all_memories:
                if conversation_id:
                    if (
                        memory.get("metadata", {}).get("conversation_id")
                        != conversation_id
                    ):
                        continue

                self._memory.delete(memory_id=memory["id"])
                deleted_count += 1

        return deleted_count

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

        embedding_metadata = metadata or {}
        embedding_metadata["type"] = "raw_embedding"
        embedding_metadata["user_id"] = user_id

        if conversation_id:
            embedding_metadata["conversation_id"] = conversation_id
        if message_id:
            embedding_metadata["message_id"] = message_id

        result = self._memory.add(
            messages=content,
            user_id=user_id,
            metadata=embedding_metadata,
            infer=False,  # This tells mem0 to store raw content
        )

        embedding_id = self._extract_id_from_result(result)
        self._embeddings_cache[embedding_id] = content

        return embedding_id

    async def search_embeddings(
        self,
        *,
        query: str,
        user_id: str,
        conversation_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for similar embeddings using vector similarity."""

        raw_results = self._memory.search(
            query=query,
            user_id=user_id,
            limit=limit,
        )

        results_list = self._extract_results_list(raw_results)
        embeddings = [self._result_to_dict(r) for r in results_list]

        return self._filter_and_format_embeddings(
            embeddings,
            conversation_id=conversation_id,
            limit=limit,
        )

    def _filter_and_format_embeddings(
        self,
        results: list[dict[str, Any]],
        conversation_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Filter and format embedding search results."""

        embeddings = []

        for result in results:
            metadata = result.get("metadata", {})

            if metadata.get("type") != "raw_embedding":
                continue

            if conversation_id and metadata.get("conversation_id") != conversation_id:
                continue

            embeddings.append(
                {
                    "id": result.get("id", ""),
                    "content": result.get("memory", ""),
                    "score": result.get("score", 0.0),
                    "metadata": metadata,
                }
            )

            if len(embeddings) >= limit:
                break

        return embeddings
