from pydantic import BaseModel
from typing import List


class AIEvaluationResult(BaseModel):
    passed: bool
    score: float
    feedback: str
    detected_concepts: List[str]
    mistakes: List[str]
