from datetime import datetime, timezone

from app.schemas.ai_evaluation import AIEvaluationResult
from app.schemas.roadmap_state import RoadmapState, TaskSlot


def apply_submission_consequences(
    roadmap: RoadmapState,
    slot: TaskSlot,
    evaluation: AIEvaluationResult
) -> RoadmapState:
    """
    Apply consequences of an evaluation to the roadmap.

    Rules:
    - Pass + score >= threshold -> complete slot, unlock next
    - Pass + score < threshold  -> reinforcement required
    - Fail                      -> lock phase and roadmap
    """

    now = datetime.now(timezone.utc)

    # ---------- CASE 1: PASS + STRONG SCORE ----------
    if evaluation.passed and evaluation.score >= roadmap.confidence_threshold:
        slot.status = "completed"
        slot.active_task_instance_id = None

        for phase in roadmap.phases:
            for idx, s in enumerate(phase.slots):
                if s.slot_id == slot.slot_id:
                    if idx + 1 < len(phase.slots):
                        next_slot = phase.slots[idx + 1]
                        if next_slot.status == "locked":
                            next_slot.status = "available"
                    else:
                        phase.phase_status = "completed"

        # Check if roadmap completed
        if all(p.phase_status == "completed" for p in roadmap.phases):
            roadmap.status = "completed"
            roadmap.is_active = False

        roadmap.last_evaluated_at = now
        return roadmap

    # ---------- CASE 2: PASS + WEAK SCORE ----------
    if evaluation.passed and evaluation.score < roadmap.confidence_threshold:
        slot.status = "in_progress"
        slot.active_task_instance_id = f"{slot.slot_id}_reinforcement"

        roadmap.last_evaluated_at = now
        return roadmap

    # ---------- CASE 3: FAIL ----------
    if not evaluation.passed:
        slot.status = "failed"

        for phase in roadmap.phases:
            for s in phase.slots:
                if s.slot_id == slot.slot_id:
                    phase.phase_status = "locked"
                    phase.locked_reason = "Remediation required due to failed task"

        roadmap.status = "locked"
        roadmap.locked_reason = "User failed a required task"
        roadmap.last_evaluated_at = now
        return roadmap

    return roadmap
