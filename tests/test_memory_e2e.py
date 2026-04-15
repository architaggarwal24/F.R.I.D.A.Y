"""End-to-end session simulation tests for the memory system."""

import os
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from friday.tools.memory import (
    CHROMA_PERSIST_PATH,
    remember,
)
from friday.agent import build_system_prompt, voice_turn


def _wipe_store():
    """Wipe the ChromaDB persist store, handling Windows file locks."""
    import gc
    import shutil
    import time
    import friday.tools.memory as memory_module

    store_path = CHROMA_PERSIST_PATH
    if not os.path.exists(store_path):
        return

    # Close the ChromaDB client before deleting files
    if memory_module._chroma_client is not None:
        try:
            memory_module._chroma_client = None
        except Exception:
            pass

    time.sleep(0.1)
    gc.collect()

    import stat

    def onerror(func, path, exc_info):
        # On Windows, try to make the file writable before retrying
        try:
            os.chmod(path, stat.S_IWUSR | stat.S_IRUSR)
            os.unlink(path)
        except OSError:
            pass

    try:
        shutil.rmtree(store_path, onerror=onerror)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def clean_chroma_client():
    """Reset the module-level singletons and wipe the persist store before each test."""
    import gc
    import friday.tools.memory as memory_module

    memory_module._chroma_client = None
    memory_module._embedding_model = None
    gc.collect()

    _wipe_store()

    yield

    memory_module._chroma_client = None
    memory_module._embedding_model = None
    gc.collect()

    _wipe_store()


@pytest.fixture
def seed_memory():
    """Seed 'Boss prefers concise responses' into ChromaDB."""
    import friday.tools.memory as memory_module

    memory_module._chroma_client = None
    memory_module._embedding_model = None

    collection = memory_module._get_collection()
    embed = memory_module._get_embedding_model()

    content = "Boss prefers concise responses"
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


def test_auto_recall_injects_memory_into_system_prompt(seed_memory):
    """A seeded memory about response style is injected into the system prompt.

    When a voice turn is processed, recall() is called on the user utterance.
    If relevant memories exist, they are prepended to the system prompt.
    """
    result = voice_turn(
        user_utterance="how should you respond to me",
        base_system_prompt="You are F.R.I.D.A.Y, a voice AI assistant.",
    )

    assert "system_prompt" in result
    system_prompt = result["system_prompt"]

    # The memory content should appear in the system prompt
    assert "Boss prefers concise responses" in system_prompt
    # The memory block prefix should be present
    assert "Relevant memory context:" in system_prompt


def test_auto_recall_no_injection_when_no_memories():
    """When recall returns no results, the base system prompt is used unchanged."""
    result = voice_turn(
        user_utterance="tell me about quantum physics",
        base_system_prompt="You are F.R.I.D.A.Y, a voice AI assistant.",
    )

    assert "system_prompt" in result
    system_prompt = result["system_prompt"]

    # No memory context block should be prepended
    assert "Relevant memory context:" not in system_prompt
    assert system_prompt == "You are F.R.I.D.A.Y, a voice AI assistant."


def test_voice_turn_returns_both_system_prompt_and_response():
    """When call_llm_fn is provided, voice_turn returns both system_prompt and response."""
    def fake_llm(system_prompt, utterance):
        return {"text": f"Response to: {utterance}"}

    result = voice_turn(
        user_utterance="hello",
        base_system_prompt="You are F.R.I.D.A.Y.",
        call_llm_fn=fake_llm,
    )

    assert "system_prompt" in result
    assert "response" in result
    assert result["response"]["text"] == "Response to: hello"


def _store_size(path: str) -> int:
    """Return total size in bytes of all files in path (recursive)."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def test_full_voice_session_with_memory_lifecycle():
    """Simulate a full multi-turn voice session with memory persistence.

    Turn 1 — Boss: "I prefer dark mode on everything"
    Turn 2 — Boss: "Remind me to review the AutoClip workflow on Sunday"
    Turn 3 — Boss: "What are my preferences?"
    Turn 4 — Simulate process restart; verify memories survive on disk
    """
    import friday.tools.memory as memory_module
    from friday.tools.memory import recall as memory_recall

    # ── Turn 1 ──────────────────────────────────────────────────────────────
    result1 = remember("I prefer dark mode on everything", "preference")
    assert result1.get("status") == "stored", f"Turn 1 failed: {result1}"
    dark_mode_id = result1["memory_id"]
    assert isinstance(dark_mode_id, str) and len(dark_mode_id) > 0

    # ── Turn 2 ──────────────────────────────────────────────────────────────
    result2 = remember(
        "Remind me to review the AutoClip workflow on Sunday", "reminder"
    )
    assert result2.get("status") == "stored", f"Turn 2 failed: {result2}"
    assert result2.get("category") == "reminder", (
        f"Expected category 'reminder', got {result2.get('category')}"
    )
    reminder_id = result2["memory_id"]
    assert isinstance(reminder_id, str) and len(reminder_id) > 0

    # Verify Turn 2 gets its own distinct memory_id
    assert reminder_id != dark_mode_id

    # ── Turn 3 ──────────────────────────────────────────────────────────────
    preferences = memory_recall("What are my preferences?", limit=5)
    assert len(preferences) >= 1, "Turn 3: recall returned no results"

    # The dark mode memory should be present
    contents = [r["content"] for r in preferences]
    assert any("dark mode" in c for c in contents), (
        f"Turn 3: dark mode memory not in recall results: {preferences}"
    )

    # The AutoClip reminder should also be retrievable
    reminders = memory_recall("AutoClip workflow on Sunday", limit=5)
    assert len(reminders) >= 1, "Turn 3: reminder not found in recall"

    # ── Turn 4 — Simulate process restart ────────────────────────────────────
    # 1. Capture current store size for final reporting
    store_size_before = _store_size(CHROMA_PERSIST_PATH) if os.path.exists(CHROMA_PERSIST_PATH) else 0

    # 2. Clear the in-process singleton (simulates process death)
    memory_module._chroma_client = None
    memory_module._embedding_model = None

    # 3. Re-initialise from disk — next _get_client() call rebuilds from persist
    new_client = memory_module._get_client()
    assert new_client is not None

    # 4. Verify both memories survive the restart
    post_restart_prefs = memory_recall("dark mode preferences", limit=5)
    assert len(post_restart_prefs) >= 1, (
        "Turn 4: dark mode memory lost after restart"
    )
    post_restart_contents = [r["content"] for r in post_restart_prefs]
    assert any("dark mode" in c for c in post_restart_contents), (
        f"Turn 4: dark mode memory missing after restart: {post_restart_prefs}"
    )

    post_restart_reminders = memory_recall("AutoClip workflow", limit=5)
    assert len(post_restart_reminders) >= 1, (
        "Turn 4: reminder memory lost after restart"
    )

    # ── Store size after all turns ───────────────────────────────────────────
    store_size_after = _store_size(CHROMA_PERSIST_PATH)
    assert store_size_after > 0, "chroma_store is empty — persistence broken"

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n=== test_full_voice_session_with_memory_lifecycle ===")
    print(f"  Turns completed : 4/4")
    print(f"  Dark mode ID   : {dark_mode_id}")
    print(f"  Reminder ID    : {reminder_id}")
    print(f"  Recall prefs   : {len(post_restart_prefs)} result(s)")
    print(f"  Recall remind  : {len(post_restart_reminders)} result(s)")
    print(f"  Store size     : {store_size_after:,} bytes")