import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

import friday.tools.memory as memory_module
from friday.tools.memory import remember, recall


@pytest.fixture(autouse=True)
def dashboard_e2e_setup():
    """UUID collection override for test isolation."""
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


@pytest.fixture
def seeded_memories():
    """Seed test memories for e2e scenarios."""
    m1 = remember("Boss prefers dark mode", category="preference", source="voice")
    m2 = remember("Review AutoClip on Sunday", category="reminder", source="voice")
    m3 = remember("ChromaDB is the vector store", category="fact", source="voice")
    return {"preference": m1, "reminder": m2, "fact": m3}


@pytest.fixture
def client(seeded_memories):
    """TestClient with fresh app import after seeding."""
    from friday.dashboard.server import app
    return TestClient(app)


def test_dashboard_index_shows_all_categories(client, seeded_memories):
    """GET / shows all 3 categories in response."""
    response = client.get("/")
    assert response.status_code == 200
    assert "preference" in response.text.lower()
    assert "reminder" in response.text.lower()
    assert "fact" in response.text.lower()


def test_dashboard_search_returns_match(client, seeded_memories):
    """GET /search?q=dark+mode returns matching result."""
    response = client.get("/search?q=dark+mode")
    assert response.status_code == 200
    assert "dark mode" in response.text.lower()


def test_dashboard_memory_detail(client, seeded_memories):
    """GET /memory/<id> shows memory content."""
    memory_id = seeded_memories["fact"]["memory_id"]
    response = client.get(f"/memory/{memory_id}")
    assert response.status_code == 200
    assert "ChromaDB" in response.text


def test_dashboard_edit_memory(client, seeded_memories):
    """POST /memory/<id>/edit updates content."""
    memory_id = seeded_memories["fact"]["memory_id"]
    new_content = "ChromaDB is the persistent vector store"
    response = client.post(f"/memory/{memory_id}/edit", data={"content": new_content})
    assert response.status_code == 200
    result = recall("persistent vector store")
    assert any(new_content in r.get("content", "") for r in result)


def test_dashboard_delete_memory(client, seeded_memories):
    """POST /memory/<id>/delete removes memory."""
    memory_id = seeded_memories["reminder"]["memory_id"]
    response = client.post(f"/memory/{memory_id}/delete")
    assert response.status_code == 200
    result = recall("Review AutoClip")
    assert len(result) == 0


def test_dashboard_export_returns_json(client, seeded_memories):
    """GET /export returns valid JSON list with all memories."""
    response = client.get("/export")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_dashboard_stats_shows_total(client, seeded_memories):
    """GET /stats shows total count."""
    response = client.get("/stats")
    assert response.status_code == 200
    assert "total" in response.text.lower()
