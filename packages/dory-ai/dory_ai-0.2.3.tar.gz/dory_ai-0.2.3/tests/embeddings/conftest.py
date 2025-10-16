"""Fixtures for embeddings tests."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import mongomock
import pytest

from src.dory.embeddings.adapters.base import MemoryAdapter
from src.dory.embeddings.config import EmbeddingsConfig


@pytest.fixture
def mock_adapter() -> AsyncMock:
    """Provide mock adapter for embeddings service tests."""
    adapter = AsyncMock(spec=MemoryAdapter)

    # Default behaviors for common operations
    adapter.add_memory.return_value = "mem_123"
    adapter.search_memories.return_value = [
        {"content": "Memory 1", "score": 0.95},
        {"content": "Memory 2", "score": 0.85},
    ]
    adapter.add_embedding.return_value = "emb_123"
    adapter.search_embeddings.return_value = [{"content": "Result 1", "score": 0.92}]
    adapter.delete_memories.return_value = 1

    return adapter


@pytest.fixture
def sample_memory_data() -> dict[str, Any]:
    """Provide sample memory data for tests."""
    return {
        "content": "Test memory content",
        "user_id": "test_user",
        "conversation_id": "conv_123",
        "metadata": {"source": "test", "timestamp": datetime.now(UTC).isoformat()},
    }


@pytest.fixture
def sample_embedding_data() -> dict[str, Any]:
    """Provide sample embedding data for tests."""
    return {
        "content": "Text to embed",
        "user_id": "test_user",
        "message_id": "msg_456",
        "metadata": {"type": "document"},
    }


@pytest.fixture
def mock_mongodb_client():
    """Provide a mongomock client for tests."""
    return mongomock.MongoClient()


@pytest.fixture
def mock_mongodb_patch():
    """Patch pymongo.MongoClient with mongomock."""
    with patch("pymongo.MongoClient", mongomock.MongoClient):
        yield


@pytest.fixture
def mock_mem0():
    """Mock mem0.Memory to avoid real API calls."""
    with patch("src.dory.embeddings.adapters.mem0.Memory") as mock_memory_class:
        mock_instance = MagicMock()
        mock_memory_class.return_value = mock_instance

        # Configure default behaviors
        mock_instance.add.return_value = {
            "id": "test_mem_123",  # Changed from "memory_id" to "id"
            "memory": "Test memory content",
            "metadata": {"timestamp": datetime.now(UTC).isoformat()},
        }

        mock_instance.get.return_value = {
            "memory": "Retrieved memory content",
            "metadata": {"user_id": "test_user"},
        }

        mock_instance.search.return_value = [
            {"memory": "Found memory 1", "score": 0.95, "metadata": {"source": "test"}},
            {"memory": "Found memory 2", "score": 0.85, "metadata": {"source": "test"}},
        ]

        mock_instance.delete.return_value = {"success": True}
        mock_instance.get_all.return_value = [
            {"memory": "Memory 1", "metadata": {}},
            {"memory": "Memory 2", "metadata": {}},
        ]

        # Mock for embeddings
        mock_instance.get_embeddings = MagicMock(return_value=[0.1] * 1536)

        yield mock_instance


@pytest.fixture
def embeddings_config():
    """Basic configuration for embeddings tests."""
    return EmbeddingsConfig(
        store="memory",
        collection="test_memories",
    )


@pytest.fixture
def test_embeddings():
    """Build in-memory embeddings service for testing.

    This creates an embeddings service that stores everything in memory,
    perfect for unit tests and development.

    Returns:
        In-memory Embeddings service
    """
    from src.dory.embeddings import build_embeddings

    return build_embeddings(store="memory", collection="test_memories")


@pytest.fixture
def mock_vector_store():
    """Mock for mem0 vector store."""
    mock_store = MagicMock()

    # Configure behaviors
    mock_store.create_col.return_value = None
    mock_store.insert.return_value = "vec_123"
    mock_store.search.return_value = [
        {
            "id": "vec_1",
            "text": "Similar text",
            "score": 0.92,
            "metadata": {"type": "test"},
        }
    ]
    mock_store.delete.return_value = None

    return mock_store


@pytest.fixture
def complete_mock_setup(mock_mongodb_patch, mock_mem0):
    """Complete setup with all necessary mocks."""
    # Additional mock for OpenAI if used directly
    with patch("openai.Embedding.create") as mock_openai:
        mock_openai.return_value = MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])

        yield {
            "mem0": mock_mem0,
            "openai": mock_openai,
            "mongodb": mongomock.MongoClient(),
        }
