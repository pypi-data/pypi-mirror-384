"""Integration tests for embeddings service following project conventions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dory.embeddings.adapters.mem0 import Mem0Adapter
from src.dory.embeddings.builders import build_embeddings
from src.dory.embeddings.config import EmbeddingsConfig
from src.dory.embeddings.service import Embeddings


async def test_should_complete_full_memory_flow_when_using_embeddings_service() -> None:
    """Verify end-to-end flow of adding and retrieving memories."""

    mock_adapter = AsyncMock()
    mock_adapter.add_memory.return_value = "mem_123"
    mock_adapter.search_memories.return_value = [
        {"content": "Test memory", "score": 0.95}
    ]
    service = Embeddings(adapter=mock_adapter)

    memory_id = await service.remember(
        messages="Important information",
        user_id="test_user",
    )

    results = await service.recall(
        query="Important",
        user_id="test_user",
    )

    assert memory_id == "mem_123", f"Expected 'mem_123', got '{memory_id}'"
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert results[0]["content"] == "Test memory"
    assert results[0]["score"] == 0.95

    mock_adapter.add_memory.assert_called_once()
    mock_adapter.search_memories.assert_called_once()


async def test_should_handle_vector_operations_when_storing_embeddings() -> None:
    """Verify that raw embeddings can be stored and searched."""

    mock_adapter = AsyncMock()
    mock_adapter.add_embedding.return_value = "emb_456"
    mock_adapter.search_embeddings.return_value = [
        {"content": "Similar content", "score": 0.89}
    ]
    service = Embeddings(adapter=mock_adapter)

    embedding_id = await service.store_embedding(
        content="Document content",
        user_id="test_user",
        message_id="msg_789",
    )

    results = await service.search_embeddings(
        query="Document",
        user_id="test_user",
    )

    assert embedding_id == "emb_456", f"Expected 'emb_456', got '{embedding_id}'"
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert results[0]["content"] == "Similar content"
    assert results[0]["score"] == 0.89

    mock_adapter.add_embedding.assert_called_once()
    mock_adapter.search_embeddings.assert_called_once()


@patch("src.dory.embeddings.adapters.mem0.Memory")
async def test_should_process_memories_when_using_mem0_adapter(
    mock_memory_class: MagicMock,
    embeddings_config: EmbeddingsConfig,
) -> None:
    """Verify that Mem0Adapter correctly integrates with mem0 library."""

    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    mock_memory.add.return_value = {
        "results": [{"id": "mem_from_mem0", "memory": "Test memory", "event": "ADD"}]
    }
    mock_memory.search.return_value = {
        "results": [{"memory": "Found by mem0", "score": 0.91, "id": "search_id"}]
    }

    adapter = Mem0Adapter(config=embeddings_config, memory=mock_memory)
    service = Embeddings(adapter=adapter)

    memory_id = await service.remember(
        messages="Test with mem0",
        user_id="test_user",
    )

    results = await service.recall(
        query="mem0",
        user_id="test_user",
    )

    assert memory_id == "mem_from_mem0", f"Expected 'mem_from_mem0', got '{memory_id}'"
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert results[0]["content"] == "Found by mem0"
    assert results[0]["score"] == 0.91

    # Verify mem0 calls
    mock_memory.add.assert_called_once_with(
        messages="Test with mem0",
        user_id="test_user",
        metadata={},
    )
    mock_memory.search.assert_called_once_with(
        query="mem0",
        user_id="test_user",
        limit=10,
    )


@patch("src.dory.embeddings.adapters.mem0.Memory")
async def test_should_separate_memories_and_embeddings_when_both_stored(
    mock_memory_class: MagicMock,
    embeddings_config: EmbeddingsConfig,
) -> None:
    """Verify that memories and raw embeddings are stored and searched separately."""

    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    def add_side_effect(**kwargs):
        if kwargs.get("infer") is False:
            return {
                "results": [{"id": "emb_id", "memory": "Embedding", "event": "ADD"}]
            }
        else:
            return {"results": [{"id": "mem_id", "memory": "Memory", "event": "ADD"}]}

    mock_memory.add.side_effect = add_side_effect

    mock_memory.search.return_value = {
        "results": [
            {
                "memory": "Memory result",
                "score": 0.95,
                "metadata": {"type": "memory"},
                "id": "mem_search",
            },
            {
                "memory": "Embedding result",
                "score": 0.92,
                "metadata": {"type": "raw_embedding"},
                "id": "emb_search",
            },
        ]
    }

    adapter = Mem0Adapter(config=embeddings_config, memory=mock_memory)
    service = Embeddings(adapter=adapter)

    memory_id = await service.remember(
        messages="This is a memory",
        user_id="test_user",
    )
    embedding_id = await service.store_embedding(
        content="This is an embedding",
        user_id="test_user",
    )

    memory_results = await service.recall(
        query="test",
        user_id="test_user",
    )

    embedding_results = await service.search_embeddings(
        query="test",
        user_id="test_user",
    )

    assert memory_id == "mem_id", f"Memory should get 'mem_id', got '{memory_id}'"
    assert embedding_id == "emb_id", (
        f"Embedding should get 'emb_id', got '{embedding_id}'"
    )

    assert len(memory_results) == 1, "Should return only memory results"
    assert memory_results[0]["content"] == "Memory result"

    assert len(embedding_results) == 1, "Should return only embedding results"
    assert embedding_results[0]["content"] == "Embedding result"


async def test_should_handle_conversation_context_when_provided() -> None:
    """Verify that conversation context is properly passed through the service."""

    mock_adapter = AsyncMock()
    mock_adapter.add_memory.return_value = "conv_mem_123"
    mock_adapter.search_memories.return_value = [
        {"content": "Conversation memory", "score": 0.93}
    ]
    service = Embeddings(adapter=mock_adapter)

    conversation_id = "conv_456"
    user_id = "test_user"

    memory_id = await service.remember(
        messages="Message in conversation",
        user_id=user_id,
        conversation_id=conversation_id,
    )

    results = await service.recall(
        query="conversation",
        user_id=user_id,
        conversation_id=conversation_id,
    )

    assert memory_id == "conv_mem_123"
    assert len(results) == 1
    assert results[0]["content"] == "Conversation memory"

    mock_adapter.add_memory.assert_called_once_with(
        messages="Message in conversation",
        user_id=user_id,
        conversation_id=conversation_id,
        metadata=None,
    )
    mock_adapter.search_memories.assert_called_once_with(
        query="conversation",
        user_id=user_id,
        conversation_id=conversation_id,
        limit=10,
    )


async def test_should_delete_memories_when_forget_called() -> None:
    """Verify that memories can be deleted through the service."""

    mock_adapter = AsyncMock()
    mock_adapter.delete_memories.return_value = 3
    service = Embeddings(adapter=mock_adapter)

    user_id = "test_user"
    memory_ids = ["mem_1", "mem_2", "mem_3"]

    deleted_count = await service.forget(
        user_id=user_id,
        memory_ids=memory_ids,
    )

    assert deleted_count == 3, f"Expected 3 deleted, got {deleted_count}"
    mock_adapter.delete_memories.assert_called_once_with(
        user_id=user_id,
        conversation_id=None,
        memory_ids=memory_ids,
    )


@patch("src.dory.embeddings.builders.Memory")
async def test_should_create_working_service_when_using_builder(
    mock_memory_class: MagicMock,
) -> None:
    """Verify that builder functions create fully functional services."""

    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    mock_memory.add.return_value = {
        "results": [
            {"id": "built_mem_123", "memory": "Built service test", "event": "ADD"}
        ]
    }

    service = build_embeddings(
        api_key="test-key",
        store="mongodb",
        connection_string="mongodb://localhost:27017/test",
        collection="test_collection",
    )

    memory_id = await service.remember(
        messages="Built service test",
        user_id="test_user",
    )

    assert memory_id == "built_mem_123", f"Expected 'built_mem_123', got '{memory_id}'"
    mock_memory.add.assert_called_once()


async def test_should_handle_metadata_correctly_when_provided() -> None:
    """Verify that metadata is properly passed through all operations."""

    mock_adapter = AsyncMock()
    mock_adapter.add_memory.return_value = "meta_mem_123"
    mock_adapter.add_embedding.return_value = "meta_emb_456"
    service = Embeddings(adapter=mock_adapter)

    memory_metadata = {"source": "chat", "importance": "high"}
    embedding_metadata = {"type": "document", "format": "pdf"}

    memory_id = await service.remember(
        messages="Memory with metadata",
        user_id="test_user",
        metadata=memory_metadata,
    )

    embedding_id = await service.store_embedding(
        content="Embedding with metadata",
        user_id="test_user",
        metadata=embedding_metadata,
    )

    assert memory_id == "meta_mem_123"
    assert embedding_id == "meta_emb_456"

    mock_adapter.add_memory.assert_called_once_with(
        messages="Memory with metadata",
        user_id="test_user",
        conversation_id=None,
        metadata=memory_metadata,
    )

    mock_adapter.add_embedding.assert_called_once_with(
        content="Embedding with metadata",
        user_id="test_user",
        conversation_id=None,
        message_id=None,
        metadata=embedding_metadata,
    )


@pytest.mark.parametrize(
    "limit,expected_limit",
    [
        (5, 5),
        (20, 20),
        (None, 10),
    ],
)
async def test_should_respect_limit_parameter_when_searching(
    limit: int | None,
    expected_limit: int,
) -> None:
    """Verify that search operations respect the limit parameter."""

    mock_adapter = AsyncMock()
    mock_adapter.search_memories.return_value = []
    mock_adapter.search_embeddings.return_value = []
    service = Embeddings(adapter=mock_adapter)

    if limit is not None:
        await service.recall(query="test", user_id="user", limit=limit)
        await service.search_embeddings(query="test", user_id="user", limit=limit)
    else:
        await service.recall(query="test", user_id="user")
        await service.search_embeddings(query="test", user_id="user")

    mock_adapter.search_memories.assert_called_once_with(
        query="test",
        user_id="user",
        conversation_id=None,
        limit=expected_limit,
    )

    mock_adapter.search_embeddings.assert_called_once_with(
        query="test",
        user_id="user",
        conversation_id=None,
        limit=expected_limit if limit is not None else 10,
    )
