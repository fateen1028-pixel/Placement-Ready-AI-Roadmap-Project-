from datetime import datetime, timezone
from typing import Optional
from app.schemas.roadmap_state import RoadmapState
from app.schemas.task_instance import TaskInstance, TaskStatus
from app.schemas.task_template import TaskTemplate
from app.domain.task_template_resolver import resolve_task_template_id
from app.domain.task_template_loader import get_task_template
from app.domain.adaptive_control import DecisionContext
from app.domain.task_context import modulate_task_parameters

def start_slot(
    *,
    roadmap: RoadmapState,
    slot_id: str,
    task_template: Optional[TaskTemplate] = None,
    context: Optional[DecisionContext] = None,
) -> TaskInstance:
    # 1️⃣ Fetch slot
    slot = roadmap.get_slot(slot_id)
    
    if slot.status not in ["available", "remediation_required", "reinforcement_required"]:
        raise ValueError(f"Slot {slot_id} is not available (status: {slot.status})")

    # 2️⃣ Determine Task Template (if not provided)
    if not task_template:
        template_id = resolve_task_template_id(
            slot=slot,
            context=context,
            track_id="dsa"
        )
        task_template = get_task_template(template_id)

    # 3️⃣ Elastic Parameter Shaping (V3)
    parameters = {}
    if context:
        parameters = modulate_task_parameters(context, task_template)

    # 4️⃣ Create Task Instance
    task_instance = TaskInstance(
        skill=task_template.skill,
        slot_id=slot_id,
        base_template_id=task_template.base_template_id or task_template.task_template_id,
        task_template_id=task_template.task_template_id,
        difficulty=task_template.difficulty,
        type=task_template.question_type,
        status=TaskStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc),
        parameters=parameters
    )
    
    # 5️⃣ Update Slot
    slot.status = "in_progress"
    slot.question_type = task_template.question_type
    slot.active_task_instance_id = task_instance.task_instance_id
    roadmap.task_instances.append(task_instance)
    
    return task_instance
