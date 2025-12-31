from typing import Dict


def apply_skill_deltas(
    current_skills: Dict[str, float],
    deltas: Dict[str, float]
) -> Dict[str, float]:
    updated = current_skills.copy()

    for skill, delta in deltas.items():
        old_value = updated.get(skill, 0.0)
        new_value = old_value + delta

        # Clamp between 0 and 1
        new_value = max(0.0, min(1.0, round(new_value, 3)))

        updated[skill] = new_value

    return updated
