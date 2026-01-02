# app/domain/task_templates.py

from app.schemas.task_template import TaskTemplate


TASK_TEMPLATES: dict[str, TaskTemplate] = {
    # ─────────────────────────────
    # Primary task
    # ─────────────────────────────
    "arrays_easy_v1": TaskTemplate(
        task_template_id="arrays_easy_v1",
        base_template_id="arrays_easy",
        slot_id="arrays_easy",
        question_type="coding",
        skill="arrays",
        difficulty="easy",
        prompt="Write a function to return the sum of an array.",
        language="python",
        starter_code="def solve(arr):\n    pass",
    ),

    # ─────────────────────────────
    # Remediation task (same slot)
    # ─────────────────────────────
    "arrays_easy_v1__remediation": TaskTemplate(
    task_template_id="arrays_easy_v1__remediation",
    base_template_id="arrays_easy",   # 🔑 REQUIRED
    slot_id="arrays_easy",
    question_type="coding",
    skill="arrays",
    difficulty="easy",
    prompt=(
        "You previously failed this task.\n"
        "Reattempt by carefully handling edge cases.\n\n"
        "Write a function that returns the sum of an array."
    ),
    language="python",
    starter_code="def solve(arr):\n    pass",
),

}
