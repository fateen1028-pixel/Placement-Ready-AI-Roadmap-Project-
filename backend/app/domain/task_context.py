# app/domain/task_context.py
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any


class TaskContext(BaseModel):
    task_instance_id: str
    skill: str
    difficulty: str
    question_type: str
    
    # Adaptive Parameters (V3)
    parameters: Dict[str, Any] = Field(default_factory=dict)

from app.domain.adaptive_control import DecisionContext
from app.schemas.task_template import TaskTemplate

def modulate_task_parameters(context: DecisionContext, template: TaskTemplate) -> Dict[str, Any]:
    """
    Elastic difficulty shaping.
    Modulates task parameters based on confidence, volatility, and velocity.
    """
    params = {}
    
    # 1. High Stability + Performance -> Increase Cognitive Load
    if context.confidence_band == "high" and context.noise_level < 0.1:
        params["input_size"] = "large"
        params["constraint_density"] = "high"
        params["ambiguity_level"] = "high"
        
    # 2. Low Confidence / High Volatility -> Reduce Degrees of Freedom
    elif context.confidence_band == "low" or context.noise_level > 0.2:
        params["input_size"] = "small"
        params["scaffolding"] = "detailed"
        params["edge_density"] = "low"
        
    # 3. Targeted Invariant Stress
    # (Future: add specific parameters for specific invariants)
    
    return params
