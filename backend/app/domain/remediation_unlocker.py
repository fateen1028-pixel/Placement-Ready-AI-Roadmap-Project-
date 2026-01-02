# app/domain/remediation_unlocker.py

from app.schemas.roadmap_state import RoadmapState


def unlock_dependent_slots_after_remediation(
    *,
    roadmap: RoadmapState,
    remediated_slot_id: str,
) -> None:
    """
    Unlock slots that were locked due to dependency failure
    AFTER a successful remediation.
    """

    found = False

    for phase in roadmap.phases:
        for slot in phase.slots:
            if slot.slot_id == remediated_slot_id:
                found = True
                continue

            if not found:
                continue

            # Only unlock slots locked due to dependency failure
            if slot.status == "locked" and slot.locked_reason == "dependency_failed":
                slot.status = "available"
                slot.locked_reason = None

    if not found:
        raise RuntimeError(
            f"Remediated slot {remediated_slot_id} not found in roadmap"
        )
