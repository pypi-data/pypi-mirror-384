"""Adapters for embeddings storage backends."""

from .base import MemoryAdapter
from .mem0 import Mem0Adapter
from .types import (
    EmbeddingMetadata,
    EmbeddingResult,
    MemoryMetadata,
    MemoryResult,
)

__all__ = [
    "MemoryAdapter",
    "Mem0Adapter",
    "MemoryResult",
    "EmbeddingResult",
    "MemoryMetadata",
    "EmbeddingMetadata",
]
