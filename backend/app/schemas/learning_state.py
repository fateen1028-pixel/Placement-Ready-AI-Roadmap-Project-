from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class EvidenceSummary(BaseModel):
    total_events: int = 0
    weighted_score: float = 0.0
    last_event_id: Optional[str] = None

class SourceMix(BaseModel):
    priors: float = 1.0
    tasks: float = 0.0
    assessments: float = 0.0
    projects: float = 0.0

class DecayInfo(BaseModel):
    half_life_days: int = 90
    last_decay_applied: Optional[datetime] = None

class SkillEntry(BaseModel):
    level: float = 0.0
    confidence: float = 0.0
    last_updated: Optional[datetime] = None
    evidence_summary: Optional[EvidenceSummary] = Field(default_factory=EvidenceSummary)
    source_mix: Optional[SourceMix] = Field(default_factory=SourceMix)
    decay: Optional[DecayInfo] = Field(default_factory=DecayInfo)


class UserLearningState(BaseModel):
    user_id: str
    skill_vector: Dict[str, SkillEntry]  # dynamic skill map
    active_tasks: List[str] = Field(default_factory=list)
    completed_tasks: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    prior_exposure_languages: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        arbitrary_types_allowed = True
