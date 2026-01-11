from typing import List, Tuple, Optional, Set, Dict
from app.schemas.task_template import TaskTemplate
from app.domain.adaptive_control import DecisionContext
from app.domain.task_template_loader import get_all_templates
from app.schemas.market_decision import MarketDecision, TradeRationale

class AdaptiveMarket:
    """
    Global arbitration engine for finding the most valuable cognitive probe 
    across the entire curriculum.
    """
    
    def build_global_probe_pool(self) -> List[TaskTemplate]:
        """
        Scans ALL available templates across the curriculum.
        """
        return get_all_templates()

    def rank_probes(
        self, 
        probes: List[TaskTemplate], 
        context: DecisionContext
    ) -> List[Tuple[float, TaskTemplate, str, Dict]]:
        """
        Scores probes and returns (score, template, source_slot, metrics).
        """
        ranked_probes: List[Tuple[float, TaskTemplate, str, Dict]] = []
        
        # 1. Identify critical targets
        global_bottleneck = context.global_bottleneck
        weak_invariant_ids = {inv.invariant_id for inv in context.weakest_invariants}
        recent_ids = set(context.recent_template_ids)
        
        # Pre-calculate pressures for fast lookup
        pressure_map = {inv.invariant_id: inv.pressure for inv in context.weakest_invariants}
        if global_bottleneck:
            # Check unstable list too if not in weakest
            for inv in context.unstable_invariants:
                pressure_map[inv.invariant_id] = inv.pressure
        
        for template in probes:
            score = 0.0
            rationale_notes = {}
            
            # --- V4 Scoring Logic ---
            
            # A. Global Bottleneck Targeting
            if global_bottleneck and template.skill == global_bottleneck:
                base_val = 10.0
                score += base_val
                rationale_notes['target'] = global_bottleneck
                rationale_notes['pressure'] = pressure_map.get(global_bottleneck, 0.0)
                
                if template.role == "diagnostic":
                    score += 2.0  # Diagnose first

            # B. Weak Invariant Targeting
            elif template.skill in weak_invariant_ids:
                score += 5.0
                rationale_notes['target'] = template.skill
                rationale_notes['pressure'] = pressure_map.get(template.skill, 0.0)
            
            # C. Invariant Intersections
            intersection = set(template.invariant_targets).intersection(weak_invariant_ids)
            if intersection:
                bonus = len(intersection) * 1.5
                score += bonus
                
            # D. Role Arbitration & Cost
            score -= (template.probe_cost * 0.5)
            
            # F. Fatigue Penalty
            if template.task_template_id in recent_ids:
                score -= 20.0
                rationale_notes['fatigue'] = True

            if score > 0:
                ranked_probes.append((score, template, template.slot_id or "global", rationale_notes))

        # Sort by score descending
        ranked_probes.sort(key=lambda x: x[0], reverse=True)
        return ranked_probes

    def select_optimal_probe(
        self, 
        context: DecisionContext, 
        current_slot_id: str
    ) -> Optional[MarketDecision]:
        """
        Returns the single best probe payload with economic justification.
        """
        all_templates = self.build_global_probe_pool()
        ranked = self.rank_probes(all_templates, context)
        
        if not ranked:
            return None
            
        best_score, best_template, source_slot, metrics = ranked[0]
        
        # Start Threshold
        threshold = 5.0
        
        if best_score > threshold:
            rationale = TradeRationale(
                target_invariant=metrics.get('target', 'unknown'),
                invariant_pressure=metrics.get('pressure', 0.0),
                volatility=context.noise_level,
                probe_cost=best_template.probe_cost,
                rank_score=best_score,
                rejected_alternatives_count=len(ranked) - 1,
                market_phase="global_intervention" if source_slot != current_slot_id else "local_optimization"
            )
            
            return MarketDecision(
                selected_template=best_template,
                source_slot_id=source_slot,
                decision_type="intervention" if source_slot != current_slot_id else "organic",
                rationale=rationale,
                outcome_expectation={
                    "expected_pressure_reduction": (best_score * 0.1) # Crude heuristic
                }
            )
            
        return None
