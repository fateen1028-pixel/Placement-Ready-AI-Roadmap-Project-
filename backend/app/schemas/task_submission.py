from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional,Dict
from app.schemas.ai_evaluation import AIEvaluationResult


class TaskSubmissionCreate(BaseModel):
    slot_id: str
    task_instance_id: str
    payload: Dict[str, Any]


class TaskSubmission(BaseModel):
    id: str
    user_id: str
    slot_id: str
    task_instance_id: str
    payload: dict
    status: str = "submitted"
    created_at: datetime
    evaluation: AIEvaluationResult | None = None
    evaluated_at: Optional[datetime] = None
