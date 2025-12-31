from typing import Any


def normalize_llm_content(content: Any) -> str:
    """
    Normalize Gemini / LangChain output into a clean JSON string.
    Handles:
    - str
    - list[str]
    - list[dict]
    - markdown code fences
    """
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
        text = "".join(parts)
    else:
        raise TypeError(f"Unsupported LLM content type: {type(content)}")

    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]

    return text.strip()