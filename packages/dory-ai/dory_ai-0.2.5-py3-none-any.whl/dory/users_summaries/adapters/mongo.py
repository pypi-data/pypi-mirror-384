from datetime import UTC, datetime
from typing import Any

from mongoengine import (
    DateTimeField,
    DictField,
    DynamicField,
    ListField,
    StringField,
    connect,
)
from mongoengine_plus.aio import AsyncDocument
from mongoengine_plus.models import BaseModel
from mongoengine_plus.models.event_handlers import updated_at

from ...messages.adapters.utils import generate_prefixed_id
from ..config import UserSummaryConfig
from ..models import UserAction, UserSummary

__all__ = ["MongoDBAdapter"]


@updated_at.apply
class UserSummaryDocument(BaseModel, AsyncDocument):
    meta = {
        "collection": "user_summaries",
        "indexes": [
            "updated_at",
            {"fields": ["user_id"], "unique": True},
        ],
        "auto_create_index": True,
    }

    id: str = StringField(primary_key=True)
    user_id: str = StringField(required=True, unique=True)
    content: str = StringField(required=True)
    metadata: dict[str, Any] = DictField()
    conversation_ids: list[str] = ListField(StringField())
    action_ids: list[str] = ListField(StringField())
    created_at: datetime = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at: datetime = DateTimeField(default=lambda: datetime.now(UTC))


class UserActionDocument(BaseModel, AsyncDocument):
    meta = {
        "collection": "user_actions",
        "indexes": [
            "user_id",
            "action_type",
            "created_at",
            {"fields": ["user_id", "created_at"]},
            {"fields": ["user_id", "action_type"]},
        ],
        "auto_create_index": True,
    }

    id: str = StringField(primary_key=True)
    user_id: str = StringField(required=True)
    action_type: str = StringField(required=True)
    action_name: str = StringField(required=True)
    metadata: Any = DynamicField()
    conversation_id: str | None = StringField(null=True)
    created_at: datetime = DateTimeField(default=lambda: datetime.now(UTC))


class MongoDBAdapter:
    def __init__(
        self,
        config: UserSummaryConfig | None = None,
        *,
        use_existing_connection: bool = False,
        connection_string: str | None = None,
        database: str | None = None,
        alias: str = "default",
        **connect_kwargs: Any,
    ) -> None:
        self._config = config or UserSummaryConfig()

        if not use_existing_connection and connection_string:
            from mongoengine.connection import ConnectionFailure, get_connection

            try:
                get_connection(alias)
            except ConnectionFailure:
                connect(
                    host=connection_string,
                    db=database,
                    alias=alias,
                    uuidRepresentation="standard",
                    **connect_kwargs,
                )
        self._alias = alias

        # Configure documents to use the specified alias
        UserSummaryDocument._meta["db_alias"] = alias
        UserActionDocument._meta["db_alias"] = alias

    async def get_summary(self, user_id: str) -> UserSummary | None:
        doc = await UserSummaryDocument.objects(user_id=user_id).async_first()
        if not doc:
            return None

        return UserSummary(
            id=doc.id,
            user_id=doc.user_id,
            content=doc.content,
            metadata=doc.metadata,
            conversation_ids=doc.conversation_ids,
            action_ids=doc.action_ids,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    async def create_summary(self, user_id: str) -> UserSummary:
        doc = UserSummaryDocument(
            id=generate_prefixed_id("SUMM_"),
            user_id=user_id,
            content="",
            metadata={},
            conversation_ids=[],
            action_ids=[],
        )
        await doc.async_save()

        return UserSummary.model_validate(doc, from_attributes=True)

    async def update_summary(self, summary: UserSummary) -> UserSummary:
        doc = await UserSummaryDocument.objects(id=summary.id).async_first()

        doc.content = summary.content
        doc.metadata = summary.metadata
        doc.conversation_ids = summary.conversation_ids
        doc.action_ids = summary.action_ids
        doc.updated_at = datetime.now(UTC)

        await doc.async_save()

        return UserSummary.model_validate(doc, from_attributes=True)

    async def add_action(self, action: UserAction) -> UserAction:
        doc = UserActionDocument(
            id=action.id,
            user_id=action.user_id,
            action_type=action.action_type,
            action_name=action.action_name,
            metadata=action.metadata,
            conversation_id=action.conversation_id,
            created_at=action.created_at,
        )
        await doc.async_save()

        return UserAction.model_validate(doc, from_attributes=True)

    async def get_user_actions(
        self,
        user_id: str,
        action_type: str | None = None,
        limit: int = 100,
    ) -> list[UserAction]:
        query = {"user_id": user_id}
        if action_type:
            query["action_type"] = action_type

        docs = (
            await UserActionDocument.objects(**query)
            .order_by("-created_at")
            .limit(limit)
            .async_to_list()
        )

        return [UserAction.model_validate(doc, from_attributes=True) for doc in docs]
