from unittest.mock import MagicMock

from dory.common.types import ChatRole, MessageType
from dory.messages.models import Message
from dory.users_summaries import UserSummaryAgent, UserSummaryModel
from dory.users_summaries.prompt_modules import UserSummaryGenerationOutput


async def test_should_generate_summary_from_messages_without_existing_summary(
    sample_messages, monkeypatch
):
    mock_output = UserSummaryGenerationOutput(
        content="User is looking for a 7-seater family vehicle.",
        metadata={"family_size": 5, "children": 3, "vehicle_preference": "7-seater"},
        key_topics=["family car", "7 seats", "SUV"],
        confidence_score=0.85,
    )

    async def mock_ainvoke(*args, **kwargs):
        return mock_output

    mock_agent = MagicMock()

    monkeypatch.setattr(
        "dory.users_summaries.agent.create_user_summary_agent",
        lambda *args, **kwargs: mock_agent,
    )
    mock_agent = MagicMock()

    monkeypatch.setattr(
        "dory.users_summaries.agent.create_user_summary_agent",
        lambda *args, **kwargs: mock_agent,
    )
    monkeypatch.setattr(
        "dory.users_summaries.agent.ainvoke_user_summary_generation", mock_ainvoke
    )

    agent = UserSummaryAgent()
    result = await agent.generate_summary(messages=sample_messages)

    assert result.content == "User is looking for a 7-seater family vehicle."
    assert result.metadata["family_size"] == 5
    assert "family car" in result.key_topics
    assert result.confidence_score == 0.85


async def test_should_include_existing_summary_when_provided(
    sample_messages, sample_actions, monkeypatch
):
    existing_summary = UserSummaryModel(
        id="SUMM_001",
        user_id="user_123",
        content="User previously showed interest in sedans.",
        metadata={"previous_interest": "sedan"},
    )

    captured_input = None

    async def mock_ainvoke(input_data, agent):
        nonlocal captured_input
        captured_input = input_data
        return UserSummaryGenerationOutput(
            content="Updated summary",
            metadata={},
            key_topics=[],
            confidence_score=0.9,
        )

    mock_agent = MagicMock()

    monkeypatch.setattr(
        "dory.users_summaries.agent.create_user_summary_agent",
        lambda *args, **kwargs: mock_agent,
    )
    monkeypatch.setattr(
        "dory.users_summaries.agent.ainvoke_user_summary_generation", mock_ainvoke
    )

    agent = UserSummaryAgent()
    await agent.generate_summary(
        messages=sample_messages,
        existing_summary=existing_summary,
        recent_actions=sample_actions,
    )

    assert (
        captured_input.existing_summary == "User previously showed interest in sedans."
    )
    assert len(captured_input.user_actions) == 2
    assert "Searched for 7-seater vehicles" in captured_input.user_actions[0]


async def test_should_format_messages_correctly(sample_messages, monkeypatch):
    captured_input = None

    async def mock_ainvoke(input_data, agent):
        nonlocal captured_input
        captured_input = input_data
        return UserSummaryGenerationOutput(
            content="Summary", metadata={}, key_topics=[], confidence_score=0.8
        )

    mock_agent = MagicMock()

    monkeypatch.setattr(
        "dory.users_summaries.agent.create_user_summary_agent",
        lambda *args, **kwargs: mock_agent,
    )
    monkeypatch.setattr(
        "dory.users_summaries.agent.ainvoke_user_summary_generation", mock_ainvoke
    )

    agent = UserSummaryAgent()
    await agent.generate_summary(messages=sample_messages)

    assert len(captured_input.conversation_messages) == 3
    assert (
        captured_input.conversation_messages[0]
        == "user: Hi, I'm looking for a car for my family"
    )
    assert "ai: Hello! I'd be happy to help" in captured_input.conversation_messages[1]
    assert (
        captured_input.conversation_messages[2]
        == "user: We need something with 7 seats, we have 3 kids"
    )


async def test_should_limit_messages_to_last_50(monkeypatch):
    many_messages = [
        Message(
            id=f"MSG_{i:03d}",
            conversation_id="CONV_001",
            user_id="user_123",
            chat_role=ChatRole.USER if i % 2 == 0 else ChatRole.AI,
            content=f"Message {i}",
            message_type=MessageType.USER_MESSAGE
            if i % 2 == 0
            else MessageType.REQUEST_RESPONSE,
        )
        for i in range(100)
    ]

    captured_input = None

    async def mock_ainvoke(input_data, agent):
        nonlocal captured_input
        captured_input = input_data
        return UserSummaryGenerationOutput(
            content="Summary", metadata={}, key_topics=[], confidence_score=0.8
        )

    mock_agent = MagicMock()

    monkeypatch.setattr(
        "dory.users_summaries.agent.create_user_summary_agent",
        lambda *args, **kwargs: mock_agent,
    )
    monkeypatch.setattr(
        "dory.users_summaries.agent.ainvoke_user_summary_generation", mock_ainvoke
    )

    agent = UserSummaryAgent()
    await agent.generate_summary(messages=many_messages)

    assert len(captured_input.conversation_messages) == 50
    assert "Message 50" in captured_input.conversation_messages[0]
    assert "Message 99" in captured_input.conversation_messages[-1]
