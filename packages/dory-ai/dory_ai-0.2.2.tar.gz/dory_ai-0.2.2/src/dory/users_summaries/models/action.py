from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

__all__ = ["UserAction"]


class UserAction(BaseModel):
    id: str = Field(...)
    user_id: str = Field(...)
    action_type: str = Field(...)
    action_name: str = Field(...)
    metadata: dict[str, Any] = Field(default_factory=dict)
    conversation_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
