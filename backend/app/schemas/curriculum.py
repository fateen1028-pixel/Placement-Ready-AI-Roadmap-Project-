from typing import List, Optional, Literal, Dict, Union
from pydantic import BaseModel, Field

class SlotMasteryPolicy(BaseModel):
    pass_score: float = 0.6
    min_confidence: float = 0.0
    invariants_required: List[str] = Field(default_factory=list)

class SlotGovernancePolicy(BaseModel):
    entry_requirements: Dict[str, Union[float, str]] = Field(default_factory=dict)
    reinforce_if: Dict[str, Union[float, str]] = Field(default_factory=dict)
    skip_if: Dict[str, Union[float, str]] = Field(default_factory=dict)
    promote_if: Dict[str, Union[float, str]] = Field(default_factory=dict)

class SlotRemediationPolicy(BaseModel):
    max_attempts: int = 3
    strategies: List[str] = Field(default_factory=lambda: ["explanation", "guided_practice", "retry_same"])

    class Config:
        populate_by_name = True

class SlotDefinition(BaseModel):
    id: str = Field(alias="slot_id")
    skill: str
    difficulty: Literal["easy", "medium", "hard"]
    question_type: Optional[Literal["mcq", "coding", "explanation"]] = Field(None, alias="type")
    
    # Policy Fields
    mastery: SlotMasteryPolicy = Field(default_factory=SlotMasteryPolicy)
    governance: SlotGovernancePolicy = Field(default_factory=SlotGovernancePolicy)
    remediation: SlotRemediationPolicy = Field(default_factory=SlotRemediationPolicy)
    unlocks: List[str] = Field(default_factory=list)
    
    concepts: List[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True

class PhaseDefinition(BaseModel):
    phase_id: str
    name: str
    objective: Optional[str] = None
    slots: List[SlotDefinition]

class Curriculum(BaseModel):
    track_id: str
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    phases: List[PhaseDefinition]

    def get_slot_definition(self, slot_id: str) -> SlotDefinition:
        """Helper to find a slot definition by ID across all phases."""
        for phase in self.phases:
            for slot in phase.slots:
                if slot.id == slot_id:
                    return slot
        raise ValueError(f"Slot definition {slot_id} not found in curriculum {self.track_id}")
