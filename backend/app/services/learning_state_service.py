from typing import Optional
from app.db import learning_state_repo, skill_history_repo
from app.db.task_submission_repo import TaskSubmissionRepo
from app.schemas.learning_state import UserLearningState
from app.domain.adaptive_control import build_decision_context, DecisionContext
from fastapi import HTTPException, status
from datetime import datetime

async def create_initial_learning_state(db, user_id: str, roadmap_id: Optional[str] = None, setup_profile: Optional[dict] = None):
    # Create a new user_learning_state document for the user
    return await learning_state_repo.create_user_learning_state(db, user_id, roadmap_id, setup_profile=setup_profile)

async def get_learning_state(db, user_id: str):
    state = await learning_state_repo.get_user_learning_state(db, user_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning state not found")
    return state

async def update_learning_state(db, user_id: str, update_data: dict):
    result = await learning_state_repo.update_user_learning_state(db, user_id, update_data)
    if result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning state not updated")
    return await get_learning_state(db, user_id)

async def get_decision_context(db, user_id: str, track_id: str) -> DecisionContext:
    state = await get_learning_state(db, user_id)
    history = await skill_history_repo.get_skill_history_for_user(db, user_id)
    
    submission_repo = TaskSubmissionRepo(db)
    submissions = await submission_repo.get_submissions_for_user(user_id, limit=50)
    
    return build_decision_context(
        user_id=user_id,
        track_id=track_id,
        skill_vector=state.skill_vector,
        history=history,
        submissions=submissions
    )
