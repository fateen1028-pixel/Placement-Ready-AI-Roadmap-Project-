from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.db.user_roadmap_repo import UserRoadmapRepo
from app.api.deps import get_current_user, get_user_roadmap_repo
from app.schemas.roadmap_state import TaskSlot
from app.domain.roadmap_validator import validate_roadmap_state, RoadmapValidationError


router = APIRouter()


@router.post("/slots/{slot_id}/start")
async def start_slot(
    slot_id: str,
    user=Depends(get_current_user),
    repo: UserRoadmapRepo = Depends(get_user_roadmap_repo),
):
    # 1️⃣ Fetch roadmap (MODEL, not dict)
    roadmap = await repo.get_user_roadmap(str(user["_id"]))

    if not roadmap:
        raise HTTPException(404, "Active roadmap not found")

    # 2️⃣ Find slot (explicit traversal)
    slot: TaskSlot | None = None
    active_phase = None

    for phase in roadmap.phases:
        if phase.phase_status == "active":
            active_phase = phase
        for s in phase.slots:
            if s.slot_id == slot_id:
                slot = s

    if not slot:
        raise HTTPException(404, "Slot not found")

    if not active_phase:
        raise HTTPException(500, "No active phase found (corrupted roadmap)")

    # 3️⃣ Slot state guards
    if slot.status == "locked":
        raise HTTPException(400, "Slot is locked")

    if slot.status in {"completed", "failed"}:
        raise HTTPException(400, "Slot already finished")

    if slot.active_task_instance_id is not None:
        raise HTTPException(409, "Slot already in progress")

    # 4️⃣ Global constraint: only one in_progress slot
    for phase in roadmap.phases:
        for s in phase.slots:
            if s.active_task_instance_id is not None:
                raise HTTPException(409, "Another slot is already active")

    # 5️⃣ Start slot (REAL state transition)
    task_instance_id = f"task_{slot.slot_id}_{int(datetime.now(timezone.utc).timestamp())}"

    slot.status = "in_progress"
    slot.active_task_instance_id = task_instance_id
    roadmap.last_evaluated_at = datetime.now(timezone.utc)
    roadmap.version += 1

    # 🔒 STEP 1: HARD INVARIANT CHECK — NO EXCEPTIONS
    try:
        validate_roadmap_state(roadmap)
    except RoadmapValidationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Roadmap invariant violated after slot start: {e}"
        )


    # 6️⃣ Validate roadmap AFTER mutation
    validate_roadmap_state(roadmap)

    # 7️⃣ Persist via repo (NOT raw collection)
    await repo.update_roadmap(roadmap)

    # 8️⃣ Return execution contract
    return {
        "slot_id": slot.slot_id,
        "task_instance_id": task_instance_id,
        "difficulty": slot.difficulty,
        "started_at": roadmap.last_evaluated_at.isoformat()
    }
