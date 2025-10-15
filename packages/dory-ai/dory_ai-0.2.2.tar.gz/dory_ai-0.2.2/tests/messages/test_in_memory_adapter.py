from dory import ChatRole, MessageType
from dory.messages.adapters import InMemoryAdapter


async def test_should_reuse_conversation_when_within_reuse_window() -> None:
    adapter = InMemoryAdapter()
    conv1 = await adapter.create_conversation(user_id="user_1")

    recent = await adapter.find_recent_conversation(
        user_id="user_1", since=conv1.updated_at
    )
    assert recent == conv1


async def test_should_store_and_return_messages_when_added_to_conversation() -> None:
    adapter = InMemoryAdapter()
    conv = await adapter.create_conversation(user_id="u")

    await adapter.add_message(
        conversation_id=conv.id,
        user_id="u",
        chat_role=ChatRole.USER,
        content="hi",
        message_type=MessageType.USER_MESSAGE,
    )
    await adapter.add_message(
        conversation_id=conv.id,
        user_id="u",
        chat_role=ChatRole.AI,
        content="hello",
        message_type=MessageType.REQUEST_RESPONSE,
    )

    history = await adapter.get_chat_history(conversation_id=conv.id, limit=5)
    assert history == [{"user": "hi"}, {"ai": "hello"}]
