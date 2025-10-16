from __future__ import annotations

from typing import Protocol

from ..models import UserAction, UserSummary


class UserSummaryAdapter(Protocol):
    async def get_summary(self, user_id: str) -> UserSummary | None: ...

    async def create_summary(self, user_id: str) -> UserSummary: ...

    async def update_summary(self, summary: UserSummary) -> UserSummary: ...

    async def add_action(self, action: UserAction) -> UserAction: ...

    async def get_user_actions(
        self, user_id: str, action_type: str | None = None, limit: int = 100
    ) -> list[UserAction]: ...
