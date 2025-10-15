"""Tests for the Embeddings service following project conventions."""

from unittest.mock import AsyncMock

import pytest

from src.dory.embeddings.service import Embeddings


async def test_should_store_memory_and_return_id_when_remember_is_called(
    mock_adapter: AsyncMock,
) -> None:
    """Verify that remember method delegates to adapter and returns memory ID."""
    # Arrange
    service = Embeddings(adapter=mock_adapter)
    messages = "Important information"
    user_id = "user_123"
    metadata = {"source": "chat"}
    expected_id = "mem_123"

    # Act
    result = await service.remember(messages=messages, user_id=user_id, metadata=metadata)

    # Assert
    assert result == expected_id, f"Expected memory ID '{expected_id}', got '{result}'"
    mock_adapter.add_memory.assert_called_once_with(
        messages=messages,
        user_id=user_id,
        conversation_id=None,
        metadata=metadata,
    )


async def test_should_store_embedding_and_return_id_when_store_embedding_is_called(
    mock_adapter: AsyncMock,
) -> None:
    """Verify that store_embedding delegates to adapter correctly."""
    # Arrange
    service = Embeddings(adapter=mock_adapter)
    content = "Text to embed"
    user_id = "user_123"
    message_id = "msg_456"
    metadata = {"type": "document"}
    expected_id = "emb_123"

    # Act
    result = await service.store_embedding(
        content=content,
        user_id=user_id,
        message_id=message_id,
        metadata=metadata,
    )

    # Assert
    assert result == expected_id, (
        f"Expected embedding ID '{expected_id}', got '{result}'"
    )
    mock_adapter.add_embedding.assert_called_once_with(
        content=content,
        user_id=user_id,
        conversation_id=None,
        message_id=message_id,
        metadata=metadata,
    )


async def test_should_return_memories_when_recall_is_called(
    mock_adapter: AsyncMock,
) -> None:
    """Verify that recall searches and returns relevant memories."""
    # Arrange
    service = Embeddings(adapter=mock_adapter)
    query = "search query"
    user_id = "user_123"
    limit = 5
    expected_memories = [
        {"content": "Memory 1", "score": 0.95},
        {"content": "Memory 2", "score": 0.85},
    ]
    mock_adapter.search_memories.return_value = expected_memories

    # Act
    results = await service.recall(query=query, user_id=user_id, limit=limit)

    # Assert
    assert results == expected_memories, "Returned memories don't match expected"
    assert len(results) == 2, f"Expected 2 memories, got {len(results)}"
    assert results[0]["content"] == "Memory 1", "First memory content mismatch"
    mock_adapter.search_memories.assert_called_once_with(
        query=query, user_id=user_id, conversation_id=None, limit=limit
    )


async def test_should_return_embeddings_when_search_embeddings_is_called(
    mock_adapter: AsyncMock,
) -> None:
    """Verify that search_embeddings returns similar content via vector search."""
    # Arrange
    service = Embeddings(adapter=mock_adapter)
    query = "search term"
    user_id = "user_123"
    limit = 3
    expected_results = [{"content": "Result 1", "score": 0.92}]
    mock_adapter.search_embeddings.return_value = expected_results

    # Act
    results = await service.search_embeddings(query=query, user_id=user_id, limit=limit)

    # Assert
    assert results == expected_results, "Search results don't match expected"
    assert results[0]["score"] == 0.92, (
        f"Expected score 0.92, got {results[0]['score']}"
    )
    mock_adapter.search_embeddings.assert_called_once_with(
        query=query, user_id=user_id, conversation_id=None, limit=limit
    )


async def test_should_delete_memories_and_return_count_when_forget_is_called(
    mock_adapter: AsyncMock,
) -> None:
    """Verify that forget deletes specified memories and returns count."""
    # Arrange
    service = Embeddings(adapter=mock_adapter)
    user_id = "user_123"
    memory_ids = ["mem_to_delete"]
    expected_count = 1

    # Act
    result = await service.forget(user_id=user_id, memory_ids=memory_ids)

    # Assert
    assert result == expected_count, f"Expected {expected_count} deleted, got {result}"
    mock_adapter.delete_memories.assert_called_once_with(
        user_id=user_id, conversation_id=None, memory_ids=memory_ids
    )


async def test_should_return_zero_when_forget_fails_to_delete(
    mock_adapter: AsyncMock,
) -> None:
    """Verify that forget returns 0 when no memories are deleted."""
    # Arrange
    service = Embeddings(adapter=mock_adapter)
    mock_adapter.delete_memories.return_value = 0
    user_id = "bad_id"

    # Act
    result = await service.forget(user_id=user_id)

    # Assert
    assert result == 0, f"Expected 0 deleted, got {result}"


@pytest.mark.parametrize(
    "conversation_id,expected_call_id",
    [
        ("conv_abc", "conv_abc"),
        (None, None),
    ],
)
async def test_should_include_conversation_id_when_provided_in_remember(
    mock_adapter: AsyncMock,
    conversation_id: str | None,
    expected_call_id: str | None,
) -> None:
    """Verify that conversation_id is passed through when provided."""
    # Arrange
    service = Embeddings(adapter=mock_adapter)
    messages = "Conversation message"
    user_id = "user_123"
    metadata = {"turn": 1}

    # Act
    await service.remember(
        messages=messages,
        user_id=user_id,
        conversation_id=conversation_id,
        metadata=metadata,
    )

    # Assert
    mock_adapter.add_memory.assert_called_once_with(
        messages=messages,
        user_id=user_id,
        conversation_id=expected_call_id,
        metadata=metadata,
    )


async def test_should_filter_by_conversation_when_recall_with_conversation_id(
    mock_adapter: AsyncMock,
) -> None:
    """Verify that recall filters results by conversation_id when provided."""
    # Arrange
    service = Embeddings(adapter=mock_adapter)
    query = "query"
    user_id = "user_123"
    conversation_id = "conv_456"

    # Act
    await service.recall(query=query, user_id=user_id, conversation_id=conversation_id)

    # Assert
    mock_adapter.search_memories.assert_called_once_with(
        query=query, user_id=user_id, conversation_id=conversation_id, limit=10
    )


async def test_should_handle_multiple_operations_in_sequence_when_batch_processing(
    mock_adapter: AsyncMock,
) -> None:
    """Verify that service handles multiple operations correctly in sequence."""
    # Arrange
    service = Embeddings(adapter=mock_adapter)
    user_id = "batch_user"
    memories_to_add = ["Memory 0", "Memory 1", "Memory 2"]

    # Act - Add multiple memories
    for i, messages in enumerate(memories_to_add):
        await service.remember(messages=messages, user_id=user_id)

    # Act - Search memories
    await service.recall(query="Memory", user_id=user_id)

    # Act - Search embeddings
    await service.search_embeddings(query="Memory", user_id=user_id)

    # Act - Delete memories
    await service.forget(user_id=user_id, memory_ids=["mem_1"])

    # Assert
    assert mock_adapter.add_memory.call_count == 3, "Should have added 3 memories"
    assert mock_adapter.search_memories.called, "Should have searched memories"
    assert mock_adapter.search_embeddings.called, "Should have searched embeddings"
    assert mock_adapter.delete_memories.called, "Should have deleted memories"
