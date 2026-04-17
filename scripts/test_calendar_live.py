#!/usr/bin/env python
"""F.R.I.D.A.Y. Calendar Live Test — standalone script."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from friday.tools.calendar import set_reminder, get_reminders, cancel_reminder
from friday.tools.memory import recall


def main():
    print("=== F.R.I.D.A.Y. Calendar Live Test ===\n")

    # Step 1 — Set a reminder
    print("Step 1 — Set a reminder:")
    result = set_reminder("F.R.I.D.A.Y. test reminder", "tomorrow at 3pm")
    print(f"  set_reminder result: {result}")
    assert result["status"] in ("set", "set_memory_only"), f"Unexpected status: {result['status']}"
    assert result.get("memory_id") is not None, "memory_id is missing"
    if result.get("event_id"):
        print(f"  [OK] Google Calendar event created: {result['event_id']}")
    else:
        print("  [WARN] Calendar write failed — memory still stored")
    print()

    # Step 2 — Get reminders
    print("Step 2 — Get reminders:")
    reminders = get_reminders(limit=5)
    print(f"  get_reminders returned: {len(reminders)} results")
    for r in reminders:
        print(f"    - {r['content']} [{r['category']}] @ {r['timestamp']}")
    print()

    # Step 3 — Cancel the reminder
    print("Step 3 — Cancel the reminder:")
    cancel = cancel_reminder(
        result["memory_id"],
        event_id=result.get("event_id")
    )
    print(f"  cancel_reminder result: {cancel}")
    assert cancel["status"] == "cancelled", f"Expected 'cancelled', got '{cancel['status']}'"
    print()

    # Step 4 — Verify it's gone
    print("Step 4 — Verify memory removed:")
    check = recall("F.R.I.D.A.Y. test reminder", limit=3)
    gone = not any("F.R.I.D.A.Y. test reminder" in m.get("content", "") for m in check)
    print(f"  Memory removed after cancel: {gone}")
    assert gone, "Memory should have been deleted"
    print()

    print("=== ALL STEPS COMPLETE ===")


if __name__ == "__main__":
    main()
