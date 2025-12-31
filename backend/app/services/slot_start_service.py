from datetime import datetime, timezone

from app.schemas.task_instance import TaskInstance
from app.schemas.roadmap_state import RoadmapState


def start_slot(
    *,
    roadmap: RoadmapState,
    slot_id: str,
    task_template_id: str,
) -> TaskInstance:
    slot = roadmap.get_slot(slot_id)

    if slot.status != "available":
        raise RuntimeError(f"Slot {slot_id} not available")

    now = datetime.now(timezone.utc)

    task_instance = TaskInstance(
        task_template_id = "arrays_easy_v1",
        slot_id=slot_id,
        difficulty=slot.difficulty,
        started_at=now,
    )

    # 🔑 MUTATIONS
    roadmap.task_instances.append(task_instance)
    slot.status = "in_progress"
    slot.active_task_instance_id = task_instance.task_instance_id
    roadmap.last_evaluated_at = now

    return task_instance
