#!/usr/bin/env python
"""F.R.I.D.A.Y. Chain Executor Live Test — standalone script."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from friday.chain import ChainExecutor


def main():
    print("=== F.R.I.D.A.Y. Chain Executor Live Test ===\n")

    system_prompt = "You are F.R.I.D.A.Y., a voice AI assistant."

    # Scenario A — Memory sufficient (uses seeded memories from test_memory_live.py)
    print("Scenario A — Memory sufficient (interface preferences):")
    result_a = ChainExecutor.run(
        "what are my interface preferences",
        system_prompt
    )
    print(f"  Source: {result_a['source']}")
    print(f"  Context: {result_a['context']}")
    assert result_a["source"] == "memory", f"Expected 'memory', got '{result_a['source']}'"
    print("  Assertion passed: source is 'memory'\n")

    # Scenario B — Web search triggered (no matching memory)
    print("Scenario B — Web search triggered (SpaceX launches):")
    result_b = ChainExecutor.run(
        "latest news about SpaceX launches",
        system_prompt
    )
    print(f"  Source: {result_b['source']}")
    print(f"  Context preview: {result_b['context'][:300]}...")
    assert result_b["source"] == "web+memory", f"Expected 'web+memory', got '{result_b['source']}'"
    print("  Assertion passed: source is 'web+memory'\n")

    # Scenario C — Reminder intent
    print("Scenario C — Reminder intent (AutoClip analytics):")
    result_c = ChainExecutor.run(
        "remind me to check the AutoClip analytics tomorrow at 10am",
        system_prompt
    )
    print(f"  Source: {result_c['source']}")
    print(f"  Context: {result_c['context']}")
    assert result_c["source"] == "reminder_set", f"Expected 'reminder_set', got '{result_c['source']}'"
    print("  Assertion passed: source is 'reminder_set'\n")

    print("=== ALL SCENARIOS COMPLETE ===")


if __name__ == "__main__":
    main()
