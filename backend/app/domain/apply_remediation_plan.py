# app/domain/apply_remediation_plan.py

from app.schemas.roadmap_state import RoadmapState
from app.schemas.task_instance import TaskInstance
from app.domain.remediation_plan import RemediationPlan


def apply_remediation_plan(
    *,
    roadmap: RoadmapState,
    failed_task: TaskInstance,
    plan: RemediationPlan,
) -> None:
    """
    Apply remediation effects to roadmap state.
    NO task instances are created here.
    """

    failed_slot = roadmap.get_slot(failed_task.slot_id)

    # 1️⃣ Mark failed slot as remediation-required
    failed_slot.status = "remediation_required"
    failed_slot.locked_reason = "remediation_required"
    failed_slot.active_task_instance_id = None

    # 2️⃣ Lock dependent slots in same phase
    phase = next(
        p for p in roadmap.phases
        if any(s.slot_id == failed_slot.slot_id for s in p.slots)
    )

    for slot in phase.slots:
        if slot.slot_id != failed_slot.slot_id:
            slot.status = "locked"
            slot.locked_reason = "dependency_failed"

    # 3️⃣ Version bump only
    roadmap.version += 1
