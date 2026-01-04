# from app.ai.gemini_client import get_gemini_llm
from app.ai.groq_client import get_groq_llm


async def run_evaluation_prompt(
    *,
    code: str,
    language: str,
    problem: str,
    constraints: str | None = None
) -> dict:
    # model = get_gemini_llm()
    model = get_groq_llm()

    prompt = f"""
You are an automated coding evaluator.

Problem:
{problem}

Language: {language}

Constraints:
{constraints or "None"}

User Code:
{code}

Return STRICT JSON in this format ONLY:
{{
  "passed": boolean,
  "score": number (0 to 1),
  "feedback": string,
  "detected_concepts": string[],
  "mistakes": string[]
}}
"""

    response = await model.invoke(prompt)

    # IMPORTANT: return RAW model output
    # return response.text
    return response.content
