from app.schemas.ai_evaluation import AIEvaluationResult
from app.ai.skill_delta import compute_skill_deltas

def run_test():
    evaluation = AIEvaluationResult(
        passed=True,
        score=0.9,
        feedback="ok",
        detected_concepts=[],
        mistakes=[]
    )

    result = compute_skill_deltas(
    evaluation=evaluation,
    difficulty="easy",
    skill="arrays",
    question_type="mcq"
)

    print("RESULT:", result)

if __name__ == "__main__":
    run_test()
