def build_structured_output(
    text: str,
    intent: str,
    source: str,
    session_id: str,
    extra: dict = None,
    structured: dict = None
):
    structured_data = {
        "intent": intent,
        "source": source,
        "session_id": session_id,
        **(extra or {})
    }

    if structured:
        structured_data["structured"] = structured

    return {
        "text": text,
        "structured_output": structured_data
    }
