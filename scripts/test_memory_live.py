#!/usr/bin/env python
"""F.R.I.D.A.Y. Memory System Live Test — standalone script."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from friday.tools.memory import remember, recall, forget
from friday.dashboard.memory_ops import stats


def main():
    print("=== F.R.I.D.A.Y. Memory System Live Test ===\n")

    # Step 1 — Store 4 memories
    print("Step 1 — Storing 4 memories:")
    r1 = remember("I prefer dark mode on all interfaces", "preference")
    print(f"  [preference] {r1}")
    r2 = remember("Always respond concisely", "preference")
    print(f"  [preference] {r2}")
    r3 = remember("Review AutoClip workflow on Sunday", "reminder")
    print(f"  [reminder] {r3}")
    r4 = remember("F.R.I.D.A.Y. uses ChromaDB for storage", "fact")
    print(f"  [fact] {r4}")
    print("Stored 4 memories\n")

    # Step 2 — Recall by meaning
    print("Step 2 — Recall preferences:")
    results = recall("what are my preferences", limit=5)
    for r in results:
        print(f"  [{r['relevance_score']:.2f}] {r['content']}")
    print()

    # Step 3 — Recall reminders
    print("Step 3 — Recall reminders:")
    results = recall("what do I need to do", limit=5)
    for r in results:
        print(f"  [{r['relevance_score']:.2f}] {r['content']}")
    print()

    # Step 4 — Store and forget
    print("Step 4 — Store and forget:")
    temp = remember("temporary test memory", "fact")
    print(f"  Stored: {temp}")
    deleted = forget(temp["memory_id"])
    print(f"  Deleted: {deleted}")
    check = recall("temporary test memory", limit=3)
    print(f"  After forget, recall returned: {check}")
    assert len(check) == 0 or "temporary test memory" not in [r["content"] for r in check], "FAIL: memory not deleted"
    print("  Assertion passed: memory was deleted\n")

    # Step 5 — Final stats
    print("Step 5 — Final stats:")
    s = stats()
    print(f"  Total memories: {s['total']}")
    print(f"  By category: {s['by_category']}")
    print(f"  Store size: {s['store_size_bytes']:,} bytes")
    print()

    print("=== ALL STEPS COMPLETE ===")


if __name__ == "__main__":
    main()
