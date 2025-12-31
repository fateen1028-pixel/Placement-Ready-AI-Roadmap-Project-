# app/domain/task_templates.py

from app.schemas.task_template import TaskTemplate


TASK_TEMPLATES: dict[str, TaskTemplate] = {
    "arrays_easy_v1": TaskTemplate(
        task_template_id="arrays_easy_v1",
        slot_id="arrays_easy",
        question_type="coding",
        skill="arrays",
        difficulty="easy",
        prompt="Write a function to return the sum of an array.",
        language="python",
        starter_code="def solve(arr):\n    pass",
    ),
}
