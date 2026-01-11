# app/schemas/task_instance.py
from pydantic import BaseModel, Field,model_validator
from datetime import datetime
from typing import Optional, Dict, Literal, Any
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskInstance(BaseModel):
    task_instance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill: str
    slot_id: str

    base_template_id: str        # canonical
    task_template_id: str        # resolved (may be remediation)

    difficulty: Literal["easy", "medium", "hard"]
    question_type: Optional[Literal["mcq", "coding", "explanation"]] = Field(None, alias="type")

    status: TaskStatus = TaskStatus.IN_PROGRESS

    started_at: datetime
    completed_at: Optional[datetime] = None

    evaluation_signals: Dict[str, float] = Field(default_factory=dict)

    # V3 Continuous Shaping
    parameters: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}
