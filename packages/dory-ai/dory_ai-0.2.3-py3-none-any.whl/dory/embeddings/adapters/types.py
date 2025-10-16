"""Type definitions for embeddings adapters."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

__all__ = [
    "MemoryResult",
    "EmbeddingResult",
    "MemoryMetadata",
    "EmbeddingMetadata",
    "Mem0Message",
    "MessageInput",
]


class Mem0Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


MessageInput = str | list[Mem0Message] | list[dict[str, str]]


class MemoryMetadata(BaseModel):
    """Metadata for a stored memory."""

    user_id: str
    conversation_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    custom: dict[str, Any] = Field(default_factory=dict)


class EmbeddingMetadata(BaseModel):
    """Metadata for a raw embedding."""

    user_id: str
    conversation_id: str | None = None
    message_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content_type: str = "message"  # message, document, etc.
    custom: dict[str, Any] = Field(default_factory=dict)


class MemoryResult(BaseModel):
    """Result from memory search."""

    id: str = Field(..., description="Memory ID")
    content: str = Field(..., description="Memory content")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    metadata: MemoryMetadata
    context: str | None = Field(None, description="Additional context from mem0")


class EmbeddingResult(BaseModel):
    """Result from embedding search."""

    id: str = Field(..., description="Embedding ID")
    content: str = Field(..., description="Original content")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    metadata: EmbeddingMetadata
    vector: list[float] | None = Field(None, description="Raw embedding vector")
