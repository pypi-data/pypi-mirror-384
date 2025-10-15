from dory.messages.adapters.utils import generate_prefixed_id
from dory.users_summaries.adapters import InMemoryAdapter
from dory.users_summaries.models import UserAction


async def test_should_create_and_retrieve_user_summary() -> None:
    adapter = InMemoryAdapter()

    summary = await adapter.create_summary(user_id="user_123")

    assert summary.user_id == "user_123"
    assert summary.content == ""
    assert summary.metadata == {}
    assert summary.conversation_ids == []
    assert summary.action_ids == []

    retrieved = await adapter.get_summary(user_id="user_123")
    assert retrieved is not None
    assert retrieved.id == summary.id


async def test_should_update_existing_summary() -> None:
    adapter = InMemoryAdapter()

    original = await adapter.create_summary(user_id="user_123")

    original.content = "Updated content"
    original.metadata = {"updated": True}
    original.conversation_ids = ["CONV_001"]

    updated = await adapter.update_summary(original)

    assert updated.content == "Updated content"
    assert updated.metadata == {"updated": True}
    assert updated.conversation_ids == ["CONV_001"]

    retrieved = await adapter.get_summary(user_id="user_123")
    assert retrieved is not None
    assert retrieved.content == "Updated content"


async def test_should_store_and_retrieve_user_actions() -> None:
    adapter = InMemoryAdapter()

    action1 = UserAction(
        id=generate_prefixed_id("ACT_"),
        user_id="user_123",
        action_type="loan_application",
        action_name="Applied for loan",
        metadata={"amount": 50000},
    )

    action2 = UserAction(
        id=generate_prefixed_id("ACT_"),
        user_id="user_123",
        action_type="car_comparison",
        action_name="Compared vehicles",
        metadata={"vehicles": ["RAV4", "CR-V"]},
    )

    action3 = UserAction(
        id=generate_prefixed_id("ACT_"),
        user_id="user_456",
        action_type="loan_application",
        action_name="Applied for loan",
        metadata={"amount": 30000},
    )

    await adapter.add_action(action1)
    await adapter.add_action(action2)
    await adapter.add_action(action3)

    user_actions = await adapter.get_user_actions(user_id="user_123")
    assert len(user_actions) == 2

    loan_actions = await adapter.get_user_actions(
        user_id="user_123", action_type="loan_application"
    )
    assert len(loan_actions) == 1
    assert loan_actions[0].metadata["amount"] == 50000


async def test_should_return_none_when_summary_not_found() -> None:
    adapter = InMemoryAdapter()

    summary = await adapter.get_summary(user_id="nonexistent")
    assert summary is None


async def test_should_respect_limit_when_retrieving_actions() -> None:
    adapter = InMemoryAdapter()

    for i in range(10):
        action = UserAction(
            id=generate_prefixed_id("ACT_"),
            user_id="user_123",
            action_type="test_action",
            action_name=f"Action {i}",
        )
        await adapter.add_action(action)

    limited_actions = await adapter.get_user_actions(user_id="user_123", limit=5)
    assert len(limited_actions) == 5
