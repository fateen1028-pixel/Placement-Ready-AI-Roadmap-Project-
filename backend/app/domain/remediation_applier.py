# app/domain/remediation_applier.py

from app.domain.remediation_plan import RemediationPlan
from app.schemas.roadmap_state import RoadmapState


def apply_remediation_plan(
    *,
    roadmap: RoadmapState,
    plan: RemediationPlan,
) -> None:
    """
    Mutates roadmap IN PLACE.
    Must preserve roadmap invariants.
    """

    for action in plan.actions:
        slot = roadmap.get_slot(action.slot_id)

        if action.action == "inject_remediation_task":
            slot.status = "remediation_required"

        elif action.action == "lock_dependent_slots":
            if slot.status in {"available", "in_progress"}:
                slot.status = "locked"

        else:
            raise RuntimeError(f"Unknown remediation action: {action.action}")
    

