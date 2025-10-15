from pydantic import BaseModel, Field

__all__ = ["ConversationConfig"]


class ConversationConfig(BaseModel):
    """Runtime configuration for conversation behaviour."""

    # Maximum period of inactivity (in days) after which a new
    # conversation will be created instead of re-using the previous one.
    # The counter is reset every time the conversation `updated_at` field
    # is modified (i.e. whenever a new message is stored).
    reuse_window_days: int = Field(
        default=14,
        ge=0,
        description=(
            "Maximum inactivity window in days to reuse the last conversation."
        ),
    )
    history_limit: int = Field(
        default=30,
        ge=0,
        description="Maximum number of past messages to include in a reply.",
    )
    conversation_id_prefix: str = Field(
        default="CONV_",
        min_length=1,
        description="Prefix used when generating conversation identifiers.",
    )
    message_id_prefix: str = Field(
        default="MSG_",
        min_length=1,
        description="Prefix used when generating message identifiers.",
    )

    connection_timeout_seconds: int = Field(
        default=30,
        ge=0,
        description="Adapter connection timeout in seconds.",
    )  # Adapter connection timeout
