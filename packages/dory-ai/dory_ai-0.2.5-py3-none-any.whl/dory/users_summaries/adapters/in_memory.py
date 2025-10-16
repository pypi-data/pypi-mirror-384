from ...messages.adapters.utils import generate_prefixed_id
from ..models import UserAction, UserSummary


class InMemoryAdapter:
    def __init__(self) -> None:
        self._summaries: dict[str, UserSummary] = {}
        self._actions: list[UserAction] = []

    async def get_summary(self, user_id: str) -> UserSummary | None:
        for summary in self._summaries.values():
            if summary.user_id == user_id:
                return summary
        return None

    async def create_summary(self, user_id: str) -> UserSummary:
        summary_id = generate_prefixed_id("SUMM_")
        summary = UserSummary(
            id=summary_id,
            user_id=user_id,
            content="",
            metadata={},
            conversation_ids=[],
            action_ids=[],
        )
        self._summaries[summary_id] = summary
        return summary

    async def update_summary(self, summary: UserSummary) -> UserSummary:
        self._summaries[summary.id] = summary
        return summary

    async def add_action(self, action: UserAction) -> UserAction:
        self._actions.append(action)
        return action

    async def get_user_actions(
        self, user_id: str, action_type: str | None = None, limit: int = 100
    ) -> list[UserAction]:
        user_actions = [a for a in self._actions if a.user_id == user_id]

        if action_type:
            user_actions = [a for a in user_actions if a.action_type == action_type]

        user_actions.sort(key=lambda a: a.created_at, reverse=True)

        return user_actions[:limit]
