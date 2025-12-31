# app/schemas/task_template.py
from pydantic import BaseModel
from typing import Literal, Optional, List, Dict


class TaskTemplate(BaseModel):
    task_template_id: str
    slot_id: str

    question_type: Literal["mcq", "coding", "explanation"]
    skill: str
    difficulty: Literal["easy", "medium", "hard"]

    prompt: str

    # MCQ-only
    options: Optional[List[str]] = None
    correct_option: Optional[str] = None

    # Coding-only
    language: Optional[str] = None
    starter_code: Optional[str] = None
    test_cases: Optional[List[Dict]] = None

    # Explanation-only
    rubric: Optional[str] = None
