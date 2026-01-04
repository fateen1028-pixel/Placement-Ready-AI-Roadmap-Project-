from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status
from typing import Dict, Any

from app.schemas.learning_state import (
    UserLearningState,
    SkillEntry,
)
from app.db.skill_registry_repo import skill_exists


# -------------------------------
# CREATE USER LEARNING STATE
# -------------------------------

async def create_user_learning_state(
    db,
    user_id: str,
    roadmap_id: str | None = None,
    setup_profile: dict | None = None,
):
    now = datetime.utcnow()

    doc = {
        "user_id": ObjectId(user_id),
        "roadmap_id": roadmap_id,
        "skill_vector": {},              # skill_id -> SkillEntry
        "active_tasks": [],              # list of task_instance_ids
        "completed_tasks": [],           # list of task_instance_ids
        "goals": [],
        "prior_exposure_languages": [],
        "created_at": now,
        "updated_at": now,
    }

    if setup_profile:
        doc["goals"] = setup_profile.get("goals", [])
        doc["prior_exposure_languages"] = setup_profile.get(
            "prior_exposure_languages", []
        )

        # store any additional onboarding metadata
        for k, v in setup_profile.items():
            if k not in ["goals", "prior_exposure_languages"]:
                doc[k] = v

    result = await db.user_learning_state.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


# -------------------------------
# FETCH LEARNING STATE
# -------------------------------

async def get_user_learning_state(db, user_id: str, session=None) -> UserLearningState:
    doc = await db.user_learning_state.find_one(
        {"user_id": ObjectId(user_id)},
        session=session
    )

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User learning state not found",
        )

    doc["user_id"] = str(doc["user_id"])
    return UserLearningState(**doc)


# -------------------------------
# ADD OR UPDATE A SKILL ENTRY
# (used by SkillVector update engine)
# -------------------------------

async def add_or_update_skill(
    db,
    user_id: str,
    skill_id: str,
    skill_data: dict,
):
    # hard validation — no phantom skills allowed
    if not await skill_exists(db, skill_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill '{skill_id}' not found in registry",
        )

    entry = SkillEntry(**skill_data)

    result = await db.user_learning_state.update_one(
        {"user_id": ObjectId(user_id)},
        {
            "$set": {
                f"skill_vector.{skill_id}": entry.dict(),
                "updated_at": datetime.utcnow(),
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User learning state not found",
        )


# -------------------------------
# APPLY MULTIPLE SKILL UPDATES
# (bulk-safe, atomic)
# -------------------------------

async def apply_skill_vector_updates(
    db,
    user_id: str,
    updated_skills: dict[str, SkillEntry],
    session=None
):
    update_payload: Dict[str, Any] = {
        f"skill_vector.{skill_id}": entry.model_dump()
        for skill_id, entry in updated_skills.items()
    }


    update_payload["updated_at"] = datetime.utcnow()

    result = await db.user_learning_state.update_one(
        {"user_id": ObjectId(user_id)},
        {"$set": update_payload},
        session=session
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User learning state not found",
        )


# -------------------------------
# TASK TRACKING
# -------------------------------

async def add_active_task(
    db,
    user_id: str,
    task_instance_id: str,
):
    await db.user_learning_state.update_one(
        {"user_id": ObjectId(user_id)},
        {
            "$addToSet": {"active_tasks": task_instance_id},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )


async def complete_task(
    db,
    user_id: str,
    task_instance_id: str,
):
    await db.user_learning_state.update_one(
        {"user_id": ObjectId(user_id)},
        {
            "$pull": {"active_tasks": task_instance_id},
            "$addToSet": {"completed_tasks": task_instance_id},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )


# -------------------------------
# GENERIC UPDATE (RARE USE)
# -------------------------------

async def update_user_learning_state(
    db,
    user_id: str,
    update_data: dict,
):
    update_data["updated_at"] = datetime.utcnow()

    result = await db.user_learning_state.update_one(
        {"user_id": ObjectId(user_id)},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User learning state not found",
        )
