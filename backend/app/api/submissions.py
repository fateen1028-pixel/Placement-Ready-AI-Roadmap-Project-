from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.api.deps import (
    get_current_user,
    get_task_submission_repo,
    get_user_roadmap_repo,
    get_db,
)

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

    # 8. Create submission
    submission = await submission_repo.create_submission(
        {
            "user_id": user_id,
            "slot_id": payload.slot_id,
            "task_instance_id": payload.task_instance_id,
            "payload": payload.payload,
            "status": "submitted",
            "created_at": datetime.now(timezone.utc),
            "evaluated_at": None,
        }
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

    # 11. Evaluate + mutate roadmap
    evaluation = await evaluate_submission_and_update_roadmap(
        submission=submission,
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

    # 12. Persist evaluation
    await submission_repo.attach_evaluation(
        submission.id,
        evaluation,
    )

    # 13. Persist roadmap
    await roadmap_repo.update_roadmap(roadmap)

    # 14. Persist Learning State
    await apply_skill_vector_updates(db, user_id, learning_state.skill_vector)

    return submission
