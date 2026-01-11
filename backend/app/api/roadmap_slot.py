from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.api.deps import get_current_user, get_user_roadmap_repo, get_db
from app.db.user_roadmap_repo import UserRoadmapRepo
from app.domain.roadmap_validator import (
    validate_roadmap_state,
    RoadmapValidationError,
)
from app.domain.task_template_loader import get_task_template
from app.services.ai_services import AIService
from app.services.slot_start_service import start_slot as start_slot_domain
from app.domain.task_template_resolver import resolve_task_template_id
from app.domain.governance_engine import apply_governance_to_roadmap
from app.services.learning_state_service import get_decision_context
from app.services.curriculum_service import CurriculumService
from app.core.exceptions import TemplateResolutionError, ConcurrencyError


router = APIRouter(
    prefix="/roadmap/slot",
    tags=["roadmap_slot"],
)

ai_service = AIService()


# ============================================================
# START SLOT (FIXED)
# ============================================================
from app.db.learning_state_repo import get_user_learning_state

@router.post("/start")
async def start_slot(
    slot_id: str,
    current_user: dict = Depends(get_current_user),
    repo: UserRoadmapRepo = Depends(get_user_roadmap_repo),
    db=Depends(get_db),
):
    roadmap = await repo.get_user_roadmap(str(current_user["_id"]))
    if not roadmap:
        raise HTTPException(404, "Roadmap not initialized")

    # 🔒 Global invariant: only one slot in progress
    for phase in roadmap.phases:
        for slot in phase.slots:
            if slot.status == "in_progress":
                raise HTTPException(
                    409,
                    "Another slot is already in progress",
                )

    # 🔑 Delegate to DOMAIN SERVICE (single source of truth)
    try:
        try:
            target_slot = roadmap.get_slot(slot_id)
        except ValueError:
            raise HTTPException(404, f"Slot {slot_id} not found")

        # 1. Build DecisionContext (Adaptive V3)
        context = await get_decision_context(db, str(current_user["_id"]), track_id="dsa")
        
        # 2. Apply Governance (Auto-skip/Reinforce/Promote)
        curriculum = CurriculumService.get_curriculum("dsa")
        apply_governance_to_roadmap(roadmap, curriculum, context)
        
        # Re-fetch slot in case status changed during governance
        target_slot = roadmap.get_slot(slot_id)
        
        if target_slot.status == "skipped":
             raise HTTPException(400, "This slot was automatically skipped due to your skill level. Please refresh your roadmap.")

        # 3. Resolve Template using Orchestrator
        task_template_id = resolve_task_template_id(
            slot=target_slot,
            context=context,
        )
        
        task_template = get_task_template(task_template_id)

        # V4: Global Intervention Handling
        # If the Orchestrator returned a template from a different slot/skill,
        # we consider this an "Intervention Task". 
        # We tag it in parameters eventually, but right now we ensure it runs 
        # in the current slot context, effectively "injecting" the content.
        is_intervention = False
        if task_template.slot_id and task_template.slot_id != slot_id:
            is_intervention = True
            # We could add specific headers or logging here if needed.

        task_instance = start_slot_domain(
            roadmap=roadmap,
            slot_id=slot_id,
            task_template=task_template,
            context=context,
        )

        if is_intervention:
            # Strict tagging of intervention
            task_instance.parameters["is_intervention"] = True
            task_instance.parameters["original_slot_id"] = task_template.slot_id
    except TemplateResolutionError as e:
        raise HTTPException(500, f"Configuration Error: {e}")
    except RuntimeError as e:
        raise HTTPException(400, str(e))

    roadmap.version += 1
    roadmap.last_evaluated_at = datetime.now(timezone.utc)

    try:
        validate_roadmap_state(roadmap)
    except RoadmapValidationError as e:
        raise HTTPException(
            500,
            f"Roadmap invariant violated after slot start: {e}",
        )

    try:
        await repo.update_roadmap(roadmap, expected_version=roadmap.version - 1)
    except ConcurrencyError:
        raise HTTPException(409, "Roadmap modified by another request")

    # Fetch learning state for accurate skill vector
    try:
        learning_state = await get_user_learning_state(db, str(current_user["_id"]))
        skill_vector = {k: v.level for k, v in learning_state.skill_vector.items()}
    except Exception:
        skill_vector = {}

    hint = await ai_service.generate_hint(
        slot=roadmap.get_slot(slot_id),
        user_skill_vector=skill_vector,
    )

    return {
        "slot_id": slot_id,
        "task_instance_id": task_instance.task_instance_id,
        "difficulty": task_instance.difficulty,
        "hint": hint,
        "started_at": task_instance.started_at.isoformat(),
    }


# ============================================================
# COMPLETE SLOT (UNCHANGED)
# ============================================================
@router.post("/complete")
async def complete_slot(
    slot_id: str,
    success: bool = True,
    current_user: dict = Depends(get_current_user),
    repo: UserRoadmapRepo = Depends(get_user_roadmap_repo),
):
    roadmap = await repo.get_user_roadmap(str(current_user["_id"]))
    if not roadmap:
        raise HTTPException(404, "Roadmap not initialized")

    slot_found = None
    active_phase = None

    for phase in roadmap.phases:
        if phase.phase_status != "active":
            continue

        active_phase = phase

        for slot in phase.slots:
            if slot.slot_id == slot_id:
                if slot.status != "in_progress":
                    raise HTTPException(
                        400,
                        f"Slot {slot_id} cannot be completed (status: {slot.status})",
                    )

                slot.status = "completed" if success else "failed"
                slot.active_task_instance_id = None
                slot_found = slot
                break

        if slot_found:
            break

    if not slot_found or not active_phase:
        raise HTTPException(404, f"Slot {slot_id} not found in active phase")

    skill_vector = current_user.get("skill_vector", {})
    skill_vector = await ai_service.update_skill_vector(
        skill_vector,
        slot_found,
        success,
    )
    current_user["skill_vector"] = skill_vector

    if all(
        s.status in {"completed", "failed", "remediation_required"}
        for s in active_phase.slots
    ):
        active_phase.phase_status = "completed"

        for phase in roadmap.phases:
            if phase.phase_status == "locked":
                phase.phase_status = "active"
                phase.locked_reason = None
                roadmap.current_phase = phase.phase_id
                break

    roadmap.version += 1
    roadmap.last_evaluated_at = datetime.now(timezone.utc)

    try:
        validate_roadmap_state(roadmap)
    except RoadmapValidationError as e:
        raise HTTPException(
            500,
            f"Roadmap invariant violated after slot completion: {e}",
        )

    try:
        await repo.update_roadmap(roadmap, expected_version=roadmap.version - 1)
    except ConcurrencyError:
        raise HTTPException(409, "Roadmap modified by another request")

    return {
        "slot_id": slot_id,
        "result": "completed" if success else "failed",
        "skill_vector": skill_vector,
    }


# ============================================================
# REMEDIATE SLOT (UNCHANGED)
# ============================================================
@router.post("/remediate")
async def remediate_slot(
    slot_id: str,
    current_user: dict = Depends(get_current_user),
    repo: UserRoadmapRepo = Depends(get_user_roadmap_repo),
):
    roadmap = await repo.get_user_roadmap(str(current_user["_id"]))
    if not roadmap:
        raise HTTPException(404, "Roadmap not initialized")

    slot_found = None

    for phase in roadmap.phases:
        for slot in phase.slots:
            if slot.slot_id == slot_id:
                slot.status = "remediation_required"
                slot.active_task_instance_id = None
                slot_found = slot
                break
        if slot_found:
            break

    if not slot_found:
        raise HTTPException(404, f"Slot {slot_id} not found")

    roadmap.version += 1
    roadmap.last_evaluated_at = datetime.now(timezone.utc)

    try:
        validate_roadmap_state(roadmap)
    except RoadmapValidationError as e:
        raise HTTPException(
            500,
            f"Roadmap invariant violated after remediation: {e}",
        )

    try:
        await repo.update_roadmap(roadmap, expected_version=roadmap.version - 1)
    except ConcurrencyError:
        raise HTTPException(409, "Roadmap modified by another request")

    return {
        "slot_id": slot_id,
        "status": "remediation_required",
    }
