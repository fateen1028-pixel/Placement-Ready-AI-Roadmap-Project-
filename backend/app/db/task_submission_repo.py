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

    async def get_submissions_for_user(
        self,
        user_id: str,
        limit: int = 50,
        session=None
    ) -> list[TaskSubmission]:
        cursor = self.collection.find(
            {"user_id": user_id},
            session=session
        ).sort("created_at", -1).limit(limit)

        return [
            TaskSubmission(**self._serialize(doc))
            async for doc in cursor
        ]

    async def get_submission(self, user_id: str, slot_id: str, task_instance_id: str, session=None):
        """
        Check if a submission already exists for this user + slot + task_instance
        """
        doc = await self.collection.find_one(
            {
                "user_id": user_id,
                "slot_id": slot_id,
                "task_instance_id": task_instance_id
            },
            session=session
        )
        if doc:
            return TaskSubmission(**self._serialize(doc))
        return None

    async def get_global_score_stats(self, hours: int = 24, skill: str = None, difficulty: str = None) -> dict:
        """
        V2.5: Global Score Distribution Monitoring
        V2.5.2.1: Segmented Stats
        """
        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        cutoff_dt = datetime.fromtimestamp(cutoff, timezone.utc)

        match_stage = {"created_at": {"$gte": cutoff_dt}}
        
        # Add filters if provided
        if skill:
            # Assuming we can join or store skill/difficulty on submission. 
            # For now, let's assume they are stored or we rely on task_instance_id lookup.
            # Ideally, TaskSubmission should have these fields denormalized for analytics.
            # Let's assume they are added to the schema or we query by task_instance_id if needed.
            # BUT, for V2.5 speed, let's assume we might need to add them to TaskSubmission schema later.
            # For now, let's just support if they exist in the doc.
            match_stage["skill"] = skill
            
        if difficulty:
            match_stage["difficulty"] = difficulty

        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": None,
                "avg_score": {"$avg": "$score"},
                "std_dev": {"$stdDevPop": "$score"},
                "count": {"$sum": 1}
            }}
        ]
        
        cursor = self.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        if result:
            return {
                "avg_score": result[0]["avg_score"],
                "std_dev": result[0]["std_dev"],
                "count": result[0]["count"]
            }
        return {}

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

