from app.domain.task_template_loader import get_all_templates
from app.schemas.roadmap_state import TaskSlot
from app.core.exceptions import TemplateResolutionError
from app.services.curriculum_service import CurriculumService
from app.domain.adaptive_control import DecisionContext
from app.domain.orchestrator import AdaptiveOrchestrator
from typing import Optional


def resolve_task_template_id(
    *,
    slot: TaskSlot,
    context: Optional[DecisionContext] = None,
    track_id: str = "dsa",
) -> str:
    """
    Single source of truth for task template selection.
    Uses AdaptiveOrchestrator if context is provided, else falls back to deterministic logic.
    """
    # 1. Find all templates tied to this slot
    all_templates = get_all_templates()
    candidates = [
        t for t in all_templates
        if t.slot_id == slot.slot_id
    ]

    if not candidates:
        raise TemplateResolutionError(
            f"No templates found for slot ID: {slot.slot_id}"
        )

    # 2. Determine target variant and strategy
    is_remediation = (slot.status == "remediation_required")
    
    if is_remediation:
        # Load curriculum to find the strategy for this step
        curriculum = CurriculumService.get_curriculum(track_id)
        slot_def = curriculum.get_slot_definition(slot.slot_id)
        
        if not slot_def or not slot_def.remediation:
            raise TemplateResolutionError(f"No remediation plan defined for slot {slot.slot_id}")
            
        plan = slot_def.remediation.strategies
        step = slot.current_remediation_step
        
        if step >= len(plan):
            raise TemplateResolutionError(f"Remediation strategy exhausted for {slot.slot_id} at step {step}")
            
        required_strategy = plan[step]
        
        matches = [
            t for t in candidates
            if t.variant == "remediation" and t.strategy == required_strategy
        ]
        
        if not matches:
            # Fallback: if specific remediation variant not found, try standard
            matches = [t for t in candidates if t.variant in (None, "standard")]

        if not matches:
            raise TemplateResolutionError(
                f"No suitable template found for "
                f"{slot.slot_id} with strategy {required_strategy}."
            )
            
        return matches[0].task_template_id

    # 3. Decision Control Layer (V3 Adaptive Logic)
    if context:
        orchestrator = AdaptiveOrchestrator(context)
        template = orchestrator.plan_next_action(slot, candidates)
        return template.task_template_id

    # Normal path (standard task fallback)
    matches = [
        t for t in candidates
        if t.variant in (None, "standard")
    ]
    
    if not matches:
        raise TemplateResolutionError(
            f"No standard templates found for {slot.slot_id}."
        )

    # In V2, we might want to pick a random one or one the user hasn't seen
    return matches[0].task_template_id





