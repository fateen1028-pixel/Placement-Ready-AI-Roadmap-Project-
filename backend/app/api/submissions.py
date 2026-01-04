from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.api.deps import (
    get_current_user,
    get_task_submission_repo,
    get_user_roadmap_repo,
    get_db,
)
from app.db.base import get_client
from app.core.exceptions import ConcurrencyError

from app.schemas.task_submission import TaskSubmissionCreate, TaskSubmission
from app.db.task_submission_repo import TaskSubmissionRepo
from app.db.user_roadmap_repo import UserRoadmapRepo
from app.db.learning_state_repo import (
    get_user_learning_state,
    apply_skill_vector_updates,
)

from app.domain.submission_guard import validate_submission_allowed
from app.domain.task_template_loader import get_task_template

from app.services.evaluation_service import evaluate_submission_and_update_roadmap


router = APIRouter(
    prefix="/submissions",
    tags=["submissions"],
)


@router.post("", response_model=TaskSubmission)
async def submit_task(
    payload: TaskSubmissionCreate,
    user=Depends(get_current_user),
    submission_repo: TaskSubmissionRepo = Depends(get_task_submission_repo),
    roadmap_repo: UserRoadmapRepo = Depends(get_user_roadmap_repo),
    db=Depends(get_db),
):
    user_id = str(user["_id"])

    # 1. Load active roadmap
    roadmap = await roadmap_repo.get_user_roadmap(user_id)
    if not roadmap:
        raise HTTPException(404, "Active roadmap not found")

    # 2. Slot must exist
    try:
        slot = roadmap.get_slot(payload.slot_id)
    except ValueError:
        raise HTTPException(404, "Slot not found")

    # 3. Slot must be in progress
    if slot.status != "in_progress":
        raise HTTPException(
            400,
            f"Slot not in progress (current state: {slot.status})",
        )

    # 4. Task instance must match active slot task
    if slot.active_task_instance_id != payload.task_instance_id:
        raise HTTPException(
            409,
            "Task instance does not match active slot task",
        )

    # 5. Roadmap must not be locked
    if roadmap.locked_reason:
        raise HTTPException(
            423,
            f"Roadmap locked: {roadmap.locked_reason}",
        )

    # 6. Domain-level submission guard
    validate_submission_allowed(slot, payload)

    # 7. Prevent duplicate submission
    existing = await submission_repo.get_submission(
        user_id=user_id,
        slot_id=payload.slot_id,
        task_instance_id=payload.task_instance_id,
    )
    if existing:
        raise HTTPException(409, "Duplicate submission for this task")

    # 8. (Refactored) Prepare virtual submission for evaluation
    # We do NOT persist yet to ensure transactional integrity.
    virtual_submission = TaskSubmission(
        id="temp_id",  # Placeholder, not used in logic
        user_id=user_id,
        slot_id=payload.slot_id,
        task_instance_id=payload.task_instance_id,
        payload=payload.payload,
        status="submitted",
        created_at=datetime.now(timezone.utc),
        evaluated_at=None,
    )

    # 9. Load task instance (EXPLICIT, NO MAGIC)
    task_instance = next(
        (
            ti
            for ti in roadmap.task_instances
            if ti.task_instance_id == payload.task_instance_id
        ),
        None,
    )
    if not task_instance:
        raise HTTPException(
            500,
            "TaskInstance not found in roadmap (corrupt roadmap state)",
        )

    # 🔒 Ensure this is the active task instance
    if task_instance.task_instance_id != slot.active_task_instance_id:
        raise HTTPException(
            409,
            "TaskInstance is not the active instance for this slot",
        )

    # 10. Load task template
    task_template = get_task_template(task_instance.task_template_id)

    # 10.5 Load Learning State
    learning_state = await get_user_learning_state(db, user_id)

    # Capture original version for optimistic locking
    original_roadmap_version = roadmap.version

    # 11. Evaluate + mutate roadmap
    evaluation = await evaluate_submission_and_update_roadmap(
        submission=virtual_submission,
        roadmap=roadmap,
        learning_state=learning_state,
        task_instance=task_instance,
        task_template=task_template,
    )

    # 🔒 HARD invariant check
    from app.domain.roadmap_validator import validate_roadmap_state, RoadmapValidationError

    try:
        validate_roadmap_state(roadmap)
    except RoadmapValidationError as e:
        raise HTTPException(
            500,
            f"Roadmap invariant violated after evaluation: {e}",
        )

    # 12. Persist evaluation (TRANSACTIONAL)
    client = get_client()
    try:
        async with await client.start_session() as session:
            async with session.start_transaction():
                # A. Create Submission (Atomic with updates)
                submission_data = {
                    "user_id": user_id,
                    "slot_id": payload.slot_id,
                    "task_instance_id": payload.task_instance_id,
                    "payload": payload.payload,
                    "status": "evaluated",
                    "created_at": datetime.now(timezone.utc),
                    "evaluated_at": datetime.now(timezone.utc),
                    "evaluation": evaluation.model_dump(),
                }
                
                submission = await submission_repo.create_submission(
                    submission_data,
                    session=session
                )

                # B. Update Roadmap (with Optimistic Locking)
                await roadmap_repo.update_roadmap(
                    roadmap,
                    expected_version=original_roadmap_version,
                    session=session
                )

                # C. Update Learning State
                await apply_skill_vector_updates(
                    db,
                    user_id,
                    learning_state.skill_vector,
                    session=session
                )
    except ConcurrencyError:
        raise HTTPException(
            409,
            "Roadmap was modified by another request. Please retry."
        )
    except Exception as e:
        # If anything else fails, the transaction aborts automatically.
        # We should probably log this.
        raise HTTPException(
            500,
            f"Transaction failed: {str(e)}"
        )

    return submission
