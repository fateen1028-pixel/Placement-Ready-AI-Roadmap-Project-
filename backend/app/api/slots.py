from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.db.user_roadmap_repo import UserRoadmapRepo
from app.api.deps import get_current_user, get_user_roadmap_repo
from app.schemas.roadmap_state import TaskSlot
from app.domain.roadmap_validator import validate_roadmap_state, RoadmapValidationError
from app.domain.task_template_resolver import resolve_task_template_id
from app.services.slot_start_service import start_slot as start_slot_domain


router = APIRouter()


@router.post("/slots/{slot_id}/start")
async def start_slot(
    slot_id: str,
    user=Depends(get_current_user),
    repo: UserRoadmapRepo = Depends(get_user_roadmap_repo),
):
    roadmap = await repo.get_user_roadmap(str(user["_id"]))
    if not roadmap:
        raise HTTPException(404, "Active roadmap not found")

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
        raise HTTPException(500, "No active phase found")

    if slot.status == "locked":
        raise HTTPException(400, "Slot is locked")
    if slot.status in {"completed", "failed"}:
        raise HTTPException(400, "Slot already finished")
    if slot.active_task_instance_id is not None:
        raise HTTPException(409, "Slot already in progress")
    if slot.status not in {"available", "remediation_required"}:
        raise HTTPException(400, "Slot not startable")

    for phase in roadmap.phases:
        for s in phase.slots:
            if s.active_task_instance_id is not None:
                raise HTTPException(409, "Another slot is already active")

    # 🔧 FIX: remediation-aware template resolution
    failed_task_template_id = None

    if slot.status == "remediation_required":
        failed_task = next(
            (
                ti
                for ti in roadmap.task_instances
                if ti.slot_id == slot.slot_id and ti.status == "failed"
            ),
            None,
        )

        if not failed_task:
            raise HTTPException(
                500,
                "Remediation slot has no failed task (corrupt roadmap state)"
            )

        base_template_id: str = failed_task.task_template_id
    else:
        base_template_id: str = f"{slot.slot_id}_v1"

    task_template_id = resolve_task_template_id(
        slot=slot,
        base_template_id=base_template_id,
)


    task_instance = start_slot_domain(
        roadmap=roadmap,
        slot_id=slot.slot_id,
        task_template_id=task_template_id,
    )

    roadmap.last_evaluated_at = datetime.now(timezone.utc)
    roadmap.version += 1

    try:
        validate_roadmap_state(roadmap)
    except RoadmapValidationError as e:
        raise HTTPException(
            500,
            f"Roadmap invariant violated after slot start: {e}"
        )

    await repo.update_roadmap(roadmap)

    return {
        "slot_id": slot.slot_id,
        "task_instance_id": task_instance.task_instance_id,
        "task_template_id": task_instance.task_template_id,
        "difficulty": slot.difficulty,
        "started_at": task_instance.started_at.isoformat(),
    }

