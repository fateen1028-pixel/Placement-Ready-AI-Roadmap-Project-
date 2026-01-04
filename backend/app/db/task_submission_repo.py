from datetime import datetime, timezone
from bson import ObjectId
from app.schemas.task_submission import TaskSubmission


class TaskSubmissionRepo:
    def __init__(self, db):
        self.collection = db.task_submissions

    @staticmethod
    def _serialize(doc: dict) -> dict:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        return doc

    async def submission_exists(self, task_instance_id: str) -> bool:
        return await self.collection.find_one(
            {"task_instance_id": task_instance_id}
        ) is not None

    async def create_submission(self, data: dict, session=None) -> TaskSubmission:
        data["created_at"] = datetime.now(timezone.utc)

        result = await self.collection.insert_one(data, session=session)

        saved = await self.collection.find_one(
            {"_id": result.inserted_id},
            session=session
        )

        return TaskSubmission(**self._serialize(saved))

    async def get_submissions_for_slot(
        self,
        user_id: str,
        slot_id: str,
        session=None
    ) -> list[TaskSubmission]:
        cursor = self.collection.find(
            {"user_id": user_id, "slot_id": slot_id},
            session=session
        ).sort("created_at", -1)

        return [
            TaskSubmission(**self._serialize(doc))
            async for doc in cursor
        ]
    async def get_submission(self, user_id: str, slot_id: str, task_instance_id: str, session=None):
        """
        Check if a submission already exists for this user + slot + task_instance
        """
        submission = await self.collection.find_one({
            "user_id": user_id,
            "slot_id": slot_id,
            "task_instance_id": task_instance_id
        }, session=session)
        if submission:
            return submission
        return None
    

    async def attach_evaluation(
    self,
    submission_id: str,
    evaluation,
    session=None
):
        await self.collection.update_one(
            {"_id": ObjectId(submission_id)},
            {
                "$set": {
                    "evaluation": evaluation.model_dump(),
                    "evaluated_at": datetime.now(timezone.utc),
                    "status": "evaluated",
                }
            },
            session=session
        )

