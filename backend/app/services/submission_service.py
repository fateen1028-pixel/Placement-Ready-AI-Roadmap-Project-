from datetime import datetime
from typing import Dict,Any

from app.schemas.ai_evaluation import AIEvaluationResult
from app.schemas.learning_state import UserLearningState, SkillEntry
from app.ai.skill_delta import compute_skill_deltas
from app.db.learning_state_repo import (
    get_user_learning_state,
    update_user_learning_state,
)


async def process_submission_result(
    db,
    user_id: str,
    evaluation: AIEvaluationResult,
    difficulty: str,
    skill_id: str,
):
    # 1️⃣ Load user learning state
    learning_state: UserLearningState | None = await get_user_learning_state(db, user_id)
    if not learning_state:
        raise RuntimeError("Learning state not found")

    skill_vector = learning_state.skill_vector or {}

    # 2️⃣ Compute skill delta
    deltas = compute_skill_deltas(
        evaluation=evaluation,
        difficulty=difficulty,
        skill=skill_id
    )

    # 3️⃣ Prepare MongoDB updates
    mongo_updates: Dict[str, Any] = {}

    for skill_key, delta in deltas.items():
        existing: SkillEntry | None = skill_vector.get(skill_key)

        old_level = existing.level if existing else 0.0
        new_level = min(max(old_level + delta, 0.0), 1.0)

        updated_entry = SkillEntry(
            level=new_level,
            confidence=existing.confidence if existing else 1.0,
            last_updated=datetime.utcnow(),
            evidence_summary=existing.evidence_summary if existing else None,
            source_mix=existing.source_mix if existing else None,
            decay=existing.decay if existing else None
        )

        mongo_updates[f"skill_vector.{skill_key}"] = updated_entry.dict()

    # 4️⃣ Always update the learning state timestamp
    mongo_updates["updated_at"] = datetime.utcnow()

    # 5️⃣ Persist updates
    await update_user_learning_state(db=db, user_id=user_id, update_data=mongo_updates)

    return evaluation

