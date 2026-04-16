import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

import friday.tools.memory as memory_module
from friday.tools.memory import recall, remember

from dateutil import parser
from friday.tools.calendar import parse_datetime


@pytest.fixture(autouse=True)
def calendar_test_setup():
    """Use a unique throwaway collection per test to avoid state bleed."""
    memory_module._collection_name_override = f"test_{uuid4().hex}"
    memory_module._chroma_client = None
    memory_module._embedding_model = None

    import friday.tools.calendar as calendar_module
    calendar_module._calendar_service = None

    yield

    try:
        client = memory_module._get_client()
        client.delete_collection(memory_module._collection_name_override)
    except Exception:
        pass
    memory_module._collection_name_override = None
    memory_module._chroma_client = None
    memory_module._embedding_model = None
    calendar_module._calendar_service = None


# --- parse_datetime tests ---

def test_parse_datetime_sunday():
    result = parse_datetime("Sunday at 3pm")
    assert isinstance(result, dict)
    assert "datetime" in result
    assert "T15:00" in result["datetime"]


def test_parse_datetime_tomorrow():
    result = parse_datetime("tomorrow at 9am")
    assert "T09:00" in result["datetime"]


def test_parse_datetime_explicit_date():
    result = parse_datetime("April 20 at 2pm")
    assert "T14:00" in result["datetime"]


def test_parse_datetime_empty_returns_error():
    result = parse_datetime("")
    assert result == {"status": "error", "reason": "empty datetime string"}


def test_parse_datetime_unparseable_returns_error():
    result = parse_datetime("blah blah blah")
    assert result["status"] == "error"


# --- set_reminder tests ---

def test_set_reminder_returns_required_keys():
    from friday.tools.calendar import set_reminder
    result = set_reminder("Call Pepper", "2026-04-20T17:00:00")
    for key in ("memory_id", "event_id", "status", "title", "datetime"):
        assert key in result, f"Missing key: {key}"


def test_set_reminder_status_is_set():
    from friday.tools.calendar import set_reminder
    result = set_reminder("Call Pepper", "2026-04-20T17:00:00")
    assert result["status"] == "set"


def test_set_reminder_stores_in_memory():
    from friday.tools.calendar import set_reminder
    set_reminder("Call Pepper", "2026-04-20T17:00:00")
    results = recall("Call Pepper")
    assert len(results) >= 1


def test_set_reminder_memory_stored_before_calendar():
    from friday.tools.calendar import set_reminder

    fake_insert = MagicMock()
    fake_insert.execute.side_effect = Exception("Calendar API is down")
    fake_events = MagicMock()
    fake_events.insert.return_value = fake_insert
    fake_service = MagicMock()
    fake_service.events.return_value = fake_events

    with patch("friday.tools.calendar._get_calendar_service", return_value=fake_service):
        result = set_reminder("Call Pepper", "2026-04-20T17:00:00")

    assert "memory_id" in result
    assert result["status"] == "set_memory_only"


def test_set_reminder_empty_title_returns_error():
    from friday.tools.calendar import set_reminder
    result = set_reminder("", "2026-04-20T17:00:00")
    assert result["status"] == "error"


def test_set_reminder_invalid_datetime_returns_error():
    from friday.tools.calendar import set_reminder
    result = set_reminder("Call Pepper", "not a date")
    assert result["status"] == "error"


# --- get_reminders tests ---

def test_get_reminders_returns_list():
    from friday.tools.calendar import get_reminders
    remember("Reminder to call Pepper", category="reminder", source="voice")
    remember("Reminder to email Mom", category="reminder", source="voice")
    result = get_reminders(limit=5)
    assert isinstance(result, list)
    assert len(result) >= 2


def test_get_reminders_only_returns_reminders():
    from friday.tools.calendar import get_reminders
    remember("Call Pepper", category="reminder", source="voice")
    remember("Likes pizza", category="preference", source="voice")
    result = get_reminders(limit=5)
    for item in result:
        assert item["category"] == "reminder"


def test_get_reminders_respects_limit():
    from friday.tools.calendar import get_reminders
    remember("Reminder 1", category="reminder", source="voice")
    remember("Reminder 2", category="reminder", source="voice")
    remember("Reminder 3", category="reminder", source="voice")
    result = get_reminders(limit=2)
    assert len(result) <= 2


def test_get_reminders_empty_returns_list():
    from friday.tools.calendar import get_reminders
    result = get_reminders()
    assert result == []


# --- cancel_reminder tests ---

def test_cancel_reminder_returns_cancelled():
    from friday.tools.calendar import set_reminder, cancel_reminder
    result = set_reminder("Reminder to call Pepper", "2026-04-20T17:00:00")
    memory_id = result["memory_id"]
    cancel_result = cancel_reminder(memory_id)
    assert cancel_result["status"] == "cancelled"


def test_cancel_reminder_removes_from_memory():
    from friday.tools.calendar import set_reminder, cancel_reminder
    result = set_reminder("Reminder to call Pepper", "2026-04-20T17:00:00")
    memory_id = result["memory_id"]
    cancel_reminder(memory_id)
    remaining = recall("Reminder to call Pepper")
    ids = [r.get("memory_id") for r in remaining]
    assert memory_id not in ids


def test_cancel_reminder_not_found():
    from friday.tools.calendar import cancel_reminder
    result = cancel_reminder("fake-id-999")
    assert result["status"] == "not_found"


def test_cancel_reminder_with_event_id():
    from friday.tools.calendar import set_reminder, cancel_reminder

    fake_delete = MagicMock()
    fake_delete.execute.return_value = {}
    fake_events = MagicMock()
    fake_events.delete.return_value = fake_delete
    fake_service = MagicMock()
    fake_service.events.return_value = fake_events

    with patch("friday.tools.calendar._get_calendar_service", return_value=fake_service):
        set_result = set_reminder("Reminder to call Pepper", "2026-04-20T17:00:00")
        memory_id = set_result["memory_id"]
        event_id = "fake-event-id"
        cancel_reminder(memory_id, event_id=event_id)

    fake_events.delete.assert_called_once_with(calendarId="primary", eventId=event_id)


def test_cancel_reminder_calendar_failure_still_cancels_memory():
    from friday.tools.calendar import set_reminder, cancel_reminder

    fake_delete = MagicMock()
    fake_delete.execute.side_effect = Exception("Calendar API is down")
    fake_events = MagicMock()
    fake_events.delete.return_value = fake_delete
    fake_service = MagicMock()
    fake_service.events.return_value = fake_events

    with patch("friday.tools.calendar._get_calendar_service", return_value=fake_service):
        set_result = set_reminder("Reminder to call Pepper", "2026-04-20T17:00:00")
        memory_id = set_result["memory_id"]
        cancel_result = cancel_reminder(memory_id, event_id="fake-event-id")

    assert cancel_result["status"] == "cancelled"
    remaining = recall("Reminder to call Pepper")
    ids = [r.get("memory_id") for r in remaining]
    assert memory_id not in ids
