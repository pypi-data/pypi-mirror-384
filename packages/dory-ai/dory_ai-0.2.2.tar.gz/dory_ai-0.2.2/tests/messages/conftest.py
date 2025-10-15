from collections.abc import AsyncGenerator
from typing import Any

import mongoengine
import mongomock
import pytest
import pytest_asyncio
from mongoengine_plus.aio.utils import (
    create_awaitable,
)

from dory.messages.adapters.mongo import (
    ConversationDocument,
    MessageDocument,
    MongoDBAdapter,
)


@pytest.fixture(scope="session", autouse=True)
def db_connection() -> Any:
    """Autouse in-memory MongoDB connection via mongomock for the whole test session."""

    return mongoengine.connect(
        db="db",
        alias="default",
        host="mongodb://localhost",
        mongo_client_class=mongomock.MongoClient,
    )


@pytest_asyncio.fixture(scope="function")
async def mongo_adapter() -> AsyncGenerator[MongoDBAdapter, None]:
    """Provide a MongoDBAdapter backed by an in-memory mongomock connection for tests."""

    adapter = MongoDBAdapter()

    yield adapter

    await create_awaitable(ConversationDocument.drop_collection)
    await create_awaitable(MessageDocument.drop_collection)
