import os
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from friday.tools.memory import (
    _get_collection,
    CHROMA_PERSIST_PATH,
    COLLECTION_NAME,
    remember,
    recall,
)


@pytest.fixture(autouse=True)
def clean_chroma_client():
    """Use a unique throwaway collection per test to avoid file lock / state bleed issues."""
    import friday.tools.memory as memory_module
    from uuid import uuid4

    # Before test: point to a fresh throwaway collection
    memory_module._collection_name_override = f"test_{uuid4().hex}"
    memory_module._chroma_client = None
    memory_module._embedding_model = None

    yield

    # After test: delete the throwaway collection and reset
    try:
        client = memory_module._get_client()
        client.delete_collection(memory_module._collection_name_override)
    except Exception:
        pass
    memory_module._collection_name_override = None
    memory_module._chroma_client = None
    memory_module._embedding_model = None


def test_get_collection_creates_store_and_returns_same():
    """Calling _get_collection() twice should create chroma_store/ and return same collection."""
    import friday.tools.memory as memory_module

    # Temporarily clear the override to test base COLLECTION_NAME behavior
    saved_override = memory_module._collection_name_override
    memory_module._collection_name_override = None
    memory_module._chroma_client = None

    store_path = CHROMA_PERSIST_PATH

    # First call — should create the directory
    col1 = _get_collection()
    assert os.path.isdir(store_path), f"Expected {store_path} to be created"
    assert col1.name == COLLECTION_NAME

    # Second call — should return the same collection
    col2 = _get_collection()
    assert col2.name == COLLECTION_NAME
    assert col1.name == col2.name

    # Restore the autouse fixture's override for subsequent tests
    memory_module._chroma_client = None
    memory_module._collection_name_override = saved_override


def test_remember_stores_entry():
    """remember() returns a dict with memory_id, status, and category keys."""
    result = remember("Boss prefers dark mode", "preference")
    assert isinstance(result, dict)
    assert "memory_id" in result
    assert "status" in result
    assert "category" in result


def test_remember_returns_memory_id():
    """memory_id is a non-empty string."""
    result = remember("Remember to book meeting room", "task")
    assert isinstance(result.get("memory_id"), str)
    assert len(result["memory_id"]) > 0


def test_remember_rejects_empty_content():
    """remember() with empty content returns error status."""
    result = remember("", "fact")
    assert result.get("status") == "error"


def test_remember_assigns_correct_category():
    """returned category matches the input category."""
    result = remember("Water the plants", "reminder")
    assert result.get("category") == "reminder"


def test_remember_deduplication():
    """Two nearly identical remember() calls result in duplicate status on second."""
    remember("The project deadline is Friday", "task")
    result = remember("The project deadline is Friday", "task")
    assert result.get("status") == "duplicate"


@pytest.fixture
def seed_memories():
    """Seed 3 memories into ChromaDB using a dedicated test collection."""
    import friday.tools.memory as memory_module

    # Use a fresh in-memory client for this fixture to avoid handle conflicts
    test_collection_name = "test_seed_memories"
    test_client = memory_module.chromadb.PersistentClient(path=memory_module.CHROMA_PERSIST_PATH)
    test_col = test_client.get_or_create_collection(name=test_collection_name)
    embed = memory_module._get_embedding_model()

    memories = [
        ("Boss prefers dark mode on all interfaces", "preference"),
        ("Remind Boss to call Pepper on Friday", "reminder"),
        ("Boss decided to use ChromaDB for memory storage", "task"),
    ]
    for content, category in memories:
        e = embed.encode([content])
        mid = str(memory_module.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        test_col.add(
            ids=[mid],
            embeddings=e.tolist(),
            documents=[content],
            metadatas=[{"category": category, "timestamp": ts, "source": "explicit"}],
        )

    # Patch _get_collection to return our test collection for the duration
    original_get_collection = memory_module._get_collection
    memory_module._get_collection = lambda: test_col

    yield test_col

    memory_module._get_collection = original_get_collection


def test_recall_returns_relevant_results(seed_memories):
    """recall("what are Boss's preferences") returns at least 1 result."""
    results = recall("what are Boss's preferences")
    assert isinstance(results, list)
    assert len(results) >= 1


def test_recall_respects_limit(seed_memories):
    """recall(query, limit=1) returns exactly 1 result."""
    results = recall("Boss preferences and reminders", limit=1)
    assert isinstance(results, list)
    assert len(results) == 1


def test_recall_result_has_required_keys(seed_memories):
    """Each recall result has content, category, timestamp, relevance_score."""
    results = recall("Boss's interface preferences")
    assert len(results) >= 1
    for r in results:
        assert "content" in r
        assert "category" in r
        assert "timestamp" in r
        assert "relevance_score" in r


def test_recall_empty_collection():
    """recall() on an empty collection returns an empty list without error."""
    import friday.tools.memory as memory_module

    # Create a fresh empty collection with a unique name
    empty_col_name = "test_empty_collection"
    empty_client = memory_module.chromadb.PersistentClient(path=memory_module.CHROMA_PERSIST_PATH)
    empty_col = empty_client.get_or_create_collection(name=empty_col_name)

    original_get_collection = memory_module._get_collection
    memory_module._get_collection = lambda: empty_col

    results = recall("anything at all")

    memory_module._get_collection = original_get_collection
    memory_module._chroma_client = None
    memory_module._embedding_model = None

    assert isinstance(results, list)
    assert len(results) == 0


def test_recall_filters_low_relevance(seed_memories):
    """recall() with an unrelated query returns results filtered by relevance threshold."""
    results = recall("quantum physics equations", limit=5)
    assert isinstance(results, list)
    # All returned results should have relevance_score >= 0.3, or list is empty
    if results:
        for r in results:
            assert r.get("relevance_score", 0) >= 0.3


def test_forget_deletes_memory(seed_memories):
    """forget(memory_id) removes the entry from ChromaDB."""
    from friday.tools.memory import remember, forget

    # Store a new memory
    result = remember("Temporary note to forget", "fact")
    memory_id = result["memory_id"]

    # Forget it
    forget_result = forget(memory_id)
    assert forget_result.get("status") == "deleted"

    # Verify it's gone by trying to recall it
    remaining = recall("Temporary note")
    for r in remaining:
        assert r.get("content") != "Temporary note to forget"


def test_forget_nonexistent_id_returns_error(seed_memories):
    """forget() with a non-existent memory_id returns not_found status."""
    from friday.tools.memory import forget

    result = forget("fake-id-999")
    assert result.get("status") == "not_found"


def test_forget_invalidates_deduplication(seed_memories):
    """After forgetting a memory, re-remembering it creates a new entry (not duplicate)."""
    from friday.tools.memory import remember, forget

    # Store and forget
    result = remember("Forgettable thought", "fact")
    memory_id = result["memory_id"]
    forget(memory_id)

    # Re-remember should succeed as new, not duplicate
    new_result = remember("Forgettable thought", "fact")
    assert new_result.get("status") == "stored"
    assert new_result.get("memory_id") != memory_id
