# app/schemas/task_template.py
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional, List, Dict, Any


class TaskTemplate(BaseModel):
    task_template_id: str = Field(alias="id")
    base_template_id: Optional[str] = Field(None, alias="base_id")
    slot_id: Optional[str] = None
    skill: str
    difficulty: Literal["easy", "medium", "hard"] = "easy"
    question_type: Literal["mcq", "coding", "explanation"] = Field(alias="type")
    
    variant: Optional[str] = "standard"
    strategy: Optional[Literal["explanation", "guided_practice", "retry_same", "easier_task"]] = None
    concepts: List[str] = Field(default_factory=list)

    # V3: Skill-Driven Intelligence
    invariant_targets: List[str] = Field(default_factory=list)
    role: Literal["diagnostic", "reinforcement", "stretch", "proof"] = "diagnostic"
    probe_cost: float = 1.0 # Cognitive load / time estimate

    prompt: str

    # MCQ-only
    options: Optional[List[str]] = None
    correct_option: Optional[Any] = Field(None, alias="correct_answer")

    # Coding-only
    language: Optional[str] = None
    starter_code: Optional[str] = None
    test_cases: Optional[List[Dict]] = None

    # Explanation-only
    rubric: Optional[str] = None
    
    @model_validator(mode="after")
    def set_default_base_id(self):
        if self.base_template_id is None:
            self.base_template_id = self.task_template_id
        return self

    class Config:
        populate_by_name = True
