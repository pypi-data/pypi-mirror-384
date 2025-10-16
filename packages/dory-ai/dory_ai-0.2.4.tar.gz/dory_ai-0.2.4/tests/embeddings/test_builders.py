"""Tests for embeddings builder functions."""

from unittest.mock import MagicMock, patch

import pytest

from src.dory.embeddings import build_embeddings
from src.dory.embeddings.config import EmbeddingsConfig
from src.dory.embeddings.service import Embeddings


@patch("src.dory.embeddings.builders.Memory")
def test_should_create_embeddings_with_mongodb_store(
    mock_memory_class: MagicMock,
) -> None:
    """Test creating embeddings with MongoDB store."""
    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    service = build_embeddings(
        api_key="test-key",
        store="mongodb",
        connection_string="mongodb://localhost:27017",
        collection="test_memories",
    )

    assert isinstance(service, Embeddings)
    assert mock_memory_class.from_config.called


@patch("src.dory.embeddings.builders.Memory")
def test_should_create_embeddings_with_chroma_store(
    mock_memory_class: MagicMock,
) -> None:
    """Test creating embeddings with Chroma store."""
    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    service = build_embeddings(
        api_key="test-key",
        store="chroma",
        store_path="/custom/path",
        collection="test_memories",
    )

    assert isinstance(service, Embeddings)
    assert mock_memory_class.from_config.called


@patch("src.dory.embeddings.builders.Memory")
def test_should_create_test_embeddings_with_memory_store(
    mock_memory_class: MagicMock,
) -> None:
    """Test creating embeddings with in-memory store for testing."""
    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    # Use build_embeddings with memory store (equivalent to old build_test_embeddings)
    service = build_embeddings(store="memory", collection="test_memories")

    assert isinstance(service, Embeddings)
    assert mock_memory_class.from_config.called


def test_should_validate_invalid_store_type() -> None:
    """Test that invalid store type raises error."""
    with pytest.raises(ValueError, match="Store must be one of"):
        build_embeddings(store="invalid")


def test_should_require_connection_string_for_mongodb() -> None:
    """Test that MongoDB requires connection string."""
    with pytest.raises(ValueError, match="MongoDB store requires connection_string"):
        build_embeddings(store="mongodb")


def test_embeddings_config_defaults() -> None:
    """Test EmbeddingsConfig default values."""
    config = EmbeddingsConfig()

    assert config.api_key is None
    assert config.store == "memory"
    assert config.store_path is None
    assert config.collection == "memories"


def test_embeddings_config_to_mem0() -> None:
    """Test conversion to mem0 configuration."""
    config = EmbeddingsConfig(
        api_key="test-key",
        store="chroma",
        store_path="/test/path",
        collection="test",
    )

    mem0_config = config.to_mem0_config()

    assert "vector_store" in mem0_config
    assert mem0_config["vector_store"]["provider"] == "chroma"
    assert mem0_config["vector_store"]["config"]["path"] == "/test/path"
    assert mem0_config["vector_store"]["config"]["collection_name"] == "test"
