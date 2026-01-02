from typing import Literal

Difficulty = Literal["easy", "medium", "hard"]

def downgrade_difficulty(difficulty: Difficulty) -> Difficulty:
    if difficulty == "hard":
        return "medium"
    if difficulty == "medium":
        return "easy"
    return "easy"
