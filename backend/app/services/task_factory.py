import yaml
from pathlib import Path
from typing import List, Dict, Optional
from app.schemas.task_template import TaskTemplate
from app.core.config import settings

# ROOT_DIR is the backend directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TASK_DIR = ROOT_DIR / settings.CURRICULUM_TASKS_ROOT

class TaskFactory:
    _cache: Dict[str, List[TaskTemplate]] = {}

    @classmethod
    def load_tasks(cls, skill: str) -> List[TaskTemplate]:
        if skill in cls._cache:
            return cls._cache[skill]

        file_path = TASK_DIR / f"{skill}.yaml"
        return cls.load_tasks_from_file(file_path, skill)

    @classmethod
    def load_tasks_from_file(cls, file_path: Path, skill: Optional[str] = None) -> List[TaskTemplate]:
        skill = skill or file_path.stem
        
        if skill in cls._cache:
            # We might want to reload if file changed, but for now cache is simple
            return cls._cache[skill]

        if not file_path.exists():
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            templates = []
            
            # Case 1: Standard flat list of templates
            for t_data in data.get("templates", []):
                # Inject skill from file context if missing
                if "skill" not in t_data:
                    t_data["skill"] = data.get("skill", skill)
                templates.append(TaskTemplate(**t_data))
            
            # Case 2: Nested templates inside slots (as in arrays.yaml)
            for slot_entry in data.get("slots", []):
                slot_id = slot_entry.get("slot_id")
                mastery_signals = slot_entry.get("mastery_signals", [])
                
                for t_data in slot_entry.get("templates", []):
                    if "skill" not in t_data:
                        t_data["skill"] = data.get("skill", skill)
                    if "slot_id" not in t_data:
                        t_data["slot_id"] = slot_id
                    
                    # Propagate mastery signals if not explicitly set on template
                    if "invariant_targets" not in t_data and mastery_signals:
                        t_data["invariant_targets"] = mastery_signals
                        
                    templates.append(TaskTemplate(**t_data))
                
            cls._cache[skill] = templates
            return templates
        except Exception as e:
            print(f"Error loading tasks for skill {skill}: {e}")
            return []

    @classmethod
    def get_task(cls, skill: str, difficulty: str, variant: str = "standard") -> Optional[TaskTemplate]:
        templates = cls.load_tasks(skill)
        
        # Simple matching strategy for now
        candidates = [
            t for t in templates 
            if t.difficulty == difficulty and t.variant == variant
        ]
        
        if not candidates:
            # Fallback: if remediation requested but not found, try standard
            if variant == "remediation":
                return cls.get_task(skill, difficulty, "standard")
            return None
            
        # In V2, we could rotate or pick based on user history here
        return candidates[0]

    @classmethod
    def get_variant_for_strategy(cls, strategy: str) -> str:
        """
        Maps a remediation strategy to a task variant.
        """
        mapping = {
            "explanation": "explanation",
            "guided_practice": "scaffolded",
            "retry_same": "standard",
            "easier_task": "easier"
        }
        return mapping.get(strategy, "standard")
    
    @classmethod
    def clear_cache(cls):
        cls._cache = {}
