from datetime import datetime, timezone

from app.schemas.roadmap_state import RoadmapState
from app.domain.roadmap_validator import (
    validate_roadmap_state,
    RoadmapValidationError,
)


def ensure_utc(dt):
    if isinstance(dt, datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class UserRoadmapRepo:
    def __init__(self, db):
        self.collection = db.user_roadmaps

    # ---------- Internal helpers ----------

    @staticmethod
    def _to_domain(doc: dict) -> RoadmapState:
        """
        Mongo → Domain
        NOTHING persistence-related leaves this method.
        """
        data = dict(doc)
        data.pop("_id", None)

        data["user_id"] = str(data["user_id"])
        data["generated_at"] = ensure_utc(data.get("generated_at"))
        data["last_evaluated_at"] = ensure_utc(data.get("last_evaluated_at"))

        return RoadmapState(**data)

    def _to_persistence(self, roadmap: RoadmapState, *, is_new: bool) -> dict:
        """
        Domain → Mongo
        """
        data = roadmap.model_dump()
        data["user_id"] = str(data["user_id"])

        if is_new:
            data["is_active"] = True

        return data

    # ---------- Public API ----------

    async def get_user_roadmap(self, user_id: str) -> RoadmapState | None:
        doc = await self.collection.find_one(
            {"user_id": str(user_id), "is_active": True}
        )

        if not doc:
            return None

        return self._to_domain(doc)

    async def create_roadmap(self, roadmap: RoadmapState) -> None:
        # 🔒 HARD GATE
        validate_roadmap_state(roadmap)

        await self.collection.insert_one(
            self._to_persistence(roadmap, is_new=True)
        )

    async def update_roadmap(self, roadmap: RoadmapState) -> None:
        # 🔒 HARD GATE
        validate_roadmap_state(roadmap)

        result = await self.collection.update_one(
            {"user_id": roadmap.user_id, "is_active": True},
            {"$set": self._to_persistence(roadmap, is_new=False)}
        )

        if result.matched_count != 1:
            raise RuntimeError("Failed to update active roadmap")
        
    async def get_latest_roadmap(self, user_id: str) -> RoadmapState | None:
        doc = await self.collection.find_one(
            {"user_id": str(user_id)},
            sort=[("generated_at", -1)]
        )

        if not doc:
            return None

        return self._to_domain(doc)

