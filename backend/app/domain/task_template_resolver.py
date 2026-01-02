from app.domain.task_templates import TASK_TEMPLATES
from app.schemas.roadmap_state import TaskSlot


def resolve_task_template_id(
    *,
    slot: TaskSlot,
    base_template_id: str,
) -> str:
    """
    Single source of truth for task template selection.
    """

    if slot.status == "remediation_required":
        remediation_id = f"{base_template_id}__remediation"

        if remediation_id not in TASK_TEMPLATES:
            raise RuntimeError(
                f"Remediation template not found: {remediation_id}"
            )

        return remediation_id

    if base_template_id not in TASK_TEMPLATES:
        raise RuntimeError(
            f"Task template not found: {base_template_id}"
        )

    return base_template_id





