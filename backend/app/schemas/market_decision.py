from pydantic import BaseModel
from typing import Dict, Optional, List
from app.schemas.task_template import TaskTemplate

class TradeRationale(BaseModel):
    target_invariant: Optional[str] = None
    invariant_pressure: float = 0.0
    volatility: float = 0.0
    probe_cost: float = 0.0
    rank_score: float = 0.0
    rejected_alternatives_count: int = 0
    market_phase: str  # "global_intervention" | "local_optimization"

class MarketDecision(BaseModel):
    selected_template: TaskTemplate
    source_slot_id: str
    decision_type: str  # "intervention" | "organic"
    rationale: TradeRationale
    outcome_expectation: Optional[Dict[str, float]] = None 
