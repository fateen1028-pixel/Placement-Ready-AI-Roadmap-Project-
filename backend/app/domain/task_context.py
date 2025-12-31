# app/domain/task_context.py
from pydantic import BaseModel
from typing import Literal


class TaskContext(BaseModel):
    task_instance_id: str
    skill: str
    difficulty: Literal["easy", "medium", "hard"]
