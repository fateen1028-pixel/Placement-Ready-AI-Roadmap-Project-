from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Set
from datetime import datetime

from app.schemas.task_instance import TaskInstance
from app.domain.evaluation_history import EvaluationSnapshot


class TaskSlot(BaseModel):
    slot_id: str
    skill: str
    difficulty: Literal["easy", "medium", "hard"]
    question_type: Optional[Literal["mcq", "coding", "explanation"]] = Field(None, alias="type")
    status: Literal[
        "locked",
        "available",
        "in_progress",
        "completed",
        "failed",
        "remediation_required",
        "skipped",
        "reinforcement_required",
    ]
    active_task_instance_id: Optional[str] = None
    locked_reason: Optional[Literal["dependency_failed", "remediation_required", "requirements_not_met"]] = None
    remediation_attempts: int = 0
    
    # 🔑 NEW: Track position in the remediation strategy list
    current_remediation_step: int = 0
    
    # V2.3: Truthful UX
    user_message: Optional[str] = None

    # V2.4: Evaluation Consistency
    evaluation_history: List[EvaluationSnapshot] = []
    flags: Set[str] = set()

    model_config = {"populate_by_name": True}


class PhaseState(BaseModel):
    phase_id: str
    name: str
    phase_status: Literal["locked", "active", "completed"]
    slots: List[TaskSlot]
    locked_reason: Optional[str] = None

    model_config = {"extra": "forbid"}


class RoadmapState(BaseModel):
    user_id: str
    goal: str
    version: int
    status: Literal["active", "completed", "locked"]
    is_active: bool

    current_phase: str
    phases: List[PhaseState]

    # 🔑 CRITICAL
    task_instances: List[TaskInstance]

    confidence_threshold: float
    locked_reason: Optional[str] = None

    generated_at: datetime
    last_evaluated_at: datetime

    # ==========================
    # Slot lookup
    # ==========================
    def get_slot(self, slot_id: str) -> TaskSlot:
        for phase in self.phases:
            for slot in phase.slots:
                if slot.slot_id == slot_id:
                    return slot
        raise ValueError(f"Slot with id {slot_id} not found")

    # ==========================
    # TaskInstance lookup
    # ==========================
    def get_task_instance(self, task_instance_id: str) -> TaskInstance:
        for ti in self.task_instances:
            if ti.task_instance_id == task_instance_id:
                return ti
        raise ValueError(f"TaskInstance {task_instance_id} not found")
    def validate_state(self) -> None:
        # Example invariants (minimum)
        active_phases = [p for p in self.phases if p.phase_status == "active"]
        if len(active_phases) > 1:
            raise RuntimeError("More than one active phase")

        for phase in self.phases:
            for slot in phase.slots:
                if slot.active_task_instance_id:
                    ti = self.get_task_instance(slot.active_task_instance_id)
                    if ti.slot_id != slot.slot_id:
                        raise RuntimeError("TaskInstance-slot mismatch")
