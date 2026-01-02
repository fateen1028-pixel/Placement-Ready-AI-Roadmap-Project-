# app/domain/remediation_planner.py

from app.domain.remediation_plan import RemediationPlan, RemediationAction
from app.schemas.roadmap_state import RoadmapState
from app.schemas.task_instance import TaskInstance


def build_remediation_plan(
    *,
    roadmap: RoadmapState,
    failed_task: TaskInstance,
) -> RemediationPlan:
    """
    Deterministic remediation rules (V1):
    - Failed slot requires remediation task
    - Lock all later slots in the SAME phase
    """

    failed_slot_id = failed_task.slot_id

    actions: list[RemediationAction] = []

    # 1️⃣ Always inject remediation task for the failed slot
    actions.append(
        RemediationAction(
            slot_id=failed_slot_id,
            action="inject_remediation_task",
        )
    )

    # 2️⃣ Lock dependent slots in the same phase
    phase = next(
        p for p in roadmap.phases
        if any(s.slot_id == failed_slot_id for s in p.slots)
    )

    for slot in phase.slots:
        if slot.slot_id != failed_slot_id:
            actions.append(
                RemediationAction(
                    slot_id=slot.slot_id,
                    action="lock_dependent_slots",
                )
            )

    return RemediationPlan(
        failed_task_instance_id=failed_task.task_instance_id,
        actions=actions,
    )
