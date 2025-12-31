"""
SKILL DELTA RULES:

1. If evaluation.passed == False → skill decreases
2. If score < 0.6 → no positive gain (even if passed)
3. Easy tasks give small gains
4. Medium tasks give moderate gains
5. Hard tasks give controlled gains (not huge)
6. Very high score (>= 0.9) gives a bonus
7. Skill deltas are deterministic (NO randomness)
"""
from typing import Literal
from app.schemas.ai_evaluation import AIEvaluationResult





print("LOADED skill_delta.py VERSION WITH question_type")

FAIL_PENALTY = -0.05
MIN_PASS_SCORE = 0.6

BASE_DELTA = {
    "easy": 0.10,
    "medium": 0.15,
    "hard": 0.20,
}

HIGH_SCORE_BONUS = 0.05

QUESTION_TYPE_MULTIPLIER = {
    "mcq": 0.5,
    "coding": 1.0,
    "explanation": 0.7,
}


def compute_skill_deltas(
    evaluation: AIEvaluationResult,
    difficulty: str,
    skill: str,
    question_type: Literal["mcq", "coding", "explanation"],
) -> dict[str, float]:

    # 1. Fail → penalty
    if not evaluation.passed:
        return {skill: FAIL_PENALTY}

    # 2. Weak pass → no gain
    if evaluation.score < MIN_PASS_SCORE:
        return {skill: 0.0}

    # 3. Base delta from difficulty
    base = BASE_DELTA.get(difficulty)
    if base is None:
        raise ValueError(f"Unknown difficulty: {difficulty}")

    delta = base

    # 4. High score bonus
    if evaluation.score >= 0.9:
        delta += HIGH_SCORE_BONUS

    # 5. Trust adjustment
    multiplier = QUESTION_TYPE_MULTIPLIER.get(question_type)
    if multiplier is None:
        raise ValueError(f"Unknown question_type: {question_type}")

    delta = round(delta * multiplier, 3)

    return {skill: delta}
