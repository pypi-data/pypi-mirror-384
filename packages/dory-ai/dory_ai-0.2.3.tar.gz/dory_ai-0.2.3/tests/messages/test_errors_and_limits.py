import asyncio
from typing import Any

import pytest

from dory import ChatRole, DoryError, MessageType
from dory.common.exceptions import ConversationNotFoundError
from dory.messages import Messages
from dory.messages.adapters import InMemoryAdapter


async def test_should_raise_not_found_when_conversation_missing() -> None:
    service = Messages(adapter=InMemoryAdapter())

    with pytest.raises(ConversationNotFoundError):
        await service.get_conversation(conversation_id="CONV_nonexistent")


async def test_should_return_last_n_messages_when_limit_is_provided() -> None:
    service = Messages(adapter=InMemoryAdapter())
    conversation = await service.get_or_create_conversation(user_id="limit-user")

    # Create 5 messages
    contents: list[str] = ["m1", "m2", "m3", "m4", "m5"]
    for idx, text in enumerate(contents):
        await service.add_message(
            conversation_id=conversation.id,
            user_id="limit-user",
            chat_role=ChatRole.USER if idx % 2 == 0 else ChatRole.AI,
            content=text,
            message_type=(
                MessageType.USER_MESSAGE
                if idx % 2 == 0
                else MessageType.REQUEST_RESPONSE
            ),
        )
        await asyncio.sleep(0)

    history = await service.get_chat_history(conversation_id=conversation.id, limit=3)
    assert len(history) == 3
    assert history == [
        {"user": "m3"},
        {"ai": "m4"},
        {"user": "m5"},
    ]


async def test_should_allow_structured_content_when_adding_and_reading_history() -> (
    None
):
    service = Messages(adapter=InMemoryAdapter())
    conversation = await service.get_or_create_conversation(user_id="content-user")

    payload: dict[str, Any] = {"tool": "search", "args": {"query": "hello"}}
    await service.add_message(
        conversation_id=conversation.id,
        user_id="content-user",
        chat_role=ChatRole.USER,
        content=payload,
        message_type=MessageType.USER_MESSAGE,
    )

    history = await service.get_chat_history(conversation_id=conversation.id, limit=10)
    assert history[-1] == {"user": payload}
