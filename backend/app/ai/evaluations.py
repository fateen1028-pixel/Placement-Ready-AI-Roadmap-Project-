# app/ai/evaluations.py

from app.schemas.ai_evaluation import AIEvaluationResult
from app.schemas.task_instance import TaskInstance
from app.schemas.task_template import TaskTemplate
from app.domain.task_context import TaskContext

from app.ai.evaluate_mcq import evaluate_mcq
from app.ai.evaluate_coding import evaluate_coding
from app.ai.evaluate_explanation import evaluate_explanation


def evaluate_task(
    *,
    task_instance: TaskInstance,
    task_template: TaskTemplate,
    submission_payload: dict,
) -> AIEvaluationResult:
    """
    Unified evaluation dispatcher.
    """

    # Hard invariant — DB corruption if violated
    if task_instance.task_template_id != task_template.task_template_id:
        raise RuntimeError("TaskInstance does not match TaskTemplate")

    context = TaskContext(
        task_instance_id=task_instance.task_instance_id,
        skill=task_template.skill,
        difficulty=task_instance.difficulty,
    )

    if task_template.question_type == "mcq":
        if task_template.correct_option is None:
            raise RuntimeError(
                f"MCQ task {task_template.task_template_id} missing correct_option"
            )

        return evaluate_mcq(
            selected_option=submission_payload["selected_option"],
            correct_option=task_template.correct_option,
            skill=task_template.skill,
        )

    if task_template.question_type == "coding":
        return evaluate_coding(
            code=submission_payload["code"],
            language=submission_payload["language"],
            context=context,
        )

    if task_template.question_type == "explanation":
        return evaluate_explanation(
            text=submission_payload["text"],
            context=context,
        )

    raise RuntimeError(f"Unknown task type: {task_template.question_type}")
