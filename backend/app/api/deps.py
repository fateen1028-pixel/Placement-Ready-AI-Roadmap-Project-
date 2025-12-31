from fastapi import Depends, Cookie, HTTPException, status
import jwt

from app.utils.security import decode_token
from app.db.user_repo import get_user_by_id
from app.db.base import get_database
from app.db.user_roadmap_repo import UserRoadmapRepo
from app.db.task_submission_repo import TaskSubmissionRepo
from fastapi import Request


async def get_db():
    return get_database()

async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db = Depends(get_db),
):
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NO_TOKEN",
        )

    try:
        user_id = decode_token(access_token, expected_type="access")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCESS_TOKEN_EXPIRED",
        )

    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="USER_NOT_FOUND",
        )

    return user



def get_user_roadmap_repo(db = Depends(get_db)):
    return UserRoadmapRepo(db)

def get_task_submission_repo(request: Request):
    return TaskSubmissionRepo(request.app.state.db)