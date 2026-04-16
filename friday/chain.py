from friday.tools.memory import recall
from friday.tools.search import search_web

MEMORY_SUFFICIENCY_THRESHOLD = 0.4


class ChainExecutor:
    @staticmethod
    def run(utterance: str, base_system_prompt: str) -> dict:
        try:
            memories = recall(utterance, limit=3)
        except Exception:
            memories = []

        top_score = memories[0]["relevance_score"] if memories else 0.0

        if top_score >= MEMORY_SUFFICIENCY_THRESHOLD:
            memory_context = "Relevant memory context:\n- " + "\n- ".join(
                m["content"] for m in memories
            )
            context = memory_context
            source = "memory"
        else:
            try:
                results = search_web(utterance)
            except Exception:
                results = []

            parts = []

            if results:
                parts.append(
                    "Web search results:\n"
                    + "\n".join(f"- {r['title']}: {r['snippet']}" for r in results)
                )

            if memories:
                parts.append(
                    "Relevant memory context:\n- "
                    + "\n- ".join(m["content"] for m in memories)
                )

            context = "\n\n".join(parts) if parts else ""
            source = "web+memory"

        system_prompt = (context + "\n\n" + base_system_prompt) if context else base_system_prompt
        return {
            "system_prompt": system_prompt,
            "context": context,
            "source": source,
        }