# SETUP.md — F.R.I.D.A.Y. Local Setup Guide

Everything you need to get F.R.I.D.A.Y. running locally from scratch.

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| pip | latest |
| Git | any |

> **Windows users**: All commands use `venv\Scripts\activate`. On macOS/Linux use `source venv/bin/activate` instead.

---

## Step 1 — Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/FRIDAY.git
cd FRIDAY
```

---

## Step 2 — Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

**macOS / Linux**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

---

## Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `chromadb` — vector store
- `sentence-transformers` — local embeddings
- `mcp` — FastMCP tool server
- `pytest` + `pytest-asyncio` — test framework

> **First run note**: `sentence-transformers` will download the `all-MiniLM-L6-v2` model (~90MB) on first use. This is a one-time download cached locally.

---

## Step 4 — Run the tests

### Unit tests only (fast, ~30s)
```bash
pytest tests/test_memory.py -v
```
Expected: **14 passed**

### End-to-end tests (slower, ~2 min — loads embedding model)
```bash
pytest tests/test_memory_e2e.py -v
```
Expected: **4 passed**

### Full suite
```bash
pytest tests/ -v
```
Expected: **18 passed**

---

## Step 5 — Verify memory persistence

After running the tests, confirm ChromaDB wrote to disk:

```bash
# Windows
dir friday\memory\chroma_store

# macOS / Linux
ls -lh friday/memory/chroma_store
```

You should see a `chroma.sqlite3` file and one or more UUID-named folders. This confirms persistence is working.

---

## Project Layout After Setup

```
F.R.I.D.A.Y/
├── friday/
│   ├── agent.py                  # Voice turn handler
│   ├── tools/
│   │   └── memory.py             # remember / recall / forget tools
│   └── memory/
│       └── chroma_store/         # Created on first run (gitignored)
│           ├── chroma.sqlite3
│           └── <uuid>/
├── tests/
│   ├── test_memory.py
│   └── test_memory_e2e.py
├── requirements.txt
├── CLAUDE.md
├── SETUP.md
└── README.md
```

---

## Adding a New Tool

All MCP tools live in `friday/tools/`. To add a new one:

1. Create or edit a file in `friday/tools/`
2. Register the tool with `@mcp.tool()`
3. Write tests in `tests/` before implementing
4. Follow the RED → GREEN → REFACTOR cycle (see `CLAUDE.md`)

Example skeleton:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("friday-your-tool-name")

@mcp.tool()
def your_tool(input: str) -> dict:
    """What this tool does."""
    return {"status": "ok", "result": input}
```

---

## Common Issues

**`ModuleNotFoundError: No module named 'friday'`**

You're running pytest from outside the project root, or the venv isn't activated.

```bash
cd C:\Archit\Projects\F.R.I.D.A.Y
venv\Scripts\activate
pytest tests/ -v
```

---

**`PermissionError` on Windows during test teardown**

ChromaDB holds a file lock on `chroma.sqlite3` while the process is alive. Teardown warnings about this are harmless — all tests still pass. This is a known Windows/ChromaDB interaction.

---

**Embedding model download hangs or fails**

You may be behind a proxy or firewall. The model is fetched from HuggingFace on first use. Either whitelist `huggingface.co` or manually download `all-MiniLM-L6-v2` and set:

```python
SentenceTransformer("path/to/local/model")
```

---

**`pytest: no tests ran`**

Make sure you're in the project root and the venv is active. Also check that `pytest-asyncio` is installed:

```bash
pip show pytest-asyncio
```

---

## Environment Variables (optional)

None are required for local development. When integrating with the full LiveKit + Gemini pipeline, you will need:

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Google Gemini 2.5 Flash |
| `LIVEKIT_API_KEY` | LiveKit server auth |
| `LIVEKIT_API_SECRET` | LiveKit server auth |
| `LIVEKIT_URL` | LiveKit server URL |

Store these in a `.env` file (never commit it) and load with `python-dotenv`.
