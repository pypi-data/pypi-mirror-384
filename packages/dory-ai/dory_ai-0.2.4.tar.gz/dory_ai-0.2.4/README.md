# Dory

## AI Memory & Conversation Management Library

A library for managing conversation history and memory in AI-powered
applications, designed for reusability across projects.

## Overview

Dory provides three core services for AI applications:

### **Messages Service**

Simple, reliable conversation and message management with:

- **Automatic Conversation Management**: Reuses conversations within a 2-week
  window
- **Message Persistence**: Stores user messages and AI responses
- **LangChain/LangGraph Integration**: Returns chat history in the required
  format
- **MongoDB Support**: Production-ready persistence

### **Embeddings Service**

Advanced memory and vector search capabilities with:

- **Semantic Memory Storage**: Store and retrieve contextual memories
- **Vector Search**: Find relevant information using similarity search
- **Raw Embeddings**: Store and search unprocessed content for retrieval
- **Multiple Backends**: Support for Chroma (local) and MongoDB Atlas
- **Powered by Mem0**: Built on top of the robust Mem0 library

### **User Summaries Service**

AI-powered user profiling and understanding with:

- **Automatic User Profiling**: Generate comprehensive user summaries using LLM
- **Smart Action Detection**: Track preferences, facts, and behaviors
- **Contextual Understanding**: Extract insights from conversation history

## Installation

### Using uv (Recommended)

```bash
# Add to an existing project
uv add dory

# Or add to pyproject.toml dependencies
# Then run:
uv sync
```

### Using pip

```bash
pip install dory
```

### Add to pyproject.toml

```toml
[project]
dependencies = [
    "dory>=0.2.4",
    # ... other dependencies
]
```

## Quick Start

### Messages Service

```python
import asyncio
from dory.messages import Messages
from dory.messages.adapters.mongo import MongoDBAdapter
from dory.common import MessageType, ChatRole


async def messages_example():
    # Initialize with MongoDB
    adapter = MongoDBAdapter(
        connection_string="mongodb://localhost:27017/myapp",
        database="myapp",
    )

    # Create Messages service
    messages = Messages(adapter=adapter)

    # Get or create a conversation (reuses if within 2 weeks)
    conversation = await messages.get_or_create_conversation(user_id="user_123")

    # Add a user message
    await messages.add_message(
        conversation_id=conversation.id,
        user_id="user_123",
        chat_role=ChatRole.USER,
        content="What's the weather like?",
        message_type=MessageType.USER_MESSAGE
    )

    # Add an AI response
    await messages.add_message(
        conversation_id=conversation.id,
        user_id="user_123",
        chat_role=ChatRole.AI,
        content="It's sunny today!",
        message_type=MessageType.REQUEST_RESPONSE
    )

    # Get chat history for LangChain/LangGraph
    chat_history = await messages.get_chat_history(
        conversation_id=conversation.id,
        limit=30
    )
    # Returns: [{"user": "What's the weather like?"}, {"ai": "It's sunny today!"}]


if __name__ == "__main__":
    asyncio.run(messages_example())
```

### Embeddings Service

```python
import asyncio
from dory.embeddings import build_embeddings, Mem0Message


async def embeddings_example():
    # Initialize with Chroma (local vector store)
    embeddings = build_embeddings(
        api_key="your-openai-api-key",  # Required for OpenAI embeddings
        store="chroma",
        store_path="./chroma_db",
        collection="my_memories"
    )

    # Store contextual memories - Option 1: Simple string
    memory_id = await embeddings.remember(
        messages="User prefers Python over Java",
        user_id="user_123",
        conversation_id="conv_abc",
        metadata={"topic": "preferences"}
    )

    # Store memories - Option 2: Conversation format (RECOMMENDED)
    memory_id = await embeddings.remember(
        messages=[
            {"role": "user", "content": "I love Python programming"},
            {"role": "assistant", "content": "Python is great for many tasks!"},
            {"role": "user", "content": "I prefer it over Java"}
        ],
        user_id="user_123",
        conversation_id="conv_abc",
        metadata={"topic": "preferences"}
    )

    # Store memories - Option 3: Using Pydantic models (type-safe)
    memory_id = await embeddings.remember(
        messages=[
            Mem0Message(role="user", content="I love Python programming"),
            Mem0Message(role="assistant", content="Python is great!"),
        ],
        user_id="user_123",
        conversation_id="conv_abc"
    )

    # Search for relevant memories
    memories = await embeddings.recall(
        query="What programming languages does the user like?",
        user_id="user_123",
        limit=5
    )
    # Returns memories with relevance scores

    # Store raw embeddings for retrieval
    embedding_id = await embeddings.store_embedding(
        content="Python is a high-level programming language",
        user_id="user_123",
        metadata={"source": "documentation"}
    )

    # Search embeddings by similarity
    results = await embeddings.search_embeddings(
        query="Tell me about Python",
        user_id="user_123",
        limit=3
    )


if __name__ == "__main__":
    asyncio.run(embeddings_example())
```

### User Summaries Service

```python
import asyncio
from dory.users_summaries import UserSummaries
from dory.users_summaries.adapters.mongo import MongoDBAdapter


async def user_summaries_example():
    # Initialize with MongoDB
    adapter = MongoDBAdapter(
        connection_string="mongodb://localhost:27017/myapp",
        database="myapp",
    )

    # Create UserSummaries service with OpenAI
    user_summaries = UserSummaries(
        adapter=adapter,
        openai_api_key="your-openai-api-key"
    )

    # Generate or update user summary from conversation
    summary = await user_summaries.generate_summary(
        user_id="user_123",
        conversation_history=[
            {"role": "user", "content": "I love Python programming"},
            {"role": "ai", "content": "That's great! Python is versatile."},
            {"role": "user", "content": "I prefer dark mode in my IDE"},
        ]
    )

    # Access user summary and actions
    print(f"Summary: {summary.summary}")
    print(f"Actions detected: {len(summary.actions)}")

    for action in summary.actions:
        print(f"- {action.action_type}: {action.description}")

    # Get existing summary
    existing = await user_summaries.get_summary(user_id="user_123")
    if existing:
        print(f"Last updated: {existing.updated_at}")


if __name__ == "__main__":
    asyncio.run(user_summaries_example())
```

## API Reference

### Messages Service Ag

```python
# Initialize Messages with adapter
adapter = MongoDBAdapter(connection_string="...")
messages = Messages(adapter=adapter)

# Messages methods (all require keyword arguments)
async def get_or_create_conversation(self, *, user_id: str) -> Conversation:
    """Get recent conversation or create new one (2-week reuse window)."""

async def add_message(
    self,
    *,
    conversation_id: str | None = None,
    message_id: str | None = None,
    user_id: str,
    chat_role: ChatRole,
    content: Any,
    message_type: MessageType,
) -> Message:
    """Add a message. If conversation_id is None, a new conversation is created.
    If message_id is None, an ID is auto-generated.
    """

async def get_chat_history(
    self,
    *,
    conversation_id: str,
    limit: int | None = None
) -> list[dict[str, Any]]:
    """Get chat history in LangChain/LangGraph format."""
```

### Message Types

```python
class MessageType(str, Enum):
    USER_MESSAGE = "user_message"              # User input
    REQUEST_RESPONSE = "request_response"        # Final AI response
```

### Optional IDs

Both `conversation_id` and `message_id` can be provided. If omitted:

- conversation_id: a new conversation is created for the given `user_id`
- message_id: an ID is generated using the configured prefix

### Chat Roles

```python
class ChatRole(str, Enum):
    USER = "user"
    HUMAN = "human"
    AI = "ai"
```

### Models

```python
class Conversation:
    id: str                # Format: "CONV_<uuid>"
    user_id: str
    created_at: datetime
    updated_at: datetime

class Message:
    id: str                # Format: "MSG_<uuid>"
    conversation_id: str
    user_id: str
    chat_role: ChatRole
    content: Any           # String or dict
    message_type: MessageType
    created_at: datetime
```

### Embeddings Service API

```python
# Initialize with builder function
embeddings = build_embeddings(
    api_key="openai-api-key",           # Optional: for OpenAI embeddings
    store="chroma",                      # Options: "chroma", "mongodb", "memory"
    store_path="./chroma_db",           # For local stores
    connection_string="mongodb://...",  # For MongoDB Atlas
    collection="memories"                # Collection/index name
)

# Embeddings methods (all async, require keyword arguments)
async def remember(
    self,
    *,
    messages: str | list[dict[str, str]] | list[Mem0Message],
    user_id: str,
    conversation_id: str | None = None,
    metadata: dict[str, Any] | None = None
) -> str:
    """Store a memory with LLM processing for context extraction.

    Accepts three formats:
    - Simple string: "User likes Python"
    - List of dicts: [{"role": "user", "content": "..."}, ...]
    - List of Mem0Message objects (type-safe with validation)

    For best results with mem0, use conversation format (list of messages).
    """

async def recall(
    self,
    *,
    query: str,
    user_id: str,
    conversation_id: str | None = None,
    limit: int = 10
) -> list[dict[str, Any]]:
    """Search memories using semantic similarity."""

async def forget(
    self,
    *,
    user_id: str,
    conversation_id: str | None = None,
    memory_ids: list[str] | None = None
) -> int:
    """Delete memories and return count deleted."""

async def store_embedding(
    self,
    *,
    content: str,
    user_id: str,
    conversation_id: str | None = None,
    message_id: str | None = None,
    metadata: dict[str, Any] | None = None
) -> str:
    """Store raw content without LLM processing."""

async def search_embeddings(
    self,
    *,
    query: str,
    user_id: str,
    conversation_id: str | None = None,
    limit: int = 10
) -> list[dict[str, Any]]:
    """Search raw embeddings using vector similarity."""
```

### User Summaries Service API

```python
# Initialize with adapter
adapter = MongoDBAdapter(
    connection_string="mongodb://localhost:27017",
    database="myapp",
)
user_summaries = UserSummaries(
    adapter=adapter,
    openai_api_key="your-openai-api-key"
)

# User Summaries methods (all async, require keyword arguments)
async def generate_summary(
    self,
    *,
    user_id: str,
    conversation_history: list[dict[str, str]]
) -> UserSummary:
    """Generate or update user summary from conversation history.
    Creates new summary or updates existing one with new insights.
    """

async def get_summary(
    self,
    *,
    user_id: str
) -> UserSummary | None:
    """Get existing user summary."""

async def delete_summary(
    self,
    *,
    user_id: str
) -> bool:
    """Delete user summary. Returns True if deleted, False if not found."""
```

### User Summaries Models

```python
class UserSummary:
    id: str                # Format: "USR_<uuid>"
    user_id: str
    summary: str           # AI-generated summary
    actions: list[Action]  # Detected preferences, facts, behaviors
    created_at: datetime
    updated_at: datetime

class Action:
    action_type: str       # "preference", "fact", "behavior"
    description: str       # What was detected
```

## Configuration

### MongoDB Setup

```python
# For Messages
from dory.messages.adapters.mongo import MongoDBAdapter as MessagesAdapter
messages_adapter = MessagesAdapter(
    connection_string="mongodb://localhost:27017",
    database="myapp",
)

# For User Summaries
from dory.users_summaries.adapters.mongo import MongoDBAdapter as SummariesAdapter
summaries_adapter = SummariesAdapter(
    connection_string="mongodb://localhost:27017",
    database="myapp",
)

# For Embeddings (MongoDB Atlas with Vector Search)
embeddings = build_embeddings(
    api_key="openai-api-key",
    store="mongodb",
    connection_string="mongodb+srv://...",
    collection="memories"
)
```

**Indexes Created:**

- Conversations: `user_id`, `updated_at`
- Messages: `conversation_id`, `created_at`, compound index
- User Summaries: `user_id`, `updated_at`
- Embeddings: Requires MongoDB Atlas Vector Search index

### Chroma Setup

```python
embeddings = build_embeddings(
    api_key="openai-api-key",
    store="chroma",
    store_path="./chroma_db",  # Local directory
    collection="my_memories"
)
```

### In-Memory Setup (Testing)

```python
# For testing - no persistence
embeddings = build_embeddings(
    store="memory",
    collection="test_memories"
)
```

## Docker Example

A complete working example with Docker Compose is available in
`examples/docker/`:

```bash
cd examples/docker

# Copy environment file
cp env.example .env

# Add your OpenAI API key to .env (optional)
# OPENAI_API_KEY=your-key-here

# Start services
docker-compose up --build

# The demo will run automatically, showing all three services in action
```

The example demonstrates:

- Messages: Conversation management and history
- Embeddings: Memory storage and retrieval
- User Summaries: AI-powered user profiling

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific service tests
uv run pytest tests/messages/
uv run pytest tests/embeddings/
uv run pytest tests/users_summaries/
```

## License

MIT
