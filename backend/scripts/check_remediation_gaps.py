import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_FILE = ROOT / 'curriculum' / 'dsa.yaml'
TASKS_DIR = ROOT / 'curriculum' / 'tasks'


def load_yaml(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def ensure_list(node):
    return node if isinstance(node, list) else []


def main():
    curriculum = load_yaml(CURRICULUM_FILE)
    slot_skill = {}
    for phase in ensure_list(curriculum.get('phases', [])):
        for slot in ensure_list(phase.get('slots', [])):
            sid = slot.get('slot_id')
            if sid:
                slot_skill[sid] = slot.get('skill')

    found_slots = set()
    remediation_slots = set()

    for path in TASKS_DIR.glob('*.yaml'):
        data = load_yaml(path)
        for slot in ensure_list(data.get('slots', [])):
            sid = slot.get('slot_id')
            if not sid:
                continue
            found_slots.add(sid)
            templates = ensure_list(slot.get('templates', []))
            if any(t.get('variant') == 'remediation' for t in templates):
                remediation_slots.add(sid)

    expected = set(slot_skill.keys())
    missing = expected - found_slots
    gaps = expected - remediation_slots

    print(f'Total slots defined in dsa.yaml: {len(expected)}')
    print(f'Slots with task definitions found: {len(found_slots)}')
    print(f'Slots missing task definitions: {len(missing)}')
    if missing:
        for s in sorted(missing):
            print('  MISSING TASK:', s)
    print('\nSlots lacking remediation variant:', len(gaps))
    for s in sorted(gaps):
        print('  NO REMEDIATION:', s)

if __name__ == '__main__':
    main()
