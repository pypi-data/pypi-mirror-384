from dory import ChatRole, MessageType
from dory.messages import Messages
from dory.messages.adapters import InMemoryAdapter


async def test_should_create_conversation_and_return_history_when_messages_added() -> (
    None
):
    service = Messages(adapter=InMemoryAdapter())

    conversation = await service.get_or_create_conversation(user_id="u12345678910")

    await service.add_message(
        conversation_id=conversation.id,
        user_id="u12345678910",
        chat_role=ChatRole.USER,
        content="hello",
        message_type=MessageType.USER_MESSAGE,
    )
    await service.add_message(
        conversation_id=conversation.id,
        user_id="u12345678910",
        chat_role=ChatRole.AI,
        content="hi!",
        message_type=MessageType.REQUEST_RESPONSE,
    )

    history = await service.get_chat_history(conversation_id=conversation.id)
    assert history[-1] == {"ai": "hi!"}
    assert len(history) == 2
