from app.schemas.ai_evaluation import AIEvaluationResult
from app.ai.evaluate_coding import evaluate_coding
from app.ai.evaluate_explanation import evaluate_explanation
from app.ai.evaluate_mcq import evaluate_mcq
from app.domain.task_context import TaskContext

def evaluate_task(
    *,
    context: TaskContext,
    payload: dict,
) -> AIEvaluationResult:
    """
    Single authoritative evaluation router.
    """

    if context.question_type == "mcq":
        # HARD RULE: MCQs NEVER TOUCH AI
        selected = payload.get("answer")
        correct = payload.get("correct_answer")

        if selected is None or correct is None:
            raise ValueError("MCQ payload must include 'answer' and 'correct_answer'")

        passed = selected == correct

        return AIEvaluationResult(
            passed=passed,
            score=1.0 if passed else 0.0,
            feedback="Correct" if passed else "Incorrect",
            detected_concepts=[context.skill],
            mistakes=[] if passed else ["Wrong answer"],
        )

    if context.question_type == "coding":
        # AI-based evaluation
        return evaluate_coding(
            code=payload["code"],
            language=payload["language"],
            context=context,   # IMPORTANT
        )

    if context.question_type == "explanation":
        # AI-based evaluation
        return evaluate_explanation(
            text=payload["text"],
            context=context,   # IMPORTANT
        )

    raise ValueError(f"Unknown question_type: {context.question_type}")
