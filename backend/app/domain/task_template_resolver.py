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
    # Find all templates that claim to be derived from this base ID
    candidates = [
        t for t in TASK_TEMPLATES.values()
        if t.base_template_id == base_template_id
    ]

    if not candidates:
        raise RuntimeError(
            f"Task template not found: {base_template_id}"
        )

    # Determine if we need a remediation template
    is_remediation = (slot.status == "remediation_required")

    # Filter candidates
    matching_templates = []
    for t in candidates:
        is_rem_template = t.task_template_id.endswith("__remediation")
        if is_remediation == is_rem_template:
            matching_templates.append(t)

    if not matching_templates:
        type_str = "Remediation" if is_remediation else "Standard"
        raise RuntimeError(
            f"{type_str} template not found for: {base_template_id}"
        )

    # Sort by ID to get the latest version (e.g. v2 > v1)
    # This assumes standard naming conventions
    best_match = sorted(matching_templates, key=lambda x: x.task_template_id)[-1]

    return best_match.task_template_id





