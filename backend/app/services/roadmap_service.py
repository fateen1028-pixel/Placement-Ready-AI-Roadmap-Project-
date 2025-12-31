from datetime import datetime, timezone
from app.schemas.roadmap_state import RoadmapState, PhaseState, TaskSlot

def generate_v1_roadmap(user_id: str, goal: str) -> RoadmapState:
    now = datetime.now(timezone.utc)

    return RoadmapState(
        user_id=user_id,
        goal=goal,
        version=1,
        status="active",
        is_active=True,

        # 🔑 REQUIRED
        task_instances=[],

        current_phase=1,
        confidence_threshold=0.75,

        phases=[
            PhaseState(
                phase_id=1,
                name="Foundations",
                phase_status="active",
                slots=[
                    TaskSlot(
                        slot_id="arrays_easy",
                        skill="arrays",
                        difficulty="easy",
                        status="available",
                    ),
                    TaskSlot(
                        slot_id="arrays_medium",
                        skill="arrays",
                        difficulty="medium",
                        status="locked",
                    ),
                ],
            ),
            PhaseState(
                phase_id=2,
                name="Intermediate",
                phase_status="locked",
                locked_reason="Complete all slots in Foundations phase",
                slots=[],
            ),
        ],

        generated_at=now,
        last_evaluated_at=now,
    )
