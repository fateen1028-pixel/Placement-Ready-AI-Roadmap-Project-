# app/domain/task_template_loader.py

from app.domain.task_templates import TASK_TEMPLATES
from app.schemas.task_template import TaskTemplate


def get_task_template(task_template_id: str) -> TaskTemplate:
    try:
        return TASK_TEMPLATES[task_template_id]
    except KeyError:
        raise RuntimeError(
            f"TaskTemplate not found: {task_template_id}"
        )
