import sys
import os
sys.path.append(os.getcwd())

from app.domain.adaptive_market import AdaptiveMarket
from app.domain.adaptive_control import DecisionContext, InvariantScore
from app.schemas.task_template import TaskTemplate
from app.domain.orchestrator import AdaptiveOrchestrator
from app.schemas.roadmap_state import TaskSlot

# Mock Data
def mock_context_with_pressure():
    # Create context with high pressure on a specific invariant
    ctx = DecisionContext(
        user_id="user_123",
        track_id="track_456",
        learning_velocity=0.5,
        confidence_band="low",
        noise_level=0.3, # Correct field
        recent_template_ids=[],
        weakest_invariants=[
            InvariantScore(invariant_id="pointer_manipulation", pressure=2.0, score=0.3, confidence=0.8, volatility=0.2, stability="unstable")
        ],
        unstable_invariants=[],
        global_bottleneck="pointer_manipulation",
        risk_level="high"
    )
    return ctx


def mock_templates():
    # Returns a list of dummy templates
    t1 = TaskTemplate(
        task_template_id="t1",
        skill="pointer_manipulation",
        difficulty="medium",
        role="diagnostic",
        variant="standard",
        probe_cost=0.5,
        invariant_targets=["pointer_manipulation"],
        description="Test Probe",
        type="coding",
        prompt="Analyze this pointer logic..."
    )
    t2 = TaskTemplate(
        task_template_id="t2",
        skill="arrays",
        difficulty="easy",
        role="stretch",
        variant="standard",
        probe_cost=1.0,
        invariant_targets=["index_access"],
        description="Distractor",
        type="coding",
        prompt="Write array access code..."
    )
    return [t1, t2]

def test_market_audit():
    print("--- Testing Market Audit ---")
    
    # 1. Setup Market and Context
    market = AdaptiveMarket()
    ctx = mock_context_with_pressure()
    
    # Inject mock templates into market (monkeypatch)
    market.build_global_probe_pool = mock_templates
    
    # 2. Select Probe
    decision = market.select_optimal_probe(ctx, current_slot_id="arrays_slot")
    
    if decision:
        print(f"Decision Made: {decision.decision_type}")
        print(f"Selected: {decision.selected_template.task_template_id}")
        print(f"Rationale: {decision.rationale}")
        
        assert decision.rationale.target_invariant == "pointer_manipulation"
        assert decision.rationale.invariant_pressure == 2.0
        assert decision.rationale.rank_score > 0
    else:
        print("No decision made (Unexpected for high pressure)")

def test_orchestrator_log():
    print("\n--- Testing Orchestrator Logging ---")
    ctx = mock_context_with_pressure()
    orch = AdaptiveOrchestrator(ctx)
    orch.market.build_global_probe_pool = mock_templates
    
    # Mock Slot
    slot = TaskSlot(
        slot_id="arrays_slot", 
        skill="arrays", 
        status="in_progress", 
        difficulty="medium",
        completed_tasks=[]
    )
    
    # This should trigger intervention because global_bottleneck="pointer_manipulation" != slot.skill="arrays"
    # and pressure=2.0 > 1.5
    
    candidates = [] # Should not matter if market takes over
    
    result_template = orch.plan_next_action(slot, candidates)
    
    print(f"Orchestrator returned: {result_template.task_template_id}")
    assert result_template.task_template_id == "t1" # The diagnostic probe for pointers

if __name__ == "__main__":
    test_market_audit()
    test_orchestrator_log()
