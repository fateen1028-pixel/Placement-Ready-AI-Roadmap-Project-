from datetime import datetime, timezone

from app.schemas.ai_evaluation import AIEvaluationResult
from app.schemas.task_instance import TaskInstance, TaskStatus
from app.schemas.task_submission import TaskSubmission
from app.schemas.roadmap_state import RoadmapState
from app.schemas.learning_state import UserLearningState

from app.ai.evaluations import evaluate_task
from app.domain.remediation_planner import build_remediation_plan
from app.domain.remediation_applier import apply_remediation_plan
from app.domain.remediation_unlocker import unlock_dependent_slots_after_remediation
from app.domain.roadmap_validator import (
    validate_roadmap_state,
    RoadmapValidationError,
)
from app.domain.skill_vector_updater import apply_skill_vector_update
from app.domain.remediation_constants import MAX_REMEDIATION_ATTEMPTS


ACTIONABLE_SLOT_STATUSES = {
    "available",
    "in_progress",
    "remediation_required",
}


async def evaluate_submission_and_update_roadmap(
    *,
    submission: TaskSubmission,
    roadmap: RoadmapState,
    learning_state: UserLearningState,
    task_instance: TaskInstance,
    task_template,
) -> AIEvaluationResult:
    """
    Single source of truth for:
    - Evaluation
    - TaskInstance mutation
    - Slot mutation
    - Phase transitions
    - Skill vector updates

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
    task_instance.status = (
        TaskStatus.COMPLETED if evaluation.passed else TaskStatus.FAILED
    )
    task_instance.completed_at = now

    # ================================
    # 3. Mutate Slot
    # ================================
    slot = roadmap.get_slot(task_instance.slot_id)
    was_remediation = slot.status == "remediation_required"

    if evaluation.passed:
        slot.status = "completed"
    else:
        slot.status = "remediation_required"
        slot.remediation_attempts += 1

    slot.active_task_instance_id = None

    # ================================
    # Hard remediation cap
    # ================================
    if slot.remediation_attempts > MAX_REMEDIATION_ATTEMPTS:
        slot.status = "failed"

        active_phase = next(
            p for p in roadmap.phases
            if any(s.slot_id == slot.slot_id for s in p.slots)
        )

        active_phase.phase_status = "locked"
        active_phase.locked_reason = "remediation_attempts_exceeded"

        roadmap.status = "locked"
        roadmap.locked_reason = "too_many_remediation_failures"

        return evaluation

    # ================================
    # Apply remediation plan on failure
    # ================================
    if not evaluation.passed:
        plan = build_remediation_plan(
            roadmap=roadmap,
            failed_task=task_instance,
        )
        apply_remediation_plan(
            roadmap=roadmap,
            plan=plan,
        )

    # ================================
    # A7: Unlock dependent slots
    # ================================
    if evaluation.passed and was_remediation:
        unlock_dependent_slots_after_remediation(
            roadmap=roadmap,
            remediated_slot_id=slot.slot_id,
        )

    # ================================
    # 4. Update roadmap metadata
    # ================================
    roadmap.last_evaluated_at = now

    # ================================
    # 5. Phase transition logic
    # ================================
    _resolve_active_phase(roadmap)

    # ================================
    # A9: HARD INVARIANT VALIDATION
    # ================================
    try:
        validate_roadmap_state(roadmap)
    except RoadmapValidationError as e:
        raise RuntimeError(
            f"Roadmap invariant violated after evaluation cycle: {e}"
        )

    # ================================
    # A10: Skill vector update
    # ================================
    apply_skill_vector_update(
        learning_state=learning_state,
        evaluation=evaluation,
        task_instance=task_instance,
        task_template=task_template,
    )

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

