"""Voice turn handler — assembles prompt/context and calls the LLM."""

import json
from friday.tools.memory import recall


def build_system_prompt(base_system_prompt: str, user_utterance: str) -> str:
    """Build the system prompt, auto-injecting relevant memory context.

    Args:
        base_system_prompt: The base system prompt string.
        user_utterance: The user's voice utterance for this turn.

    Returns:
        The (possibly augmented) system prompt with memory context prepended.
    """
    try:
        memories = recall(user_utterance, limit=3)
    except Exception:
        # Silently continue if recall fails — never surface to user
        memories = []

    if not memories:
        return base_system_prompt

    # Prepend relevant memory context block
    memory_block = "Relevant memory context:\n- " + "\n- ".join(
        m["content"] for m in memories
    )
    return memory_block + "\n\n" + base_system_prompt


def voice_turn(
    user_utterance: str,
    base_system_prompt: str,
    call_llm_fn=None,
) -> dict:
    """Process a single voice turn.

    Args:
        user_utterance: The raw user utterance.
        base_system_prompt: The base system prompt for this assistant.
        call_llm_fn: Optional callable that takes (system_prompt, user_utterance)
                     and returns an LLM response dict. If None, returns the
                     built prompt for testing purposes.

    Returns:
        A dict with at least "system_prompt" key; optionally "response" from LLM.
    """
    system_prompt = build_system_prompt(base_system_prompt, user_utterance)

    if call_llm_fn is None:
        # No-op for testing — return what the system prompt would be
        return {"system_prompt": system_prompt}

    response = call_llm_fn(system_prompt, user_utterance)
    return {"system_prompt": system_prompt, "response": response}
