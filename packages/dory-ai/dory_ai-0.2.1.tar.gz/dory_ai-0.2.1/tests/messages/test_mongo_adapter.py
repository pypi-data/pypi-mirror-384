import asyncio

from dory import ChatRole, MessageType
from dory.messages import Messages
from dory.messages.adapters import MongoDBAdapter


async def test_should_update_timestamp_and_reuse_when_message_added(
    mongo_adapter: MongoDBAdapter,
) -> None:
    service = Messages(adapter=mongo_adapter)

    conv = await service.get_or_create_conversation(user_id="mongo-user")
    assert conv.user_id == "mongo-user"

    first_updated_at = conv.updated_at
    await asyncio.sleep(0)

    await service.add_message(
        conversation_id=conv.id,
        user_id="mongo-user",
        chat_role=ChatRole.USER,
        content="hello",
        message_type=MessageType.USER_MESSAGE,
    )

    fresh_conv = await mongo_adapter.get_conversation(conv.id)
    assert fresh_conv is not None
    assert fresh_conv.updated_at >= first_updated_at

    # Reuse conversation within 14-day window
    reused = await service.get_or_create_conversation(user_id="mongo-user")
    assert reused.id == conv.id


async def test_should_return_messages_in_chronological_order_when_history_requested(
    mongo_adapter: MongoDBAdapter,
) -> None:
    service = Messages(adapter=mongo_adapter)
    conv = await service.get_or_create_conversation(user_id="hist-user")

    await service.add_message(
        conversation_id=conv.id,
        user_id="hist-user",
        chat_role=ChatRole.USER,
        content="msg1",
        message_type=MessageType.USER_MESSAGE,
    )

    # Small delay to ensure different timestamps
    await asyncio.sleep(0.001)

    await service.add_message(
        conversation_id=conv.id,
        user_id="hist-user",
        chat_role=ChatRole.AI,
        content="msg2",
        message_type=MessageType.REQUEST_RESPONSE,
    )

    history = await service.get_chat_history(conversation_id=conv.id, limit=10)
    assert history == [{"user": "msg1"}, {"ai": "msg2"}]
