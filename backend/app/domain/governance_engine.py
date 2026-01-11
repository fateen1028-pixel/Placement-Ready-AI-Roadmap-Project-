from typing import Dict, Union
from app.schemas.roadmap_state import RoadmapState, TaskSlot
from app.schemas.curriculum import Curriculum, SlotDefinition
from app.domain.adaptive_control import DecisionContext

def apply_governance_to_roadmap(
    roadmap: RoadmapState,
    curriculum: Curriculum,
    context: DecisionContext
):
    """
    Scans the roadmap and applies skip/reinforce/promote rules based on DecisionContext.
    Moves the roadmap from linear to skill-governed.
    """
    for phase in roadmap.phases:
        for slot in phase.slots:
            # We don't apply governance to already completed or skipped slots
            if slot.status in ["completed", "skipped", "failed"]:
                continue
                
            slot_def = curriculum.get_slot_definition(slot.slot_id)
            policy = slot_def.governance
            
            # 1. Check Skip conditions (Top Priority)
            if _meets_policy(policy.skip_if, context):
                slot.status = "skipped"
                slot.user_message = "Automatically skipped based on your current skill level."
                continue

            # 2. Check Reinforcement conditions
            if _meets_policy(policy.reinforce_if, context, require_tracked_skill=True):
                slot.status = "reinforcement_required"
                slot.user_message = "This skill needs reinforcement before you proceed."
                continue
                
            # 3. Check Promotion conditions
            if _meets_policy(policy.promote_if, context):
                # Mark as available but with a 'fast_track' flag for the orchestrator
                slot.status = "available"
                slot.flags.add("fast_track")
                slot.user_message = "You've been fast-tracked for this skill!"
            
            # 4. Check Entry requirements for locked slots
            has_reqs = bool(policy.entry_requirements)
            meets_reqs = _meets_policy(policy.entry_requirements, context)

            if slot.status == "locked" and slot.locked_reason == "requirements_not_met":
                if not has_reqs or meets_reqs:
                    slot.status = "available"
                    slot.locked_reason = None
            elif slot.status == "available":
                # Only re-lock if requirements explicitly exist and are failing
                if has_reqs and not meets_reqs:
                    slot.status = "locked"
                    slot.locked_reason = "requirements_not_met"

def _evaluate_threshold(score: float, threshold: Union[float, str]) -> bool:
    if isinstance(threshold, (float, int)):
        return score >= threshold
    
    threshold_str = str(threshold).strip()
    try:
        if threshold_str.startswith(">="):
            return score >= float(threshold_str[2:])
        elif threshold_str.startswith(">"):
            return score > float(threshold_str[1:])
        elif threshold_str.startswith("<="):
            return score <= float(threshold_str[2:])
        elif threshold_str.startswith("<"):
            return score < float(threshold_str[1:])
        else:
            return score >= float(threshold_str)
    except ValueError:
        return False

def _meets_policy(
    requirements: Dict[str, Union[float, str]], 
    context: DecisionContext,
    require_tracked_skill: bool = False
) -> bool:
    """
    Checks if the user's current scores in DecisionContext meet ALL of the required thresholds.
    """
    if not requirements:
        return False
        
    for skill_id, threshold in requirements.items():
        if require_tracked_skill and skill_id not in context.all_scores:
            return False

        user_score = context.all_scores.get(skill_id, 0.0)
        if not _evaluate_threshold(user_score, threshold):
            return False
    return True
