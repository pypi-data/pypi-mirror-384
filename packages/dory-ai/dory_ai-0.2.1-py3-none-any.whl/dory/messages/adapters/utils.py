from __future__ import annotations

import uuid
from typing import Any

from ...common.types import ChatRole

__all__ = [
    "generate_prefixed_id",
    "history_item",
]


def generate_prefixed_id(prefix: str) -> str:
    """Create a unique identifier using the given prefix and a hex UUID.

    Using the standard library keeps this independent from storage backends.
    """

    return f"{prefix}{uuid.uuid4().hex}"


def history_item(chat_role: ChatRole, content: Any) -> dict[str, Any]:
    """Return a single chat history item mapping role->content."""

    return {chat_role.value: content}
