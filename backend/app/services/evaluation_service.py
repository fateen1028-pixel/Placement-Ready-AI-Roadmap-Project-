from datetime import datetime, timezone

from app.schemas.ai_evaluation import AIEvaluationResult
from app.schemas.task_instance import TaskInstance, TaskStatus
from app.schemas.task_submission import TaskSubmission
from app.schemas.roadmap_state import RoadmapState
from app.ai.evaluations import evaluate_task


ACTIONABLE_SLOT_STATUSES = {
    "available",
    "in_progress",
    "remediation_required",
}


async def evaluate_submission_and_update_roadmap(
    *,
    submission: TaskSubmission,
    roadmap: RoadmapState,
    task_instance: TaskInstance,
    task_template,
) -> AIEvaluationResult:
    """
    Single source of truth for:
    - Evaluation
    - TaskInstance mutation
    - Slot mutation
    - Phase transitions

    Must always leave roadmap in a VALID state.
    """

    # ================================
    # 1. Run evaluation
    # ================================
    evaluation = evaluate_task(
        task_instance=task_instance,
        task_template=task_template,
        submission_payload=submission.payload,
    )

    now = datetime.now(timezone.utc)

    # ================================
    # 2. Mutate TaskInstance
    # ================================
    if evaluation.passed:
        task_instance.status = TaskStatus.COMPLETED
    else:
        task_instance.status = TaskStatus.FAILED

    task_instance.completed_at = now

    # ================================
    # 3. Mutate Slot
    # ================================
    slot = roadmap.get_slot(task_instance.slot_id)

    if evaluation.passed:
        slot.status = "completed"
    else:
        # V1: failures still count as terminal
        slot.status = "failed"

    slot.active_task_instance_id = None

    # ================================
    # 4. Update roadmap metadata
    # ================================
    roadmap.last_evaluated_at = now

    # ================================
    # 5. Phase transition logic (CORRECT)
    # ================================
    _resolve_active_phase(roadmap)

    return evaluation


def _resolve_active_phase(roadmap: RoadmapState) -> None:
    """
    Ensures roadmap invariants:
    - Active phase must have actionable slots
    - Empty phases are auto-completed
    """

    while True:
        active_phase = next(
            (p for p in roadmap.phases if p.phase_status == "active"),
            None,
        )

        if not active_phase:
            return

        has_actionable = any(
            slot.status in ACTIONABLE_SLOT_STATUSES
            for slot in active_phase.slots
        )

        if has_actionable:
            return

        # No actionable slots → complete this phase
        active_phase.phase_status = "completed"

        # Find next locked phase
        next_phase = next(
            (p for p in roadmap.phases if p.phase_status == "locked"),
            None,
        )

        if not next_phase:
            roadmap.status = "completed"
            roadmap.is_active = False
            return

        # Unlock it
        next_phase.phase_status = "active"
        next_phase.locked_reason = None
        roadmap.current_phase = next_phase.phase_id

        # Unlock its slots
        for slot in next_phase.slots:
            if slot.status == "locked":
                slot.status = "available"

        # Loop again in case THIS phase is also empty

