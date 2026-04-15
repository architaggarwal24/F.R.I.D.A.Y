# F.R.I.D.A.Y.
### Fully Responsive Intelligent Digital Assistant for You

> *"I've dated holograms with more substance than this, but sure, let's give it a shot."*

F.R.I.D.A.Y. is a voice-first AI assistant built on a **LiveKit pipeline** with a **FastMCP backend**. She reasons via Google Gemini 2.5 Flash, speaks via the `nova` TTS voice, and now — she **remembers**.

---

## What's in this repo

This repository contains the **Memory System** — the first major capability module beyond the base demo.

| Module | Description |
|--------|-------------|
| `friday/tools/memory.py` | Three MCP tools: `remember`, `recall`, `forget` |
| `friday/agent.py` | Voice turn handler with silent auto-recall injection |
| `tests/test_memory.py` | 14 unit tests covering all memory tools |
| `tests/test_memory_e2e.py` | End-to-end 4-turn session simulation |

---

## How the Memory System Works

On every voice turn, F.R.I.D.A.Y. silently calls `recall()` with the user's utterance and injects relevant memories into the system prompt — before the LLM ever sees the input. Boss never has to say *"remember what I told you."*

```
Boss says something
        ↓
recall(utterance, limit=3)       ← semantic search, silent
        ↓
Relevant memories found?
  YES → prepend to system prompt
  NO  → continue unchanged
        ↓
LLM generates response with full context
```

### The three tools

```python
remember(content, category)   # stores a memory with embedding + dedup check
recall(query, limit)          # semantic search — returns most relevant memories
forget(memory_id)             # deletes a memory by ID
```

### Storage

- **Backend**: ChromaDB (local, persistent, embedded — no external server)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (local, free, fast)
- **Deduplication**: Cosine similarity threshold at 0.97 — near-identical memories are rejected
- **Noise floor**: Recall filters results below 0.3 relevance score
- **Persistence**: Survives process restarts — memories live on disk at `friday/memory/chroma_store/`

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Voice pipeline | LiveKit |
| Tool server | FastMCP |
| LLM | Google Gemini 2.5 Flash |
| TTS | nova voice |
| Vector store | ChromaDB (persistent) |
| Embeddings | sentence-transformers / all-MiniLM-L6-v2 |
| Tests | pytest + pytest-asyncio |

---

## Project Structure

```
F.R.I.D.A.Y/
├── friday/
│   ├── agent.py                  # Voice turn handler + auto-recall hook
│   ├── tools/
│   │   └── memory.py             # remember / recall / forget MCP tools
│   └── memory/
│       └── chroma_store/         # Runtime only — created on first run, gitignored
├── tests/
│   ├── test_memory.py            # Unit tests
│   └── test_memory_e2e.py        # End-to-end session tests
├── requirements.txt
├── CLAUDE.md                     # Claude Code guidance
├── SETUP.md                      # Setup & run instructions
└── README.md
```

---

## Test Results

```
18 passed in ~105s
```

```
tests/test_memory.py         14 passed   ← unit tests
tests/test_memory_e2e.py      4 passed   ← e2e session simulation
```

---

## Roadmap

- [ ] `get_calendar` + `set_reminder` — act on reminders, not just store them
- [ ] Chained tool reasoning — `recall` → `search_web` in one autonomous turn
- [ ] Voice persona tuning — tighter response formatting for `nova` TTS
- [ ] Memory dashboard — view, edit, and delete what F.R.I.D.A.Y. knows

---

## License

MIT
