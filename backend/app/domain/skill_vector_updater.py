from datetime import datetime, timezone

from app.schemas.learning_state import UserLearningState, SkillEntry, EvidenceSummary, SourceMix
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
                confidence=0.1,  # Initial confidence for first observation
                last_updated=now,
                evidence_summary=EvidenceSummary(
                    total_events=1,
                    weighted_score=evaluation.score,
                    last_event_id=task_instance.task_instance_id
                ),
                source_mix=SourceMix(
                    priors=0.0,
                    tasks=1.0,  # 100% from this task
                    assessments=0.0,
                    projects=0.0
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

            # Update Confidence (Simple heuristic: grows with exposure)
            # Cap at 1.0, increment by 0.05 per interaction
            entry.confidence = min(1.0, entry.confidence + 0.05)

            # Update Source Mix (Moving average towards 'tasks')
            if entry.source_mix is None:
                entry.source_mix = SourceMix()
            
            # Shift 10% towards tasks
            alpha = 0.1
            entry.source_mix.tasks = (1 - alpha) * entry.source_mix.tasks + alpha * 1.0
            entry.source_mix.priors = (1 - alpha) * entry.source_mix.priors
            entry.source_mix.assessments = (1 - alpha) * entry.source_mix.assessments
            entry.source_mix.projects = (1 - alpha) * entry.source_mix.projects
