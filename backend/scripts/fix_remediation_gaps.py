import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_FILE = ROOT / 'curriculum' / 'dsa.yaml'
TASKS_DIR = ROOT / 'curriculum' / 'tasks'
BACKUP_DIR = ROOT / 'curriculum' / 'backups_remediation'

BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Simple mental-model prompt templates per skill fallback
SKILL_PROMPTS = {
    'complexity': "Explain the core idea of this slot in a simple mental-model and why it matters. Use a real-world analogy.",
    'arrays': "Use a lockers analogy to explain the memory layout and access costs.",
    'strings': "Describe strings as arrays of characters and how traversal and slicing behave.",
    'linked_lists': "Use a treasure-hunt clue-chain analogy: each node points to the next.",
    'recursion': "Use a stack-of-plates analogy to explain call/return order.",
    'heaps_tries': "Use a corporate hierarchy for heaps and dictionary pages for tries.",
    'hash_tables': "Use a set-of-buckets (mailboxes) analogy to explain collisions and hashing.",
    'graphs': "Use a city map analogy: nodes are places, edges are roads; show traversal.",
    'dynamic_programming': "Use memoized cookbook recipes: store partial results and reuse them.",
    'bit_manipulation': "Use light switches and bit masks to show turning bits on/off.",
    'strategies': "Explain the high-level strategy with an example (divide and conquer, greedy).",
    'sorting_basics': "Explain the simple visual mental model for the sort (bubbles, selection).",
    'stacks': "Use plates or undo stack analogy.",
    'queues': "Use a waiting line (queue) analogy.",
}


def load_yaml(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def dump_yaml(path: Path, data):
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def ensure_list(node):
    return node if isinstance(node, list) else []


def make_remediation(slot_id: str, skill: str):
    prompt = SKILL_PROMPTS.get(skill, f"Explain {slot_id} in a simple mental-model analogy.")
    return {
        'id': f'{slot_id}_remediation',
        'type': 'explanation',
        'variant': 'remediation',
        'difficulty': 'easy',
        'prompt': prompt,
        'concepts': ['mental_model']
    }


def main():
    if not CURRICULUM_FILE.exists():
        print('dsa.yaml not found; aborting')
        return

    curriculum = load_yaml(CURRICULUM_FILE)

    # Build slot -> skill map
    slot_skill = {}
    for phase in ensure_list(curriculum.get('phases', [])):
        for slot in ensure_list(phase.get('slots', [])):
            sid = slot.get('slot_id')
            if sid:
                slot_skill[sid] = slot.get('skill')

    # Iterate task files
    modified_files = []

    for path in TASKS_DIR.glob('*.yaml'):
        data = load_yaml(path)
        skill = data.get('skill') or path.stem
        slots = ensure_list(data.get('slots', []))
        changed = False

        for slot in slots:
            sid = slot.get('slot_id')
            if not sid:
                continue
            templates = ensure_list(slot.get('templates', []))
            has_remediation = any(t.get('variant') == 'remediation' for t in templates)
            if not has_remediation:
                # Create remediation template
                remediation = make_remediation(sid, skill)
                templates.append(remediation)
                slot['templates'] = templates
                changed = True
                print(f"Added remediation to {path.name} -> {sid}")

        if changed:
            # backup
            backup_path = BACKUP_DIR / path.name
            if not backup_path.exists():
                backup_path.write_bytes(path.read_bytes())
            dump_yaml(path, data)
            modified_files.append(path.name)

    print('Done. Modified files:', modified_files)


if __name__ == '__main__':
    main()
