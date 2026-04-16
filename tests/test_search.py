import pytest
from friday.tools.search import search_web


def test_search_returns_list():
    result = search_web("Python programming")
    assert isinstance(result, list)


def test_search_result_has_required_keys():
    results = search_web("Python programming")
    for r in results:
        assert "title" in r
        assert "url" in r
        assert "snippet" in r


def test_search_respects_max_results():
    result = search_web("AI news", max_results=2)
    assert len(result) <= 2


def test_search_empty_query_returns_empty_list():
    result = search_web("")
    assert result == []


def test_search_never_raises():
    result = search_web("!@#$%^&*()")
    assert isinstance(result, list)