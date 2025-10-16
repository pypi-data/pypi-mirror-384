class DoryError(Exception):
    """Base class for Dory domain exceptions."""


class ConversationNotFoundError(DoryError):
    """Raised when a conversation id does not exist in storage."""

    def __init__(self, conversation_id: str) -> None:  # noqa: D401
        super().__init__(f"Conversation {conversation_id} not found")
        self.conversation_id = conversation_id
