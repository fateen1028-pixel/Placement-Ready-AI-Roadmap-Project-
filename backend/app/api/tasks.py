from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user, get_user_roadmap_repo
from app.db.user_roadmap_repo import UserRoadmapRepo
from app.services.task_factory import TaskFactory

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/")
async def get_tasks(current_user=Depends(get_current_user)):
    return {
        "message": "Protected tasks",
        "user_id": str(current_user["_id"]),
    }

@router.get("/{instance_id}")
async def get_task_execution_details(
    instance_id: str,
    repo: UserRoadmapRepo = Depends(get_user_roadmap_repo),
    current_user=Depends(get_current_user)
):
    """
    Hydrate a TaskInstance with its static content (Question, Code, etc.)
    """
    user_id = str(current_user["_id"])
    roadmap = await repo.get_user_roadmap(user_id)
    
    if not roadmap:
        raise HTTPException(404, "Roadmap not found")

    # 1. Find the specific instance in the user's history
    #    (It could be active OR completed)
    target_instance = None
    for instance in roadmap.task_instances:
        if instance.task_instance_id == instance_id:
            target_instance = instance
            break
            
    if not target_instance:
        raise HTTPException(404, "Task instance not found in your history")

    # 2. Lookup the static content
    # Note: TaskFactory.load_tasks populates the cache for a skill.
    # We need to find the template by ID or by skill + match.
    # Since we have templates per skill in separate files, we use the skill from the instance.
    
    # Ensure cache is populated for this skill
    templates = TaskFactory.load_tasks(target_instance.skill)
    
    template = None
    for t in templates:
        if t.task_template_id == target_instance.task_template_id:
            template = t
            break
    
    if not template:
        # Fallback: Trying to load by ID might be hard without knowing the skill file,
        # but the instance HAS the skill field.
        raise HTTPException(500, f"Content missing for template: {target_instance.task_template_id} (skill: {target_instance.skill})")

    # 3. Merge and Return
    return {
        "instance_id": target_instance.task_instance_id,
        "status": target_instance.status,
        "difficulty": target_instance.difficulty,
        "slot_id": target_instance.slot_id,
        
        # Static Content
        "title": f"Task: {template.skill} ({template.difficulty})",
        "description": template.prompt,
        "language": template.language,
        "starter_code": template.starter_code,
        "question_type": template.question_type,
        "options": template.options,
        "invariants_required": template.invariant_targets,
        
        # User State (future proofing)
        "current_code": template.starter_code, # In v2, this would come from saved drafts
    }
