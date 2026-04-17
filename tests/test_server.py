import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset memory singletons for each test."""
    import friday.tools.memory as memory_module
    from uuid import uuid4
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
def client(reset_singletons):
    # Import app HERE (after singletons reset) so TestClient sees fresh module state
    from friday.dashboard.server import app
    return TestClient(app)


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "F.R.I.D.A.Y" in response.text


def test_search_endpoint(client):
    response = client.get("/search?q=dark+mode")
    assert response.status_code == 200


def test_memory_detail_not_found(client):
    response = client.get("/memory/fake-id-999")
    assert response.status_code == 404 or "not found" in response.text.lower()


def test_stats_endpoint(client):
    response = client.get("/stats")
    assert response.status_code == 200
    assert "total" in response.text.lower()


def test_export_endpoint(client):
    response = client.get("/export")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
