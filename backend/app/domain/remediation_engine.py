from app.domain.remediation_plan import (
    RemediationPlan,
    RemediationAction,
)
from app.schemas.roadmap_state import RoadmapState

DIFFICULTY_ORDER = {
    "easy": 0,
    "medium": 1,
    "hard": 2,
}


def build_remediation_plan(
    roadmap: RoadmapState,
    failed_task_instance_id: str,
) -> RemediationPlan:
    """
    Builds a deterministic remediation plan for a failed task instance.
    This function MUST NOT mutate roadmap state.
    """

    # ─────────────────────────────────────────────
    # 1️⃣ Locate failed TaskInstance
    # ─────────────────────────────────────────────
    task_instance = roadmap.get_task_instance(failed_task_instance_id)

    if task_instance.status != "failed":
        raise ValueError(
            "Remediation requested for non-failed task instance"
        )

    # ─────────────────────────────────────────────
    # 2️⃣ Locate owning slot & phase
    # ─────────────────────────────────────────────
    failed_slot = None
    owning_phase = None

    for phase in roadmap.phases:
        for slot in phase.slots:
            if slot.slot_id == task_instance.slot_id:
                failed_slot = slot
                owning_phase = phase
                break
        if failed_slot:
            break

    if failed_slot is None or owning_phase is None:
        raise ValueError(
            "Failed slot not found in roadmap phases"
        )

    # ─────────────────────────────────────────────
    # 3️⃣ Build remediation actions
    # ─────────────────────────────────────────────
    actions: list[RemediationAction] = []

    # Rule 1 — Inject remediation task for failed slot
    actions.append(
        RemediationAction(
            slot_id=failed_slot.slot_id,
            action="inject_remediation_task",
        )
    )

    # Rule 2 — Lock dependent slots (same phase, same skill, higher difficulty)
    failed_difficulty_rank = DIFFICULTY_ORDER[failed_slot.difficulty]

    for slot in owning_phase.slots:
        if slot.skill != failed_slot.skill:
            continue

        if DIFFICULTY_ORDER[slot.difficulty] <= failed_difficulty_rank:
            continue

        actions.append(
            RemediationAction(
                slot_id=slot.slot_id,
                action="lock_dependent_slots",
            )
        )

    # ─────────────────────────────────────────────
    # 4️⃣ Return plan
    # ─────────────────────────────────────────────
    return RemediationPlan(
        failed_task_instance_id=failed_task_instance_id,
        actions=actions,
    )
