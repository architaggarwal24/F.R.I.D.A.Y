"""Voice turn handler — assembles prompt/context and calls the LLM."""

from friday.chain import ChainExecutor


def build_system_prompt(base_system_prompt: str, user_utterance: str) -> str:
    """Build the system prompt using ChainExecutor (backward-compatible)."""
    result = ChainExecutor.run(user_utterance, base_system_prompt)
    return result["system_prompt"]


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
    result = ChainExecutor.run(user_utterance, base_system_prompt)

    if call_llm_fn is None:
        return {"system_prompt": result["system_prompt"], "source": result["source"]}

    response = call_llm_fn(result["system_prompt"], user_utterance)
    return {"system_prompt": result["system_prompt"], "source": result["source"], "response": response}