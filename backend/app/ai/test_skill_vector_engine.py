from app.ai.skill_vector_engine import apply_skill_deltas
def test_simple_increase():
    current = {"arrays": 0.3}
    deltas = {"arrays": 0.15}

    result = apply_skill_deltas(current, deltas)
    print("SIMPLE:", result)
def test_upper_clamp():
    current = {"arrays": 0.95}
    deltas = {"arrays": 0.2}

    result = apply_skill_deltas(current, deltas)
    print("UPPER CLAMP:", result)
def test_negative_delta():
    current = {"arrays": 0.1}
    deltas = {"arrays": -0.2}

    result = apply_skill_deltas(current, deltas)
    print("NEGATIVE:", result)
def test_new_skill():
    current = {}
    deltas = {"graphs": 0.1}

    result = apply_skill_deltas(current, deltas)
    print("NEW SKILL:", result)
if __name__ == "__main__":
    test_simple_increase()
    test_upper_clamp()
    test_negative_delta()
    test_new_skill()
