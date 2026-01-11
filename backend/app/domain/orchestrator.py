from typing import List, Optional
import json
from datetime import datetime
from app.schemas.roadmap_state import TaskSlot
from app.schemas.task_template import TaskTemplate
from app.domain.adaptive_control import DecisionContext
from app.core.exceptions import TemplateResolutionError
from app.domain.adaptive_market import AdaptiveMarket
from app.schemas.market_decision import MarketDecision

class AdaptiveOrchestrator:
    """
    Central authority for skill-driven task selection.
    Transforms the linear roadmap into a series of targeted cognitive probes.
    """
    def __init__(self, context: DecisionContext):
        self.context = context
        self.market = AdaptiveMarket()

    def _log_market_intervention(self, decision: MarketDecision):
        """
        AUDIT TRAIL: Records why the market overrode the slot.
        In production, this would write to a Time-Series DB (Pressure Ledger).
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "MARKET_INTERVENTION",
            "target_invariant": decision.rationale.target_invariant,
            "pressure": decision.rationale.invariant_pressure,
            "cost": decision.rationale.probe_cost,
            "score": decision.rationale.rank_score,
            "probe_id": decision.selected_template.task_template_id,
            "reason": f"Pressure {decision.rationale.invariant_pressure} > Threshold. Probe selected for efficiency."
        }
        # For now, print to stdout so it appears in logs
        print(f"[PRESSURE_LEDGER] {json.dumps(entry)}")

    def plan_next_action(self, slot: TaskSlot, candidates: List[TaskTemplate]) -> TaskTemplate:
        """
        Determines the optimal template based on DecisionContext and slot state.
        
        Priority:
        1. Reinforcement: If volatility is high or explicit reinforcement status.
        2. Diagnostic: If confidence is low or noise is high.
        3. Proof: If user is trending upward or fast-tracked.
        4. Progress (Stretch): Default learning path.
        """
        
        # 0. Global Arbitration (V4)
        # Check if the current concept is too noisy compared to peers
        # If arrays are volatile but stacks are stable, we might prefer a stabilizing probe here
        if self.context.global_bottleneck and self.context.global_bottleneck != slot.skill:
            # Check pressure
            bottleneck_skill = self.context.global_bottleneck
            pressure = 0.0
            # Find pressure from invariants
            # We iterate unstable + weakest to find the bottleneck pressure
            scan_list = self.context.unstable_invariants + self.context.weakest_invariants
            for inv in scan_list:
                if inv.invariant_id == bottleneck_skill:
                    pressure = inv.pressure
                    break
            
            critical_threshold = 1.5
            if pressure > critical_threshold:
                # Delegate to AdaptiveMarket
                market_decision = self.market.select_optimal_probe(self.context, current_slot_id=slot.slot_id)
                if market_decision:
                    # AUDIT: Log the market intervention
                    self._log_market_intervention(market_decision)
                    return market_decision.selected_template
        
        # 1. Specialized Status Logic
        if slot.status == "reinforcement_required":
            matches = [t for t in candidates if t.role == "reinforcement"]
            # Fallback if no reinforcement variant exists
            if not matches:
                matches = [t for t in candidates if t.role == "diagnostic"]
            if matches:
                return self._pick_optimal(matches)

        # 1. High Risk / High Volatility -> Reinforcement
        if self.context.risk_level == "high" or self.context.noise_level > 0.2:
            matches = [t for t in candidates if t.role == "reinforcement"]
            if matches:
                return self._pick_optimal(matches)

        # 2. Low Confidence / High Noise -> Diagnostic
        if self.context.confidence_band == "low" or self.context.noise_level > 0.1:
            matches = [t for t in candidates if t.role == "diagnostic"]
            if matches:
                 # Prefer diagnostic templates that target known weak invariants
                weak_ids = {i.invariant_id for i in self.context.weakest_invariants}
                targeted = [t for t in matches if set(t.invariant_targets).intersection(weak_ids)]
                return self._pick_optimal(targeted or matches)

        # 3. Upward Trend / Fast Track -> Proof
        if "fast_track" in slot.flags or self.context.learning_velocity > 0.1:
            matches = [t for t in candidates if t.role == "proof"]
            if matches:
                return self._pick_optimal(matches)

        # 4. Success / Standard Path -> Stretch
        matches = [t for t in candidates if t.role == "stretch"]
        if not matches:
             # Fallback to standard templates
             matches = [t for t in candidates if t.variant in (None, "standard")]
             
        if not matches:
            raise TemplateResolutionError(f"No suitable templates found for slot {slot.slot_id} with role-based selection.")
            
        return self._pick_optimal(matches)

    def _pick_optimal(self, templates: List[TaskTemplate]) -> TaskTemplate:
        """
        Picks the "cheapest" probe (least cognitive load) among candidates to stabilize the signal.
        """
        if not templates:
            raise TemplateResolutionError("Internal Error: No templates available for selection logic.")
        return min(templates, key=lambda t: t.probe_cost)
