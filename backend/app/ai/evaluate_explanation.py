from app.schemas.ai_evaluation import AIEvaluationResult
from app.domain.task_context import TaskContext
from app.ai.gemini_client import get_gemini_llm
from app.ai.utils import normalize_llm_content
from langchain_core.messages import HumanMessage
import json


def evaluate_explanation(
    *,
    text: str,
    context: TaskContext,
) -> AIEvaluationResult:
    """
    AI evaluation for explanation tasks.
    """

    llm = get_gemini_llm()

    prompt = f"""
Evaluate the explanation below.

Skill: {context.skill}
Difficulty: {context.difficulty}

Rules:
- Return ONLY valid JSON
- No markdown
- No commentary

JSON schema:
{{
  "passed": true,
  "score": 0.0,
  "feedback": "",
  "detected_concepts": [],
  "mistakes": []
}}

User explanation:
{text}
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    raw = normalize_llm_content(response.content)

    try:
        data = json.loads(raw)
        return AIEvaluationResult(**data)
    except Exception as e:
        raise RuntimeError(
            f"Invalid JSON from explanation evaluator.\nRaw:\n{raw}"
        ) from e
