from friday.tools.memory import recall
from friday.tools.search import search_web

MEMORY_SUFFICIENCY_THRESHOLD = 0.4

REMINDER_TRIGGERS = [
    "remind me", "don't let me forget", "remember to",
    "schedule", "put on my calendar", "set a reminder",
    "add to my calendar"
]


class ChainExecutor:
    @staticmethod
    def run(utterance: str, base_system_prompt: str) -> dict:
        if any(trigger in utterance.lower() for trigger in REMINDER_TRIGGERS):
            try:
                from friday.tools.calendar import set_reminder, parse_datetime
                dt_result = parse_datetime(utterance)
                dt_str = dt_result.get("datetime", "") if dt_result.get("status") == "ok" else ""
                if dt_str:
                    reminder_result = set_reminder(utterance, dt_str)
                else:
                    reminder_result = {"status": "error", "reason": "no datetime found"}
                if reminder_result.get("status") in ("set", "set_memory_only"):
                    context = f"Reminder set: {utterance}"
                else:
                    context = f"Could not set reminder: {reminder_result.get('reason')}"
                return {
                    "system_prompt": context + "\n\n" + base_system_prompt,
                    "context": context,
                    "source": "reminder_set"
                }
            except Exception:
                pass

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