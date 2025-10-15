"""Tests for message formats in embeddings service."""

from unittest.mock import MagicMock, patch

import pytest

from src.dory.embeddings import Mem0Message
from src.dory.embeddings.adapters.mem0 import Mem0Adapter
from src.dory.embeddings.config import EmbeddingsConfig
from src.dory.embeddings.service import Embeddings


@patch("src.dory.embeddings.adapters.mem0.Memory")
async def test_should_accept_string_messages_when_adding_memory(
    mock_memory_class: MagicMock,
    embeddings_config: EmbeddingsConfig,
) -> None:
    """Verify that string messages are accepted and normalized."""
    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    mock_memory.add.return_value = {
        "results": [{"id": "mem_str", "memory": "String memory", "event": "ADD"}]
    }

    adapter = Mem0Adapter(config=embeddings_config, memory=mock_memory)
    service = Embeddings(adapter=adapter)

    memory_id = await service.remember(
        messages="User likes Python decorators",
        user_id="test_user",
    )

    assert memory_id == "mem_str"
    mock_memory.add.assert_called_once_with(
        messages="User likes Python decorators",
        user_id="test_user",
        metadata={},
    )


@patch("src.dory.embeddings.adapters.mem0.Memory")
async def test_should_accept_list_of_dicts_when_adding_memory(
    mock_memory_class: MagicMock,
    embeddings_config: EmbeddingsConfig,
) -> None:
    """Verify that list of dict messages are accepted and normalized."""
    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    mock_memory.add.return_value = {
        "results": [{"id": "mem_list", "memory": "List memory", "event": "ADD"}]
    }

    adapter = Mem0Adapter(config=embeddings_config, memory=mock_memory)
    service = Embeddings(adapter=adapter)

    messages = [
        {"role": "user", "content": "Can you teach me about decorators?"},
        {"role": "assistant", "content": "Decorators are a powerful feature..."},
        {"role": "user", "content": "Can you show me an example?"},
    ]

    memory_id = await service.remember(
        messages=messages,
        user_id="test_user",
    )

    assert memory_id == "mem_list"
    mock_memory.add.assert_called_once_with(
        messages=messages,
        user_id="test_user",
        metadata={},
    )


@patch("src.dory.embeddings.adapters.mem0.Memory")
async def test_should_accept_list_of_mem0_messages_when_adding_memory(
    mock_memory_class: MagicMock,
    embeddings_config: EmbeddingsConfig,
) -> None:
    """Verify that list of Mem0Message objects are accepted and normalized."""
    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    mock_memory.add.return_value = {
        "results": [{"id": "mem_obj", "memory": "Object memory", "event": "ADD"}]
    }

    adapter = Mem0Adapter(config=embeddings_config, memory=mock_memory)
    service = Embeddings(adapter=adapter)

    messages = [
        Mem0Message(role="user", content="What are Python decorators?"),
        Mem0Message(role="assistant", content="Decorators modify functions..."),
        Mem0Message(role="user", content="Show me a simple example"),
    ]

    memory_id = await service.remember(
        messages=messages,
        user_id="test_user",
    )

    assert memory_id == "mem_obj"

    call_args = mock_memory.add.call_args
    assert call_args.kwargs["user_id"] == "test_user"
    assert call_args.kwargs["metadata"] == {}

    messages_arg = call_args.kwargs["messages"]
    assert isinstance(messages_arg, list)
    assert len(messages_arg) == 3
    assert messages_arg[0] == {"role": "user", "content": "What are Python decorators?"}
    assert messages_arg[1] == {
        "role": "assistant",
        "content": "Decorators modify functions...",
    }
    assert messages_arg[2] == {"role": "user", "content": "Show me a simple example"}


@patch("src.dory.embeddings.adapters.mem0.Memory")
async def test_should_raise_error_when_empty_messages_list(
    mock_memory_class: MagicMock,
    embeddings_config: EmbeddingsConfig,
) -> None:
    """Verify that empty messages list raises error."""
    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    adapter = Mem0Adapter(config=embeddings_config, memory=mock_memory)
    service = Embeddings(adapter=adapter)

    with pytest.raises(ValueError, match="Messages list cannot be empty"):
        await service.remember(
            messages=[],
            user_id="test_user",
        )


@patch("src.dory.embeddings.adapters.mem0.Memory")
async def test_should_raise_error_when_invalid_message_type(
    mock_memory_class: MagicMock,
    embeddings_config: EmbeddingsConfig,
) -> None:
    """Verify that invalid message type raises error."""
    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    adapter = Mem0Adapter(config=embeddings_config, memory=mock_memory)
    service = Embeddings(adapter=adapter)

    with pytest.raises(ValueError, match="Invalid messages format"):
        await service.remember(
            messages=123,
            user_id="test_user",
        )


@patch("src.dory.embeddings.adapters.mem0.Memory")
async def test_should_preserve_conversation_context_with_message_list(
    mock_memory_class: MagicMock,
    embeddings_config: EmbeddingsConfig,
) -> None:
    """Verify that conversation context is preserved when using message lists."""
    mock_memory = MagicMock()
    mock_memory_class.from_config.return_value = mock_memory

    mock_memory.add.return_value = {
        "results": [{"id": "mem_ctx", "memory": "Context memory", "event": "ADD"}]
    }

    adapter = Mem0Adapter(config=embeddings_config, memory=mock_memory)
    service = Embeddings(adapter=adapter)

    messages = [
        {"role": "user", "content": "I love red cars"},
        {
            "role": "assistant",
            "content": "Great! Red is a popular color for sports cars.",
        },
    ]

    conversation_id = "conv_123"
    metadata = {"source": "chat", "timestamp": "2024-01-01"}

    memory_id = await service.remember(
        messages=messages,
        user_id="test_user",
        conversation_id=conversation_id,
        metadata=metadata,
    )

    assert memory_id == "mem_ctx"

    call_args = mock_memory.add.call_args
    assert call_args.kwargs["messages"] == messages
    assert call_args.kwargs["user_id"] == "test_user"

    metadata_arg = call_args.kwargs["metadata"]
    assert metadata_arg["conversation_id"] == conversation_id
    assert metadata_arg["source"] == "chat"
    assert metadata_arg["timestamp"] == "2024-01-01"
