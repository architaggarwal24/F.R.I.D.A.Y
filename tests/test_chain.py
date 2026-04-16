from unittest.mock import patch, MagicMock
import pytest
from friday.chain import ChainExecutor


@pytest.fixture
def high_score_memories():
    return [{"content": "Python is great", "relevance_score": 0.8}]


@pytest.fixture
def low_score_memories():
    return [{"content": "random stuff", "relevance_score": 0.2}]


@pytest.fixture
def empty_memories():
    return []


def test_chain_returns_required_keys():
    result = ChainExecutor.run("test", "system")
    assert "system_prompt" in result
    assert "context" in result
    assert "source" in result


def test_chain_source_is_memory_when_score_sufficient(high_score_memories):
    with patch("friday.chain.recall") as mock_recall:
        mock_recall.return_value = high_score_memories
        result = ChainExecutor.run("test", "system")
        assert result["source"] == "memory"


def test_chain_source_is_web_when_score_insufficient(low_score_memories):
    with patch("friday.chain.recall") as mock_recall, \
         patch("friday.chain.search_web") as mock_search:
        mock_recall.return_value = low_score_memories
        mock_search.return_value = []
        result = ChainExecutor.run("test", "system")
        assert result["source"] == "web+memory"


def test_chain_does_not_call_search_when_memory_sufficient(high_score_memories):
    with patch("friday.chain.recall") as mock_recall, \
         patch("friday.chain.search_web") as mock_search:
        mock_recall.return_value = high_score_memories
        ChainExecutor.run("test", "system")
        mock_search.assert_not_called()


def test_chain_calls_search_when_memory_insufficient(low_score_memories):
    with patch("friday.chain.recall") as mock_recall, \
         patch("friday.chain.search_web") as mock_search:
        mock_recall.return_value = low_score_memories
        mock_search.return_value = []
        ChainExecutor.run("test", "system")
        mock_search.assert_called_once()


def test_chain_never_raises():
    with patch("friday.chain.recall") as mock_recall:
        mock_recall.side_effect = Exception("db error")
        result = ChainExecutor.run("test", "system")
        assert isinstance(result, dict)


def test_chain_source_is_web_when_memory_empty(empty_memories):
    with patch("friday.chain.recall") as mock_recall, \
         patch("friday.chain.search_web") as mock_search:
        mock_recall.return_value = empty_memories
        mock_search.return_value = []
        result = ChainExecutor.run("test", "system")
        assert result["source"] == "web+memory"


def test_chain_reminder_trigger_detected():
    fake_result = {
        "status": "set", "memory_id": "x", "event_id": "y",
        "title": "test", "datetime": "2026-04-20T15:00:00"
    }
    with patch("friday.tools.calendar.set_reminder", return_value=fake_result):
        result = ChainExecutor.run("remind me to call Pepper on Friday at 5pm", "system")
    assert result["source"] == "reminder_set"


def test_chain_non_reminder_uses_normal_chain():
    result = ChainExecutor.run("what is the weather today", "system")
    assert result["source"] != "reminder_set"


def test_chain_reminder_failure_falls_through():
    with patch("friday.tools.calendar.set_reminder", side_effect=Exception("fail")):
        result = ChainExecutor.run("remind me to do something tomorrow", "system")
    assert isinstance(result, dict)