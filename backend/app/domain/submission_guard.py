from fastapi import HTTPException
from app.schemas.roadmap_state import TaskSlot
from app.schemas.task_submission import TaskSubmissionCreate


def validate_submission_allowed(
    slot: TaskSlot,
    payload: TaskSubmissionCreate,
) -> None:
    """
    Enforces domain invariants before allowing a submission.
    """

    # 1️⃣ Slot must be in progress
    if slot.status != "in_progress":
        raise HTTPException(
            status_code=400,
            detail=f"Slot not in progress (current state: {slot.status})"
        )

    # 2️⃣ Task instance ID must match
    if slot.active_task_instance_id != payload.task_instance_id:
        raise HTTPException(
            status_code=409,
            detail="Task instance does not match active slot task"
        )

    # 3️⃣ Defensive sanity check
    if not payload.payload:
        raise HTTPException(
            status_code=400,
            detail="Submission payload is empty"
        )
