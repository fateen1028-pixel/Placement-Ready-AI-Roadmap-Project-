# app/api/roadmap.py

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user, get_user_roadmap_repo
from app.schemas.roadmap_state import RoadmapState
from app.db.user_roadmap_repo import UserRoadmapRepo
from app.services.roadmap_service import generate_v1_roadmap
from app.domain.roadmap_validator import validate_roadmap_state, RoadmapValidationError
from bson import ObjectId
from pprint import pprint
router = APIRouter(
    prefix="/roadmap",
    tags=["roadmap"]
)


@router.get("", response_model=RoadmapState)
@router.get("/current", response_model=RoadmapState)
async def get_roadmap(
    current_user=Depends(get_current_user),
    repo: UserRoadmapRepo = Depends(get_user_roadmap_repo)
):
    """
    Retrieve the currently active roadmap for the logged-in user.
    """
    user_id = str(current_user["_id"])

    try:
        roadmap = await repo.get_user_roadmap(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Active roadmap not found")
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not initialized")
    
    # Validate roadmap integrity before returning
    try:
        validate_roadmap_state(roadmap)
    except RoadmapValidationError as e:
        raise HTTPException(status_code=500, detail=f"Roadmap corrupted: {e}")

    return roadmap


@router.post("/init", response_model=RoadmapState)
async def init_roadmap(
    user: dict = Depends(get_current_user),
    repo: UserRoadmapRepo = Depends(get_user_roadmap_repo)
):
    existing = await repo.get_user_roadmap(user_id=user["_id"])
    if existing:
        raise HTTPException(400, "Roadmap already exists")

    roadmap = generate_v1_roadmap(
        user_id=str(user["_id"]),
        goal=user.get("goal", "placement")
    )

    try:
        validate_roadmap_state(roadmap)
    except RoadmapValidationError as e:
        raise HTTPException(500, f"Generated roadmap invalid: {e}")

    await repo.create_roadmap(roadmap)

    return roadmap

@router.get("/latest", response_model=RoadmapState)
async def get_latest_roadmap(
    user=Depends(get_current_user),
    roadmap_repo: UserRoadmapRepo = Depends(get_user_roadmap_repo),
):
    user_id = str(user["_id"])

    # 1. Try active roadmap first
    roadmap = await roadmap_repo.get_user_roadmap(user_id)
    if roadmap:
        return roadmap

    # 2. Fallback to latest (completed)
    roadmap = await roadmap_repo.get_latest_roadmap(user_id)
    if roadmap:
        return roadmap

    raise HTTPException(404, "No roadmap exists")

