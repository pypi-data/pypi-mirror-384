from unittest.mock import AsyncMock, MagicMock

import pytest

from dory.common.types import ChatRole, MessageType
from dory.messages.models import Message
from dory.users_summaries import UserAction


@pytest.fixture
def mock_agent():
    mock = MagicMock()
    mock.run = AsyncMock()
    return mock


@pytest.fixture
def sample_messages():
    return [
        Message(
            id="MSG_001",
            conversation_id="CONV_001",
            user_id="user_123",
            chat_role=ChatRole.USER,
            content="Hi, I'm looking for a car for my family",
            message_type=MessageType.USER_MESSAGE,
        ),
        Message(
            id="MSG_002",
            conversation_id="CONV_001",
            user_id="user_123",
            chat_role=ChatRole.AI,
            content="Hello! I'd be happy to help you find a family car. What size are you looking for?",
            message_type=MessageType.REQUEST_RESPONSE,
        ),
        Message(
            id="MSG_003",
            conversation_id="CONV_001",
            user_id="user_123",
            chat_role=ChatRole.USER,
            content="We need something with 7 seats, we have 3 kids",
            message_type=MessageType.USER_MESSAGE,
        ),
    ]


@pytest.fixture
def sample_actions():
    return [
        UserAction(
            id="ACT_001",
            user_id="user_123",
            action_type="vehicle_search",
            action_name="Searched for 7-seater vehicles",
            metadata={"seats": 7, "type": "SUV"},
        ),
        UserAction(
            id="ACT_002",
            user_id="user_123",
            action_type="comparison",
            action_name="Compared vehicles",
            metadata={"vehicles": ["Honda Pilot", "Toyota Highlander"]},
        ),
    ]
