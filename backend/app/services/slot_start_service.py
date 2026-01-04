from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.task_instance import TaskInstance, TaskStatus
from app.schemas.roadmap_state import RoadmapState
from app.schemas.task_template import TaskTemplate


def start_slot(
    *,
    roadmap: RoadmapState,
    slot_id: str,
    task_template: TaskTemplate,
) -> TaskInstance:
    # 1️⃣ Fetch slot
    slot = roadmap.get_slot(slot_id)

    if slot.status not in ["available", "remediation_required"]:
        raise RuntimeError(f"Slot {slot_id} not available (status: {slot.status})")

    # 2️⃣ Handle Remediation Retry (Increment Attempts)
    if slot.status == "remediation_required":
        slot.remediation_attempts += 1

    # 3️⃣ Defensive validation
    if task_template.skill != slot.skill:
        raise RuntimeError(
            f"TaskTemplate skill {task_template.skill} "
            f"does not match slot skill {slot.skill}"
        )

    if task_template.difficulty != slot.difficulty:
        raise RuntimeError(
            f"TaskTemplate difficulty {task_template.difficulty} "
            f"does not match slot difficulty {slot.difficulty}"
        )

    now = datetime.now(timezone.utc)

    # 3️⃣ Create TaskInstance (FULLY VALID)
    task_instance = TaskInstance(
        task_instance_id=str(uuid4()),
        base_template_id=task_template.base_template_id,
        task_template_id=task_template.task_template_id,
        skill=task_template.skill,
        difficulty=task_template.difficulty,
        slot_id=slot_id,
        status=TaskStatus.IN_PROGRESS,
        started_at=now,
    )

    # 4️⃣ Mutate roadmap state
    roadmap.task_instances.append(task_instance)

    slot.status = "in_progress"
    slot.active_task_instance_id = task_instance.task_instance_id

    roadmap.last_evaluated_at = now

    return task_instance
