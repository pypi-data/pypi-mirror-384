from enum import Enum
from typing import Final

__all__: Final = (
    "ChatRole",
    "MessageType",
)


class ChatRole(str, Enum):
    """The speaker of a message in a conversation."""

    USER = "user"
    AI = "ai"
    HUMAN = "human"


class MessageType(str, Enum):
    """A coarse-grained classification used by orchestrators and tools."""

    USER_MESSAGE = "user_message"
    REQUEST_RESPONSE = "request_response"
