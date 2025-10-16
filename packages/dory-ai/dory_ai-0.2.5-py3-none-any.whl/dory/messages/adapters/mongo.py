from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable

from mongoengine import (
    DateTimeField,
    DynamicField,
    EnumField,
    StringField,
    connect,
)
from mongoengine_plus.aio import AsyncDocument
from mongoengine_plus.models import BaseModel
from mongoengine_plus.models.event_handlers import updated_at

from ...common.types import ChatRole, MessageType
from ..config import ConversationConfig
from ..models import Conversation, Message
from .base import StorageAdapter
from .utils import generate_prefixed_id, history_item

__all__ = ["MongoDBAdapter"]


@updated_at.apply
class ConversationDocument(BaseModel, AsyncDocument):
    meta = {
        "collection": "conversations",
        "indexes": [
            "user_id",
            "updated_at",
            {"fields": ["user_id", "updated_at"]},
        ],
        "auto_create_index": True,
    }

    id: str = StringField(primary_key=True)
    user_id: str = StringField(required=True)
    metadata: Any = DynamicField()
    created_at: datetime = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at: datetime = DateTimeField(default=lambda: datetime.now(UTC))


class MessageDocument(BaseModel, AsyncDocument):
    meta = {
        "collection": "messages",
        "indexes": [
            "conversation_id",
            "created_at",
            {"fields": ["conversation_id", "created_at"]},
        ],
        "auto_create_index": True,
    }

    id: str = StringField(primary_key=True)
    conversation_id: str = StringField(required=True)
    user_id: str = StringField(required=True)
    chat_role: ChatRole = EnumField(ChatRole, required=True)
    content: Any = DynamicField(required=True)
    message_type: MessageType = EnumField(MessageType, required=True)
    metadata: Any = DynamicField()
    created_at: datetime = DateTimeField(default=lambda: datetime.now(UTC))


class MongoDBAdapter(StorageAdapter):
    """MongoDB implementation using mongoengine-plus async API."""

    def __init__(
        self,
        config: ConversationConfig | None = None,
        *,
        use_existing_connection: bool = False,
        connection_string: str | None = None,
        database: str | None = None,
        alias: str = "default",
        **connect_kwargs: Any,
    ) -> None:
        self._config = config or ConversationConfig()

        if not use_existing_connection and connection_string:
            from mongoengine.connection import ConnectionFailure, get_connection

            try:
                get_connection(alias)
            except ConnectionFailure:
                connect(
                    host=connection_string,
                    db=database,
                    alias=alias,
                    connectTimeoutMS=self._config.connection_timeout_seconds * 1000,
                    uuidRepresentation="standard",
                    **connect_kwargs,
                )
        self._alias = alias

        # Configure documents to use the specified alias
        ConversationDocument._meta["db_alias"] = alias
        MessageDocument._meta["db_alias"] = alias

    @staticmethod
    def _to_conversation(doc: ConversationDocument) -> Conversation:
        return Conversation.model_validate(doc, from_attributes=True)

    async def find_recent_conversation(
        self, *, user_id: str, since: datetime
    ) -> Conversation | None:
        doc = (
            await ConversationDocument.objects(user_id=user_id, updated_at__gte=since)
            .order_by("-updated_at")
            .limit(1)
            .async_first()
        )
        return self._to_conversation(doc) if doc else None

    async def create_conversation(self, *, user_id: str) -> Conversation:
        conv_id = generate_prefixed_id(self._config.conversation_id_prefix)
        doc = ConversationDocument(id=conv_id, user_id=user_id)
        await doc.async_save()
        await doc.async_reload()
        return self._to_conversation(doc)

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        doc = await ConversationDocument.objects(id=conversation_id).async_first()
        return self._to_conversation(doc) if doc else None

    async def update_conversation_timestamp(self, conversation_id: str) -> None:
        await ConversationDocument.objects(id=conversation_id).async_update(
            set__updated_at=datetime.now(UTC)
        )

    @staticmethod
    def _to_history_dict(msg: MessageDocument) -> dict[str, Any]:
        return history_item(msg.chat_role, msg.content)

    async def add_message(
        self,
        *,
        message_id: str | None = None,
        conversation_id: str | None = None,
        user_id: str,
        chat_role: ChatRole,
        content: Any,
        message_type: MessageType,
    ) -> Message:
        # Ensure conversation exists or create a new one for this user when not provided
        if conversation_id is None:
            conversation = await self.create_conversation(user_id=user_id)
            conversation_id = conversation.id

        msg_id = message_id or generate_prefixed_id(self._config.message_id_prefix)
        msg_doc = MessageDocument(
            id=msg_id,
            conversation_id=conversation_id,
            user_id=user_id,
            chat_role=chat_role,
            content=content,
            message_type=message_type,
        )
        await msg_doc.async_save()
        await self.update_conversation_timestamp(conversation_id)
        return Message.model_validate(msg_doc, from_attributes=True)

    async def get_chat_history(
        self, *, conversation_id: str, limit: int
    ) -> list[dict[str, Any]]:
        query: Iterable[MessageDocument] = (
            await MessageDocument.objects(conversation_id=conversation_id)
            .order_by("-created_at", "id")
            .limit(limit)
            .async_to_list()
        )
        return [self._to_history_dict(msg) for msg in reversed(list(query))]
