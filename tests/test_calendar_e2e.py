import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch

import friday.tools.memory as memory_module
from friday.tools.memory import recall
from friday.tools.calendar import set_reminder, get_reminders, cancel_reminder


@pytest.fixture(autouse=True)
def mock_calendar_and_collection():
    memory_module._collection_name_override = f"test_{uuid4().hex}"
    memory_module._chroma_client = None
    memory_module._embedding_model = None

    mock_service = MagicMock()
    mock_service.events().insert().execute.return_value = {"id": "mock-event-id"}
    mock_service.events().delete().execute.return_value = {}

    with patch("friday.tools.calendar._get_calendar_service", return_value=mock_service):
        yield

    try:
        client = memory_module._get_client()
        client.delete_collection(memory_module._collection_name_override)
    except Exception:
        pass
    memory_module._collection_name_override = None
    memory_module._chroma_client = None
    memory_module._embedding_model = None


def test_set_reminder_e2e():
    result = set_reminder("Call Pepper", "2026-04-20T17:00:00")
    assert result["status"] in ("set", "set_memory_only")
    assert result["title"] == "Call Pepper"
    assert result["memory_id"] is not None
    memories = recall("Call Pepper", limit=3)
    assert any("Call Pepper" in m["content"] for m in memories)


def test_get_reminders_e2e():
    set_reminder("Reminder: Team standup", "2026-04-21T09:00:00")
    set_reminder("Reminder: Review AutoClip", "2026-04-22T14:00:00")
    reminders = get_reminders(limit=5)
    assert len(reminders) >= 2
    assert all(r["category"] == "reminder" for r in reminders)


def test_cancel_reminder_e2e():
    result = set_reminder("Cancel this task", "2026-04-23T10:00:00")
    memory_id = result["memory_id"]
    cancel = cancel_reminder(memory_id)
    assert cancel["status"] == "cancelled"
    memories = recall("Cancel this task", limit=3)
    assert not any("Cancel this task" in m["content"] for m in memories)
