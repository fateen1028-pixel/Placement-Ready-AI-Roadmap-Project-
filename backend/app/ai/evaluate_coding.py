from app.schemas.ai_evaluation import AIEvaluationResult
from app.domain.task_context import TaskContext
from app.ai.gemini_client import get_gemini_llm
from app.ai.utils import normalize_llm_content
from langchain_core.messages import HumanMessage
import json


def evaluate_coding(
    *,
    code: str,
    language: str,
    context: TaskContext,
) -> AIEvaluationResult:
    """
    AI evaluation for coding tasks.
    Context is mandatory.
    """

    llm = get_gemini_llm()

    prompt = f"""
You are evaluating a coding task.

Skill: {context.skill}
Difficulty: {context.difficulty}

Rules:
- Return ONLY valid JSON
- No markdown
- No explanations

JSON schema:
{{
  "passed": true,
  "score": 0.0,
  "feedback": "",
  "detected_concepts": [],
  "mistakes": []
}}

User code ({language}):
{code}
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    raw = normalize_llm_content(response.content)

    try:
        data = json.loads(raw)
        return AIEvaluationResult(**data)
    except Exception as e:
        raise RuntimeError(
            f"Invalid JSON from coding evaluator.\nRaw:\n{raw}"
        ) from e
