from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ..common.types import ChatRole, MessageType
from ..messages.adapters.utils import generate_prefixed_id
from ..messages.models import Message
from .adapters.base import UserSummaryAdapter
from .agent import UserSummaryAgent
from .config import UserSummaryConfig
from .models import UserAction
from .models import UserSummary as UserSummaryModel

if TYPE_CHECKING:
    from ..messages import Messages

__all__ = ["UserSummary"]


class UserSummary:
    def __init__(
        self,
        adapter: UserSummaryAdapter,
        agent: UserSummaryAgent | None = None,
        config: UserSummaryConfig | None = None,
    ):
        self._adapter = adapter
        self._agent = agent
        self._config = config or UserSummaryConfig()

    async def get_or_create_summary(self, *, user_id: str) -> UserSummaryModel:
        existing_summary = await self._adapter.get_summary(user_id)
        if existing_summary:
            return existing_summary
        return await self._adapter.create_summary(user_id)

    async def update_summary(
        self,
        *,
        user_id: str,
        conversation_id: str,
        messages_service: Messages,
        regenerate: bool = False,
    ) -> UserSummaryModel:
        if not self._agent:
            raise ValueError("Agent is required for summary generation")

        summary = await self._adapter.get_summary(user_id)

        message_dicts = await messages_service.get_chat_history(
            conversation_id=conversation_id,
            limit=self._config.max_conversation_messages,
        )

        if len(message_dicts) < self._config.summary_generation_threshold_messages:
            if not summary:
                return await self._adapter.create_summary(user_id)
            return summary

        # Convert history format to full messages for the agent
        messages: list[Message] = []
        for msg_dict in message_dicts:
            # History format is {'user': content} or {'assistant': content}
            for role_str, content in msg_dict.items():
                chat_role = ChatRole.USER if role_str == "user" else ChatRole.AI
                message_type = (
                    MessageType.USER_MESSAGE
                    if role_str == "user"
                    else MessageType.REQUEST_RESPONSE
                )
                messages.append(
                    Message(
                        id=f"temp_{len(messages)}",
                        conversation_id=conversation_id,
                        user_id=user_id,
                        chat_role=chat_role,
                        content=content,
                        message_type=message_type,
                    )
                )

        actions = await self._adapter.get_user_actions(
            user_id=user_id,
            limit=self._config.max_recent_actions,
        )

        result = await self._agent.generate_summary(
            messages=messages,
            existing_summary=summary if not regenerate else None,
            recent_actions=actions,
        )

        if summary:
            summary.content = result.content[: self._config.max_summary_length]
            summary.metadata = result.metadata
            if conversation_id not in summary.conversation_ids:
                summary.conversation_ids.append(conversation_id)
            action_ids_to_add = [
                a.id for a in actions if a.id not in summary.action_ids
            ]
            summary.action_ids.extend(action_ids_to_add)
            summary.updated_at = datetime.now(UTC)
            return await self._adapter.update_summary(summary)
        else:
            new_summary = await self._adapter.create_summary(user_id)
            new_summary.content = result.content[: self._config.max_summary_length]
            new_summary.metadata = result.metadata
            new_summary.conversation_ids = [conversation_id]
            new_summary.action_ids = [a.id for a in actions]
            return await self._adapter.update_summary(new_summary)

    async def append_to_summary(
        self,
        *,
        user_id: str,
        new_information: str,
    ) -> UserSummaryModel:
        summary = await self.get_or_create_summary(user_id=user_id)

        if summary.content:
            summary.content = f"{summary.content}\n\n{new_information}"
        else:
            summary.content = new_information

        summary.content = summary.content[: self._config.max_summary_length]
        summary.updated_at = datetime.now(UTC)

        return await self._adapter.update_summary(summary)

    async def track_action(
        self,
        *,
        user_id: str,
        action_type: str,
        action_name: str,
        metadata: dict[str, Any] | None = None,
        conversation_id: str | None = None,
    ) -> UserAction:
        action = UserAction(
            id=generate_prefixed_id("ACT_"),
            user_id=user_id,
            action_type=action_type,
            action_name=action_name,
            metadata=metadata or {},
            conversation_id=conversation_id,
        )
        return await self._adapter.add_action(action)

    async def get_context_for_prompt(
        self,
        *,
        user_id: str,
        include_actions: bool = True,
        max_length: int | None = None,
    ) -> str:
        summary = await self._adapter.get_summary(user_id)
        if not summary:
            return ""

        context_parts = [f"User Summary: {summary.content}"]

        if summary.metadata:
            metadata_str = self._format_metadata_for_context(summary.metadata)
            if metadata_str:
                context_parts.append(f"User Information: {metadata_str}")

        if include_actions and self._config.include_actions_in_context:
            recent_actions = await self._adapter.get_user_actions(
                user_id=user_id,
                limit=5,
            )
            if recent_actions:
                actions_str = self._format_actions_for_context(recent_actions)
                context_parts.append(f"Recent Actions: {actions_str}")

        full_context = "\n\n".join(context_parts)

        if max_length:
            return full_context[:max_length]
        return full_context

    def _format_metadata_for_context(self, metadata: dict[str, Any]) -> str:
        formatted_items = []
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                formatted_items.append(f"{key}: {value}")
            elif isinstance(value, list) and value:
                formatted_items.append(f"{key}: {', '.join(str(v) for v in value)}")
        return "; ".join(formatted_items)

    def _format_actions_for_context(self, actions: list[UserAction]) -> str:
        action_strings = []
        for action in actions:
            action_str = f"{action.action_name}"
            if action.metadata:
                metadata_preview = self._get_metadata_preview(action.metadata)
                if metadata_preview:
                    action_str += f" ({metadata_preview})"
            action_strings.append(action_str)
        return "; ".join(action_strings)

    def _get_metadata_preview(
        self, metadata: dict[str, Any], max_items: int = 2
    ) -> str:
        preview_items = []
        for i, (key, value) in enumerate(metadata.items()):
            if i >= max_items:
                break
            preview_items.append(f"{key}: {value}")
        return ", ".join(preview_items)
