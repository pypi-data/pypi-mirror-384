from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

__all__ = ["UserSummary"]


class UserSummary(BaseModel):
    id: str = Field(...)
    user_id: str = Field(...)
    content: str = Field(...)
    metadata: dict[str, Any] = Field(default_factory=dict)
    conversation_ids: list[str] = Field(default_factory=list)
    action_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
