from datetime import datetime, timezone

from app.schemas.learning_state import UserLearningState, SkillEntry, EvidenceSummary
from app.schemas.task_instance import TaskInstance
from app.schemas.ai_evaluation import AIEvaluationResult

from app.ai.skill_delta import compute_skill_deltas
from app.ai.skill_vector_engine import apply_skill_deltas


def apply_skill_vector_update(
    *,
    learning_state: UserLearningState,
    evaluation: AIEvaluationResult,
    task_instance: TaskInstance,
    task_template,
) -> None:
    """
    Domain-level SkillVector mutation.
    """

    # ================================
    # 1. Compute deltas
    # ================================
    deltas = compute_skill_deltas(
        evaluation=evaluation,
        difficulty=task_instance.difficulty,
        skill=task_template.skill,
        question_type=task_template.question_type,
    )

    # ================================
    # 2. Flatten current skill levels
    # ================================
    current_levels = {
        skill: entry.level
        for skill, entry in learning_state.skill_vector.items()
    }

    # ================================
    # 3. Apply delta engine
    # ================================
    updated_levels = apply_skill_deltas(
        current_skills=current_levels,
        deltas=deltas,
    )

    # ================================
    # 4. Persist back into SkillEntry
    # ================================
    now = datetime.now(timezone.utc)

    for skill, level in updated_levels.items():
        if skill not in learning_state.skill_vector:
            # Create NEW entry with evidence
            learning_state.skill_vector[skill] = SkillEntry(
                level=level,
                last_updated=now,
                evidence_summary=EvidenceSummary(
                    total_events=1,
                    weighted_score=evaluation.score,
                    last_event_id=task_instance.task_instance_id
                )
            )
        else:
            # Update EXISTING entry
            entry = learning_state.skill_vector[skill]
            entry.level = level
            entry.last_updated = now
            
            # Update Evidence
            if entry.evidence_summary is None:
                entry.evidence_summary = EvidenceSummary()
            
            entry.evidence_summary.total_events += 1
            entry.evidence_summary.weighted_score += evaluation.score
            entry.evidence_summary.last_event_id = task_instance.task_instance_id
