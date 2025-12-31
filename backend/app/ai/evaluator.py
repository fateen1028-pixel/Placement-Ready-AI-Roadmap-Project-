from langchain_core.messages import HumanMessage
from app.ai.gemini_client import get_gemini_llm
from app.schemas.ai_evaluation import AIEvaluationResult
from app.ai.evaluation_guard import enforce_evaluation_rules
from app.ai.utils import normalize_llm_content
import json


def evaluate_submission():
    llm = get_gemini_llm()

    prompt = """
Return ONLY valid JSON matching this schema:

{
  "passed": true,
  "score": 0.0,
  "feedback": "",
  "detected_concepts": [],
  "mistakes": []
}

Task:
Print numbers from 1 to 5

User code:
print(1)
print(2)
print(3)
print(4)
print(5)
"""

    # response = llm.invoke([HumanMessage(content=prompt)])
    class FakeResponse:
        content = """{
            "passed": true,
            "score": 0.1,
            "feedback": "Looks fine",
            "detected_concepts": [],
            "mistakes": []
        }"""

    response = FakeResponse()

    raw_text = normalize_llm_content(response.content)

    def extract_json(raw_text: str) -> str:
      raw_text = raw_text.strip()

      # Remove markdown code fences if present
      if raw_text.startswith("```"):
          raw_text = raw_text.strip("`")
          raw_text = raw_text.replace("json", "", 1).strip()

      # Remove leading 'json' token if present
      if raw_text.lower().startswith("json"):
          raw_text = raw_text[4:].strip()

      return raw_text
    clean_text = extract_json(raw_text)
    try:
        data = json.loads(clean_text)

        raw_result = AIEvaluationResult(**data)
        print("RAW RESULT:", raw_result)

        final_result = enforce_evaluation_rules(raw_result)
        print("FINAL RESULT:", final_result)

        return final_result

    except Exception as e:
        raise RuntimeError(
            f"AI returned invalid JSON.\nRaw output:\n{raw_text}"
        ) from e
