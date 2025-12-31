from app.schemas.ai_evaluation import AIEvaluationResult

def evaluate_mcq(
    *,
    selected_option: str,
    correct_option: str,
    skill: str
) -> AIEvaluationResult:
    correct = selected_option == correct_option

    return AIEvaluationResult(
        passed=correct,
        score=1.0 if correct else 0.0,
        feedback="Correct" if correct else "Incorrect",
        detected_concepts=[skill],
        mistakes=[] if correct else ["Wrong answer"],
    )
