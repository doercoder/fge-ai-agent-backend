def build_structured_output(text: str, intent: str, source: str, session_id: str, extra: dict = None):
    return {
        "text": text,
        "structured_output": {
            "intent": intent,
            "source": source,
            "session_id": session_id,
            **(extra or {})
        }
    }
