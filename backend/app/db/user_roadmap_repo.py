from datetime import datetime, timezone

from app.schemas.roadmap_state import RoadmapState
from app.domain.roadmap_validator import (
    validate_roadmap_state,
    RoadmapValidationError,
)
from app.core.exceptions import ConcurrencyError


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

    async def get_user_roadmap(self, user_id: str, session=None) -> RoadmapState | None:
        doc = await self.collection.find_one(
            {"user_id": str(user_id), "is_active": True},
            session=session
        )

        if not doc:
            return None

        return self._to_domain(doc)

    async def create_roadmap(self, roadmap: RoadmapState, session=None) -> None:
        # 🔒 HARD GATE
        validate_roadmap_state(roadmap)

        await self.collection.insert_one(
            self._to_persistence(roadmap, is_new=True),
            session=session
        )

    async def update_roadmap(self, roadmap: RoadmapState, expected_version: int, session=None) -> None:
        # 🔒 HARD GATE
        validate_roadmap_state(roadmap)

        # Prepare data, excluding version (handled by $inc)
        data = self._to_persistence(roadmap, is_new=False)
        data.pop("version", None)

        # Optimistic Locking:
        # Only update if the version in DB matches what we read.
        # Increment version atomically.
        result = await self.collection.find_one_and_update(
            {
                "user_id": roadmap.user_id,
                "is_active": True,
                "version": expected_version
            },
            {
                "$set": data,
                "$inc": {"version": 1}
            },
            session=session
        )

        if not result:
            # If no document matched, it means either:
            # 1. Roadmap doesn't exist (unlikely here)
            # 2. Version mismatch (Concurrency conflict)
            # We assume conflict if we knew it existed before.
            raise ConcurrencyError(
                f"Roadmap update failed. Version mismatch (expected {expected_version})."
            )
        
    async def get_latest_roadmap(self, user_id: str, session=None) -> RoadmapState | None:
        doc = await self.collection.find_one(
            {"user_id": str(user_id)},
            sort=[("generated_at", -1)],
            session=session
        )

        if not doc:
            return None

        return self._to_domain(doc)

