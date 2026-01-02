# app/schemas/task_instance.py
from pydantic import BaseModel, Field,model_validator
from datetime import datetime
from typing import Optional, Dict, Literal
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

    status: TaskStatus = TaskStatus.IN_PROGRESS

    started_at: datetime
    completed_at: Optional[datetime] = None

    evaluation_signals: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_template_relationship(self):
        if not self.task_template_id.startswith(self.base_template_id):
            raise ValueError(
                f"task_template_id '{self.task_template_id}' "
                f"is not derived from base_template_id '{self.base_template_id}'"
            )
        return self
