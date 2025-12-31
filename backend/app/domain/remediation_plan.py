from pydantic import BaseModel
from typing import List, Literal


class RemediationAction(BaseModel):
    slot_id: str
    action: Literal[
        "inject_remediation_task",
        "lock_dependent_slots",
    ]


class RemediationPlan(BaseModel):
    failed_task_instance_id: str
    actions: List[RemediationAction]
