import numpy as np
import chromadb
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from datetime import datetime, timezone
from uuid import uuid4
from mcp.server.fastmcp import FastMCP

from dataclasses import dataclass
from enum import Enum

_chroma_client = None
_embedding_model = None
_collection_name_override: str | None = None


def _get_client() -> PersistentClient:
    """Initialize ChromaDB PersistentClient (singleton)."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
    return _chroma_client


def _get_collection():
    """Get or create the memory collection (singleton)."""
    client = _get_client()
    name = _collection_name_override if _collection_name_override else COLLECTION_NAME
    return client.get_or_create_collection(name=name)


def _get_embedding_model():
    """Lazily load the sentence-transformers model (singleton)."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


class MemoryCategory(Enum):
    preference = "preference"
    task = "task"
    reminder = "reminder"
    fact = "fact"


@dataclass
class MemoryEntry:
    memory_id: str
    content: str
    category: MemoryCategory
    timestamp: str  # ISO 8601
    source: str  # one of: "voice", "inferred", "explicit"


COLLECTION_NAME = "friday_memory"
SIMILARITY_THRESHOLD = 0.97
TOP_K_DEFAULT = 5
CHROMA_PERSIST_PATH = "friday/memory/chroma_store"


mcp = FastMCP("friday-memory")


@mcp.tool()
def remember(content: str, category: str = "fact", source: str = "explicit") -> dict:
    """Store a new memory entry after checking for duplicates."""
    if not content or not content.strip():
        return {"status": "error", "reason": "empty content"}

    collection = _get_collection()
    embed_model = _get_embedding_model()
    embedding = embed_model.encode([content])

    # Query for duplicates — compute cosine similarity directly
    results = collection.query(
        query_embeddings=embedding.tolist(),
        include=["documents", "embeddings"],
        n_results=1,
    )
    if results["documents"] and results["documents"][0]:
        stored_vec = np.array(results["embeddings"][0][0])
        query_vec = embedding[0]
        q_norm = query_vec / np.linalg.norm(query_vec)
        s_norm = stored_vec / np.linalg.norm(stored_vec)
        similarity = float(np.dot(q_norm, s_norm))
        if similarity >= SIMILARITY_THRESHOLD:
            return {"status": "duplicate", "memory_id": results["ids"][0][0]}

    memory_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    collection.add(
        ids=[memory_id],
        embeddings=embedding.tolist(),
        documents=[content],
        metadatas=[{"category": category, "timestamp": timestamp, "source": source}],
    )

    return {"memory_id": memory_id, "status": "stored", "category": category}


@mcp.tool()
def recall(query: str, limit: int = TOP_K_DEFAULT) -> list[dict]:
    """Search memory for relevant entries."""
    if not query or not query.strip():
        return []

    collection = _get_collection()
    embed_model = _get_embedding_model()
    embedding = embed_model.encode([query])

    results = collection.query(
        query_embeddings=embedding.tolist(),
        include=["documents", "metadatas", "embeddings"],
        n_results=limit,
    )

    memories = []
    if results["documents"] and results["documents"][0]:
        query_vec = embedding[0]
        q_norm = query_vec / np.linalg.norm(query_vec)
        for i, doc in enumerate(results["documents"][0]):
            stored_vec = np.array(results["embeddings"][0][i])
            s_norm = stored_vec / np.linalg.norm(stored_vec)
            relevance_score = float(np.dot(q_norm, s_norm))
            if relevance_score < 0.3:
                continue
            metadata = results["metadatas"][0][i]
            memories.append({
                "content": doc,
                "category": metadata.get("category"),
                "timestamp": metadata.get("timestamp"),
                "relevance_score": relevance_score,
            })

    memories.sort(key=lambda x: x["relevance_score"], reverse=True)
    return memories


@mcp.tool()
def forget(memory_id: str) -> dict:
    """Delete a memory entry by its ID."""
    if not memory_id or not memory_id.strip():
        return {"status": "error", "reason": "invalid memory_id"}

    collection = _get_collection()
    # Check if the memory exists before attempting to delete
    existing = collection.get(ids=[memory_id])
    if not existing["ids"]:
        return {"status": "not_found", "memory_id": memory_id}

    collection.delete(ids=[memory_id])
    return {"status": "deleted", "memory_id": memory_id}
