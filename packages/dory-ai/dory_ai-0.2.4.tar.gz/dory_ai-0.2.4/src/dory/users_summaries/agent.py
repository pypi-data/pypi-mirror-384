from __future__ import annotations

from dory.messages.models import Message
from dory.users_summaries.models import UserAction, UserSummary

from .prompt_modules.user_summary_generation import (
    UserSummaryGenerationInput,
    UserSummaryGenerationOutput,
    ainvoke_user_summary_generation,
    create_user_summary_agent,
)

__all__ = ["UserSummaryAgent"]


class UserSummaryAgent:
    def __init__(self, api_key: str | None = None):
        self._agent = create_user_summary_agent(api_key)

    async def generate_summary(
        self,
        messages: list[Message],
        existing_summary: UserSummary | None = None,
        recent_actions: list[UserAction] | None = None,
    ) -> UserSummaryGenerationOutput:
        conversation_messages = [
            f"{msg.chat_role.value}: {msg.content}" for msg in messages[-50:]
        ]

        user_actions = []
        if recent_actions:
            user_actions = [
                f"{action.action_name}: {action.metadata}" for action in recent_actions
            ]

        input_data = UserSummaryGenerationInput(
            existing_summary=existing_summary.content if existing_summary else None,
            conversation_messages=conversation_messages,
            user_actions=user_actions,
        )

        return await ainvoke_user_summary_generation(input_data, self._agent)
