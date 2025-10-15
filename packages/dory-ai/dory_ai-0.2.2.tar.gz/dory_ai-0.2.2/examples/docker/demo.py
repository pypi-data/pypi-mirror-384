#!/usr/bin/env python3
"""Docker demo script for Dory library."""

import asyncio
import os
from datetime import datetime

from mongoengine import connect

from dory.common import ChatRole, MessageType
from dory.embeddings import build_embeddings
from dory.messages import Messages
from dory.messages.adapters.mongo import MongoDBAdapter
from dory.messages.config import ConversationConfig
from dory.users_summaries import (
    MongoDBAdapter as UserSummaryMongoAdapter,
)
from dory.users_summaries import (
    UserSummary,
    UserSummaryAgent,
    UserSummaryConfig,
)


def print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


async def run_demo() -> None:
    print_section("Dory Docker Demo")

    mongodb_uri = os.environ.get(
        "MONGODB_URI",
    )

    # Create MongoDB connection manually
    print("\n→ Creating MongoDB connection...")
    connect(
        host=mongodb_uri,
        alias="dory_demo",
        uuidRepresentation="standard",
    )
    print("✓ MongoDB connection established with alias 'dory_demo'")

    # Messages service
    print_section("Messages Service")
    config = ConversationConfig(
        max_messages=10,
        summarize_after=5,
        mongodb_uri=mongodb_uri,
        use_mongodb=True,
    )
    # Use existing connection
    messages = Messages(
        MongoDBAdapter(use_existing_connection=True, alias="dory_demo"), config
    )

    convo = await messages.get_or_create_conversation(user_id="demo_user")
    cid = convo.id
    for content, role in [
        ("Hello! I need help with Python decorators.", ChatRole.USER),
        ("Decorators modify functions.", ChatRole.AI),
        ("Can you show me a simple example?", ChatRole.USER),
    ]:
        await messages.add_message(
            conversation_id=cid,
            user_id="demo_user",
            chat_role=role,
            content=content,
            message_type=(
                MessageType.USER_MESSAGE
                if role == ChatRole.USER
                else MessageType.REQUEST_RESPONSE
            ),
        )
    history = await messages.get_chat_history(conversation_id=cid)
    print(f"Messages stored: {len(history)}")

    # Embeddings service (Chroma via mem0)
    print_section("Embeddings Service")
    api_key = os.environ.get("OPENAI_API_KEY")
    emb = build_embeddings(
        api_key=api_key,
        store="chroma",
        store_path="/app/chroma_db",
        collection="dory_demo_memories",
    )

    # Store memories
    print("\n→ Storing memories...")
    conversation_messages = [
        {"role": "user", "content": "Can you teach me about the @ syntax?"},
        {
            "role": "assistant",
            "content": "The @ syntax is used to apply decorators in Python",
        },
        {"role": "user", "content": "Can you show me a practical example?"},
    ]
    await emb.remember(
        messages=conversation_messages,
        user_id="demo_user",
        conversation_id=cid,
        metadata={
            "source": "demo",
            "type": "conversation",
            "timestamp": datetime.now().isoformat(),
        },
    )

    res = await emb.recall(
        query="What is the user learning about?",
        user_id="demo_user",
        conversation_id=cid,
        limit=5,
    )
    print(f"\nMemories found: {len(res)}")
    for i, r in enumerate(res, 1):
        print(
            f"  {i}. content={r.get('content')!r} score={r.get('score')} meta={r.get('metadata')}"
        )

    # Store raw embeddings and search
    for doc in [
        "Python decorators are a powerful feature for modifying functions",
        "The @ syntax is syntactic sugar for decorator application",
        "Decorators can be stacked and can accept arguments",
    ]:
        await emb.store_embedding(
            content=doc,
            user_id="demo_user",
            conversation_id=cid,
            metadata={"type": "documentation", "source": "demo"},
        )
    eres = await emb.search_embeddings(
        query="How to use decorator syntax?",
        user_id="demo_user",
        conversation_id=cid,
        limit=3,
    )
    print(f"Embeddings found: {len(eres)}")
    for i, r in enumerate(eres, 1):
        print(
            f"  {i}. content={r.get('content')!r} score={r.get('score')} meta={r.get('metadata')}"
        )

    # User Summary Service
    print_section("User Summary Service")

    # Initialize UserSummary
    if api_key:
        print("✓ Initializing UserSummary with OpenAI agent")
        # Use existing connection
        summary_adapter = UserSummaryMongoAdapter(
            use_existing_connection=True,
            alias="dory_demo",
        )
        summary_agent = UserSummaryAgent(api_key=api_key)
        summary_config = UserSummaryConfig(
            max_conversation_messages=50,
            summary_generation_threshold_messages=3,
        )
        user_summary = UserSummary(
            adapter=summary_adapter,
            agent=summary_agent,
            config=summary_config,
        )

        # Track some user actions
        print("\n→ Tracking user actions...")
        await user_summary.track_action(
            user_id="demo_user",
            action_type="tutorial_request",
            action_name="Requested Python decorators tutorial",
            metadata={"topic": "decorators", "level": "beginner"},
            conversation_id=cid,
        )
        await user_summary.track_action(
            user_id="demo_user",
            action_type="example_request",
            action_name="Asked for simple decorator example",
            metadata={"preference": "simple_examples"},
        )
        print("✓ Actions tracked")

        # Update summary based on conversation
        print("\n→ Generating user summary from conversation...")
        summary_result = await user_summary.update_summary(
            user_id="demo_user",
            conversation_id=cid,
            messages_service=messages,
        )
        print("✓ Summary generated:")
        print(f"  Content: {summary_result.content}")
        print(f"  Metadata: {summary_result.metadata}")

        # Get context for LLM prompt
        print("\n→ Getting context for LLM prompts...")
        context = await user_summary.get_context_for_prompt(
            user_id="demo_user",
            include_actions=True,
        )
        print(f"✓ Context generated ({len(context)} chars):")
        print(f"{context[:500]}..." if len(context) > 500 else context)

        # Append additional information
        print("\n→ Appending new information to summary...")
        updated_summary = await user_summary.append_to_summary(
            user_id="demo_user",
            new_information="User completed the decorator tutorial and showed interest in advanced topics like class decorators and decorator factories.",
        )
        print(f"✓ Summary updated: {len(updated_summary.content)} chars")

        print("✓ Summary updated:")
        print(f"  Content: {updated_summary.content}")
        print(f"  Metadata: {updated_summary.metadata}")

    else:
        print("⚠️  No OpenAI API key found - skipping AI-powered summary generation")
        print("   Set OPENAI_API_KEY environment variable to enable this feature")

    print_section("Demo Complete")


if __name__ == "__main__":
    asyncio.run(run_demo())
