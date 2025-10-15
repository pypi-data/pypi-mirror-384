"""Embeddings service for memory and vector search management."""

from .adapters.types import Mem0Message, MessageInput
from .builders import build_embeddings
from .config import EmbeddingsConfig
from .service import Embeddings

__all__ = [
    "Embeddings",
    "EmbeddingsConfig",
    "build_embeddings",
    "Mem0Message",
    "MessageInput",
]
