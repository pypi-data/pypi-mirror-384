from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

__all__ = [
    "PromptModel",
    "UserSummaryGenerationInput",
    "UserSummaryGenerationOutput",
]


class PromptModel(BaseModel):
    prompt_name: str
    model: str
    json_format: bool
    temperature: float
    template: str


class UserSummaryGenerationInput(BaseModel):
    existing_summary: str | None = Field(
        default=None, description="Current user summary if it exists"
    )
    conversation_messages: list[str] = Field(
        description="Recent conversation messages formatted as 'role: content'"
    )
    user_actions: list[str] = Field(
        default_factory=list,
        description="Recent user actions formatted as 'action_name: metadata'",
    )


class UserSummaryGenerationOutput(BaseModel):
    content: str = Field(description="Human-readable summary of the user")
    metadata: dict[str, Any] = Field(
        description="Structured data extracted from conversations and actions"
    )
    key_topics: list[str] = Field(description="Main topics discussed or acted upon")
    confidence_score: float = Field(
        description="Confidence in the summary accuracy (0.0-1.0)"
    )
