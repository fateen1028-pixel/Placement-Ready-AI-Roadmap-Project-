from datetime import datetime

from app.schemas.roadmap_state import RoadmapState
from app.schemas.task_instance import TaskInstance, TaskStatus
from app.domain.remediation_plan import RemediationPlan


def apply_remediation_plan(
    *,
    roadmap: RoadmapState,
    failed_task_instance: TaskInstance,
    plan: RemediationPlan,
) -> None:
    """
    Applies remediation actions to the roadmap.
    MUST leave roadmap in a valid state.
    """

    # Guard 1: plan-task consistency
    if plan.failed_task_instance_id != failed_task_instance.task_instance_id:
        raise RuntimeError("RemediationPlan does not match failed TaskInstance")

    # Guard 2: task must be FAILED
    if failed_task_instance.status != TaskStatus.FAILED:
        raise RuntimeError("Remediation can only be applied to FAILED tasks")

    # Apply actions
    for action in plan.actions:
        if action.action == "inject_remediation_task":
            _inject_remediation_task(
                roadmap=roadmap,
                failed_task_instance=failed_task_instance,
                slot_id=action.slot_id,
            )

        elif action.action == "lock_dependent_slots":
            _lock_dependent_slots(
                roadmap=roadmap,
                slot_id=action.slot_id,
            )

        else:
            raise RuntimeError(f"Unknown remediation action: {action.action}")

    # Final invariant check
    roadmap.validate_state()


def _inject_remediation_task(
    *,
    roadmap: RoadmapState,
    failed_task_instance: TaskInstance,
    slot_id: str,
) -> None:
    slot = roadmap.get_slot(slot_id)

    if slot.status != "failed":
        raise RuntimeError(
            f"Cannot inject remediation into slot {slot_id} with status {slot.status}"
        )

    now = datetime.utcnow()

    remediation_task = TaskInstance(
        task_instance_id=f"remediation_{slot_id}_{int(now.timestamp())}",
        task_template_id=failed_task_instance.task_template_id,
        slot_id=slot_id,
        difficulty=failed_task_instance.difficulty,
        status=TaskStatus.IN_PROGRESS,
        started_at=now,
    )

    roadmap.task_instances.append(remediation_task)

    slot.status = "remediation_required"
    slot.active_task_instance_id = remediation_task.task_instance_id


def _lock_dependent_slots(
    *,
    roadmap: RoadmapState,
    slot_id: str,
) -> None:
    found = False

    for phase in roadmap.phases:
        for slot in phase.slots:
            if slot.slot_id == slot_id:
                found = True
                continue

            if not found:
                continue

            if slot.status == "completed":
                continue

            slot.status = "locked"
            slot.locked_reason = "dependency_failed"

    if not found:
        raise RuntimeError(f"Slot {slot_id} not found for dependency locking")
