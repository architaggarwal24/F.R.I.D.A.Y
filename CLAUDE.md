# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

F.R.I.D.A.Y is a voice-first AI assistant built on a LiveKit pipeline with a FastMCP backend.
Reasoning: Google Gemini 2.5 Flash. TTS: nova voice.

- **chromadb** - Persistent vector store for semantic memory
- **sentence-transformers** - Local text embeddings (all-MiniLM-L6-v2)
- **FastMCP** - Tool registration via @mcp.tool() decorator
- **pytest + pytest-asyncio** - All tests async-aware

## Project Structure

```
friday/
├── tools/             ← All MCP tools live here (@mcp.tool())
│   └── memory.py      ← Memory system (remember, recall, forget)
├── memory/
│   └── chroma_store/  ← ChromaDB persistent storage (do not delete)
└── agent.py           ← Main voice turn handler + prompt assembly

tests/
├── test_memory.py       ← Unit tests for memory tools
└── test_memory_e2e.py   ← End-to-end session simulation
```

## Commands

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Run all tests
pytest

# Run async tests only
pytest -m asyncio

# Run with verbose output
pytest -v
```

## Memory System — Key Rules

- ChromaDB client and embedding model are **singletons** — lazy-loaded, never re-initialized
- CHROMA_PERSIST_PATH = "friday/memory/chroma_store" — never hardcode another path
- SIMILARITY_THRESHOLD = 0.97 — dedup cutoff
- Minimum relevance score for recall = 0.3 — anything below is noise, filter it out
- All 3 memory tools must be registered with @mcp.tool()

## Testing Rules

- **Always write tests before implementation** — RED phase must be confirmed before GREEN
- Use pytest fixtures to seed ChromaDB with test data — never depend on production store
- Clear or use a separate test collection in fixtures to avoid state bleed between tests
- Async tests must use @pytest.mark.asyncio

## Coding Conventions

- All MCP tools return plain dicts or list[dict] — no custom objects
- Use uuid4() for memory IDs
- Timestamps: datetime.utcnow().isoformat()
- Source field values: "voice" | "inferred" | "explicit" — no other values