from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from dory.common.types import ChatRole, MessageType
from dory.messages.models import Message
from dory.users_summaries import (
    InMemoryAdapter,
    UserAction,
    UserSummary,
    UserSummaryConfig,
    UserSummaryModel,
)
from dory.users_summaries.prompt_modules import UserSummaryGenerationOutput


async def test_should_get_or_create_summary_when_exists():
    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter)

    existing_summary = await adapter.create_summary(user_id="user_123")
    existing_summary.content = "Existing content"
    await adapter.update_summary(existing_summary)

    result = await service.get_or_create_summary(user_id="user_123")

    assert result.id == existing_summary.id
    assert result.content == "Existing content"


async def test_should_get_or_create_summary_when_not_exists():
    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter)

    result = await service.get_or_create_summary(user_id="new_user")

    assert result.user_id == "new_user"
    assert result.content == ""
    assert result.metadata == {}


async def test_should_track_action_successfully():
    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter)

    action = await service.track_action(
        user_id="user_123",
        action_type="vehicle_search",
        action_name="Searched for SUVs",
        metadata={"category": "SUV", "budget": 50000},
        conversation_id="CONV_001",
    )

    assert action.user_id == "user_123"
    assert action.action_type == "vehicle_search"
    assert action.action_name == "Searched for SUVs"
    assert action.metadata["category"] == "SUV"
    assert action.conversation_id == "CONV_001"

    stored_actions = await adapter.get_user_actions(user_id="user_123")
    assert len(stored_actions) == 1
    assert stored_actions[0].id == action.id


async def test_should_append_to_existing_summary():
    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter)

    await adapter.create_summary(user_id="user_123")
    await service.append_to_summary(
        user_id="user_123",
        new_information="User prefers electric vehicles",
    )

    summary = await adapter.get_summary(user_id="user_123")
    assert summary.content == "User prefers electric vehicles"

    await service.append_to_summary(
        user_id="user_123",
        new_information="Has a budget of $40,000",
    )

    updated_summary = await adapter.get_summary(user_id="user_123")
    expected_content = "User prefers electric vehicles\n\nHas a budget of $40,000"
    assert updated_summary.content == expected_content


async def test_should_respect_max_summary_length_when_appending():
    config = UserSummaryConfig(max_summary_length=50)
    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter, config=config)

    await adapter.create_summary(user_id="user_123")

    long_text = "A" * 100
    result = await service.append_to_summary(
        user_id="user_123",
        new_information=long_text,
    )

    assert len(result.content) == 50
    assert result.content == "A" * 50


async def test_should_get_context_for_prompt_with_full_data():
    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter)

    summary = UserSummaryModel(
        id="SUMM_001",
        user_id="user_123",
        content="User is looking for a family car",
        metadata={
            "name": "John Doe",
            "location": "California",
            "preferences": ["electric", "7-seater"],
        },
    )
    await adapter.update_summary(summary)

    await service.track_action(
        user_id="user_123",
        action_type="search",
        action_name="Searched for Tesla Model X",
        metadata={"price": 90000, "seats": 7},
    )

    context = await service.get_context_for_prompt(user_id="user_123")

    assert "User Summary: User is looking for a family car" in context
    assert "User Information:" in context
    assert "name: John Doe" in context
    assert "location: California" in context
    assert "preferences: electric, 7-seater" in context
    assert "Recent Actions:" in context
    assert "Searched for Tesla Model X" in context
    assert "price: 90000" in context


async def test_should_get_empty_context_when_no_summary():
    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter)

    context = await service.get_context_for_prompt(user_id="nonexistent")

    assert context == ""


async def test_should_respect_max_length_in_context():
    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter)

    summary = UserSummaryModel(
        id="SUMM_001",
        user_id="user_123",
        content="A very long summary " * 50,
        metadata={},
    )
    await adapter.update_summary(summary)

    context = await service.get_context_for_prompt(
        user_id="user_123",
        max_length=100,
    )

    assert len(context) == 100


async def test_should_exclude_actions_from_context_when_requested():
    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter)

    summary = UserSummaryModel(
        id="SUMM_001",
        user_id="user_123",
        content="User summary",
        metadata={"key": "value"},
    )
    await adapter.update_summary(summary)

    await service.track_action(
        user_id="user_123",
        action_type="test",
        action_name="Test Action",
    )

    context = await service.get_context_for_prompt(
        user_id="user_123",
        include_actions=False,
    )

    assert "User Summary: User summary" in context
    assert "User Information: key: value" in context
    assert "Recent Actions:" not in context
    assert "Test Action" not in context


async def test_should_update_summary_with_agent(sample_messages, monkeypatch):
    mock_output = UserSummaryGenerationOutput(
        content="Updated user summary from agent",
        metadata={"new_key": "new_value"},
        key_topics=["cars", "family"],
        confidence_score=0.9,
    )

    mock_agent = MagicMock()
    mock_agent.generate_summary = AsyncMock(return_value=mock_output)

    mock_messages_service = MagicMock()
    # Convert messages to history format that get_chat_history returns
    history_format = []
    for msg in sample_messages:
        role_key = "user" if msg.chat_role == ChatRole.USER else "assistant"
        history_format.append({role_key: msg.content})
    mock_messages_service.get_chat_history = AsyncMock(return_value=history_format)

    adapter = InMemoryAdapter()
    config = UserSummaryConfig(summary_generation_threshold_messages=3)
    service = UserSummary(adapter=adapter, agent=mock_agent, config=config)

    result = await service.update_summary(
        user_id="user_123",
        conversation_id="CONV_001",
        messages_service=mock_messages_service,
    )

    assert result.content == "Updated user summary from agent"
    assert result.metadata == {"new_key": "new_value"}
    assert "CONV_001" in result.conversation_ids

    mock_messages_service.get_chat_history.assert_called_once_with(
        conversation_id="CONV_001",
        limit=100,
    )
    mock_agent.generate_summary.assert_called_once()


async def test_should_raise_error_when_updating_without_agent():
    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter, agent=None)

    mock_messages_service = MagicMock()

    with pytest.raises(ValueError, match="Agent is required for summary generation"):
        await service.update_summary(
            user_id="user_123",
            conversation_id="CONV_001",
            messages_service=mock_messages_service,
        )


async def test_should_not_update_when_below_message_threshold(monkeypatch):
    config = UserSummaryConfig(summary_generation_threshold_messages=5)

    mock_agent = MagicMock()
    mock_agent.generate_summary = AsyncMock()

    mock_messages_service = MagicMock()
    mock_messages_service.get_chat_history = AsyncMock(
        return_value=[
            Message(
                id="MSG_001",
                conversation_id="CONV_001",
                user_id="user_123",
                chat_role=ChatRole.USER,
                content="Hello",
                message_type=MessageType.USER_MESSAGE,
            )
        ]
    )

    adapter = InMemoryAdapter()
    service = UserSummary(adapter=adapter, agent=mock_agent, config=config)

    result = await service.update_summary(
        user_id="user_123",
        conversation_id="CONV_001",
        messages_service=mock_messages_service,
    )

    assert result.content == ""
    mock_agent.generate_summary.assert_not_called()


async def test_should_regenerate_summary_when_requested(sample_messages, monkeypatch):
    mock_output = UserSummaryGenerationOutput(
        content="Completely new summary",
        metadata={"fresh": "data"},
        key_topics=["new_topics"],
        confidence_score=0.95,
    )

    mock_agent = MagicMock()
    mock_agent.generate_summary = AsyncMock(return_value=mock_output)

    mock_messages_service = MagicMock()
    # Convert messages to history format that get_chat_history returns
    history_format = []
    for msg in sample_messages:
        role_key = "user" if msg.chat_role == ChatRole.USER else "assistant"
        history_format.append({role_key: msg.content})
    mock_messages_service.get_chat_history = AsyncMock(return_value=history_format)

    adapter = InMemoryAdapter()
    existing = await adapter.create_summary(user_id="user_123")
    existing.content = "Old content"
    existing.metadata = {"old": "data"}
    await adapter.update_summary(existing)

    config = UserSummaryConfig(summary_generation_threshold_messages=3)
    service = UserSummary(adapter=adapter, agent=mock_agent, config=config)

    result = await service.update_summary(
        user_id="user_123",
        conversation_id="CONV_002",
        messages_service=mock_messages_service,
        regenerate=True,
    )

    assert result.content == "Completely new summary"
    assert result.metadata == {"fresh": "data"}

    call_args = mock_agent.generate_summary.call_args[1]
    assert call_args["existing_summary"] is None
