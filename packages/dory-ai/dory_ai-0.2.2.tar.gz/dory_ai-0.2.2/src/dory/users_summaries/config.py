from __future__ import annotations

from pydantic import BaseModel

__all__ = ["UserSummaryConfig"]


class UserSummaryConfig(BaseModel):
    max_conversation_messages: int = 100
    max_recent_actions: int = 20
    max_summary_length: int = 1000
    include_actions_in_context: bool = True
    auto_update_on_conversation_end: bool = False
    summary_generation_threshold_messages: int = 10
