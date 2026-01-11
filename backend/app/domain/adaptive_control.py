from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import statistics

from app.schemas.learning_state import SkillEntry
from app.schemas.skill_history import SkillHistory
from app.schemas.task_submission import TaskSubmission

class InvariantScore(BaseModel):
    invariant_id: str
    score: float
    confidence: float
    volatility: float  # Variance or standard deviation in recent scores
    stability: Literal["stable", "unstable", "collapsing"]
    pressure: float = 0.0 # V4: Importance * Instability

class DecisionContext(BaseModel):
    user_id: str
    track_id: str
    all_scores: Dict[str, float] = Field(default_factory=dict)
    
    # V4: Global Bottleneck Awareness
    global_bottleneck: Optional[str] = None # Invariant ID with highest pressure
    
    weakest_invariants: List[InvariantScore] = Field(default_factory=list)
    unstable_invariants: List[InvariantScore] = Field(default_factory=list)
    dominant_invariants: List[InvariantScore] = Field(default_factory=list)
    confidence_band: Literal["low", "medium", "high"] = "medium"
    learning_velocity: float = 0.0  # Average level delta per submission
    noise_level: float = 0.0  # Measure of inconsistency in recent performance
    risk_level: Literal["low", "medium", "high"] = "low"
    
    # V4: Fatigue Management
    recent_template_ids: List[str] = Field(default_factory=list)

def derive_stability(volatility: float, velocity: float) -> Literal["stable", "unstable", "collapsing"]:
    if volatility > 0.25:
        return "unstable"
    if velocity < -0.1:
        return "collapsing"
    return "stable"

def build_decision_context(
    user_id: str,
    track_id: str,
    skill_vector: Dict[str, SkillEntry],
    history: List[SkillHistory],
    submissions: List[TaskSubmission],
    lookback_window: int = 5
) -> DecisionContext:
    """
    Transforms raw skill data and history into an actionable DecisionContext.
    """
    invariant_scores: List[InvariantScore] = []
    all_scores: Dict[str, float] = {}
    
    # 1. Group history by skill to calculate velocity and volatility
    skill_series: Dict[str, List[float]] = {}
    for h in history:
        if h.skill not in skill_series:
            skill_series[h.skill] = []
        skill_series[h.skill].append(float(h.new_level) / 100.0 if h.new_level > 1 else h.new_level)

    total_velocity = 0.0
    velocity_count = 0

    for skill_id, entry in skill_vector.items():
        all_scores[skill_id] = entry.level
        recent_scores = skill_series.get(skill_id, [])[-lookback_window:]
        
        # Calculate volatility (STDEV)
        volatility = statistics.stdev(recent_scores) if len(recent_scores) > 1 else 0.0
        
        # Calculate velocity (Mean Delta)
        velocity = 0.0
        if len(recent_scores) > 1:
            deltas = [recent_scores[i] - recent_scores[i-1] for i in range(1, len(recent_scores))]
            velocity = statistics.mean(deltas)
            total_velocity += velocity
            velocity_count += 1
        
        # Calculate Invariant Pressure (V4)
        # Pressure = (1.0 - score) * importance * volatility
        # We assume importance = 1.0 for now, but volatility is a multiplier.
        # High volatility on a low score = Urgent Pressure.
        pressure = (1.0 - entry.level) * (1.0 + volatility)

        invariant_scores.append(InvariantScore(
            invariant_id=skill_id,
            score=entry.level,
            confidence=entry.confidence,
            volatility=volatility,
            stability=derive_stability(volatility, velocity),
            pressure=pressure
        ))

    # 1.5 Extract Recent Probes (Fatigue)
    recent_templates = []
    if submissions:
         # submissions are sorted latest first in repo
        recent_templates = [s.task_instance_id for s in submissions[:lookback_window]]

    # 2. Categorize Invariants
    # Sorted by score ascending
    sorted_invariants = sorted(invariant_scores, key=lambda x: x.score)
    
    # Identify Global Bottleneck (Highest Pressure)
    bottleneck_candidates = sorted(invariant_scores, key=lambda x: x.pressure, reverse=True)
    global_bottleneck = bottleneck_candidates[0].invariant_id if bottleneck_candidates else None
    
    weakest = sorted_invariants[:3]
    dominant = [i for i in invariant_scores if i.score >= 0.8 and i.stability == "stable"]
    unstable = [i for i in invariant_scores if i.stability != "stable" or i.volatility > 0.15]

    # 3. Overall Metrics
    avg_velocity = total_velocity / velocity_count if velocity_count > 0 else 0.0
    avg_volatility = statistics.mean([i.volatility for i in invariant_scores]) if invariant_scores else 0.0
    
    # Simple risk and confidence heuristics
    risk = "low"
    if any(i.stability == "collapsing" for i in invariant_scores) or avg_volatility > 0.2:
        risk = "high"
    elif avg_volatility > 0.1:
        risk = "medium"

    conf_band = "medium"
    avg_conf = statistics.mean([i.confidence for i in invariant_scores]) if invariant_scores else 0.5
    if avg_conf > 0.8:
        conf_band = "high"
    elif avg_conf < 0.4:
        conf_band = "low"

    return DecisionContext(
        user_id=user_id,
        track_id=track_id,
        all_scores=all_scores,
        global_bottleneck=global_bottleneck,
        weakest_invariants=weakest,
        unstable_invariants=unstable,
        dominant_invariants=dominant,
        confidence_band=conf_band,
        learning_velocity=avg_velocity,
        noise_level=avg_volatility,
        risk_level=risk,
        recent_template_ids=recent_templates
    )
