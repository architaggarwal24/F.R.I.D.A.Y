"""End-to-end tests for ChainExecutor using real ChromaDB and DuckDuckGo."""

import gc
import os
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from friday.tools.memory import (
    CHROMA_PERSIST_PATH,
    _get_collection,
    _get_embedding_model,
)
from friday.chain import ChainExecutor


@pytest.fixture(autouse=True)
def clean_chroma_for_chain_tests():
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


@pytest.fixture(autouse=False)
def seeded_memory():
    """Seed 'Boss prefers dark mode on all interfaces' into ChromaDB."""
    collection = _get_collection()
    embed = _get_embedding_model()

    content = "Boss prefers dark mode on all interfaces"
    e = embed.encode([content])
    mid = str(uuid4())
    ts = datetime.now(timezone.utc).isoformat()
    collection.add(
        ids=[mid],
        embeddings=e.tolist(),
        documents=[content],
        metadatas=[{"category": "preference", "timestamp": ts, "source": "explicit"}],
    )

    yield mid


@pytest.fixture(autouse=False)
def cold_store():
    """Start with an empty (wiped) ChromaDB store — no memories."""
    yield


def test_chain_e2e_memory_sufficient(seeded_memory):
    """Scenario A: high-relevance memory is available — source is 'memory'."""
    result = ChainExecutor.run(
        "what are my interface preferences",
        "You are F.R.I.D.A.Y.",
    )

    assert result["source"] == "memory"
    assert "dark mode" in result["context"]
    assert "You are F.R.I.D.A.Y." in result["system_prompt"]


def test_chain_e2e_web_search_triggered(cold_store):
    """Scenario B: no memory — web search is triggered, source is 'web+memory'."""
    result = ChainExecutor.run(
        "latest news about SpaceX",
        "You are F.R.I.D.A.Y.",
    )

    assert result["source"] == "web+memory"
    assert "Web search results:" in result["context"]
    assert isinstance(result["system_prompt"], str)
    assert len(result["system_prompt"]) > 0