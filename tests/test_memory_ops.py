import pytest
from uuid import uuid4

import friday.tools.memory as memory_module
from friday.tools.memory import recall

from friday.dashboard.memory_ops import (
    list_all,
    search,
    edit,
    bulk_delete,
    export,
    stats,
)


@pytest.fixture(autouse=True)
def dashboard_test_setup():
    memory_module._collection_name_override = f"test_{uuid4().hex}"
    memory_module._chroma_client = None
    memory_module._embedding_model = None

    yield

    try:
        client = memory_module._get_client()
        client.delete_collection(memory_module._collection_name_override)
    except Exception:
        pass
    memory_module._collection_name_override = None
    memory_module._chroma_client = None
    memory_module._embedding_model = None


def test_list_all_returns_grouped_dict():
    from friday.tools.memory import remember
    remember("Likes blue", category="preference", source="voice")
    remember("Prefers dark theme", category="preference", source="voice")
    remember("Call Mom", category="reminder", source="voice")
    result = list_all(grouped=True)
    assert isinstance(result, dict)
    assert "preference" in result
    assert "reminder" in result
    assert len(result["preference"]) == 2


def test_search_returns_results():
    from friday.tools.memory import remember
    remember("Boss uses dark mode", category="fact", source="voice")
    results = search("dark mode", limit=3)
    assert len(results) >= 1


def test_edit_updates_content():
    from friday.tools.memory import remember
    mem = remember("Old content here", category="fact", source="voice")
    memory_id = mem["memory_id"]
    edit(memory_id, "new content here")
    updated = recall("new content here", limit=3)
    assert any("new content here" in r["content"] for r in updated)
    old = recall("Old content here", limit=3)
    assert not any("Old content here" in r["content"] for r in old)


def test_delete_removes_memory():
    from friday.tools.memory import remember
    mem = remember("To be deleted", category="fact", source="voice")
    memory_id = mem["memory_id"]
    delete_fn = __import__("friday.dashboard.memory_ops", fromlist=["bulk_delete"]).bulk_delete
    from friday.tools.memory import _get_collection
    collection = _get_collection()
    collection.delete(ids=[memory_id])
    remaining = recall("To be deleted", limit=3)
    assert not any("To be deleted" in r["content"] for r in remaining)


def test_bulk_delete_by_category():
    from friday.tools.memory import remember
    remember("Reminder one", category="reminder", source="voice")
    remember("Reminder two", category="reminder", source="voice")
    remember("A random fact", category="fact", source="voice")
    result = bulk_delete("reminder")
    assert result["deleted"] == 2
    remaining = export(category=None)
    categories = [r.get("category") for r in remaining]
    assert "reminder" not in categories
    assert "fact" in categories


def test_export_returns_all():
    from friday.tools.memory import remember
    remember("Fact one", category="fact", source="voice")
    remember("Fact two", category="fact", source="voice")
    remember("Pref one", category="preference", source="voice")
    result = export()
    assert len(result) >= 3
    for item in result:
        assert "content" in item
        assert "category" in item
        assert "timestamp" in item


def test_export_filtered_by_category():
    from friday.tools.memory import remember
    remember("My reminder", category="reminder", source="voice")
    remember("My preference", category="preference", source="voice")
    result = export(category="reminder")
    for item in result:
        assert item["category"] == "reminder"


def test_stats_returns_counts():
    from friday.tools.memory import remember
    remember("Pref one", category="preference", source="voice")
    remember("Pref two", category="preference", source="voice")
    remember("A fact", category="fact", source="voice")
    result = stats()
    assert "total" in result
    assert "by_category" in result
    assert "store_size_bytes" in result
