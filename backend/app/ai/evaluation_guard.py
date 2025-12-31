from app.schemas.ai_evaluation import AIEvaluationResult


def enforce_evaluation_rules(result: AIEvaluationResult) -> AIEvaluationResult:
    # Clamp score
    score = max(0.0, min(1.0, result.score))

    passed = result.passed

    # Invariant 1: pass implies minimum score
    if passed and score < 0.6:
        score = 0.6

    # Invariant 2: fail implies maximum score
    if not passed and score > 0.5:
        score = 0.5

    # Invariant 3: no mistakes => must pass
    if not result.mistakes and not passed:
        passed = True
        score = max(score, 0.6)

    return AIEvaluationResult(
        passed=passed,
        score=score,
        feedback=result.feedback,
        detected_concepts=result.detected_concepts,
        mistakes=result.mistakes,
    )
    