# SkillForgeAI System Architecture & Flow Documentation

## 1. System Overview

SkillForgeAI is an adaptive learning platform that generates personalized roadmaps for users. The core of the system is a dynamic state machine that manages **Roadmaps**, **Phases**, **Slots**, and **Task Instances**.

This document details the internal mechanics of the Task Execution Lifecycle, specifically focusing on the **Remediation Restart Flow**, which ensures users are never stranded when they fail a task.

---

## 2. Core Domain Models

### 2.1 Roadmap State (`RoadmapState`)
The root aggregate for a user's learning journey.
- **`phases`**: Ordered list of learning phases.
- **`task_instances`**: A flat history of all tasks ever attempted (successful or not).
- **`status`**: `active`, `completed`, or `locked`.
- **`locked_reason`**: If locked, explains why (e.g., `too_many_remediation_failures`).

### 2.2 Task Slot (`TaskSlot`)
A placeholder in a roadmap phase that represents a specific skill requirement.
- **`slot_id`**: Unique identifier.
- **`status`**:
    - `available`: Ready to be started.
    - `in_progress`: Currently active.
    - `completed`: Successfully passed.
    - `remediation_required`: Failed, waiting for retry.
    - `failed`: Permanently failed (locks roadmap).
- **`remediation_attempts`**: Counter for retries (0-based).
- **`active_task_instance_id`**: Pointer to the currently running task (if any).

### 2.3 Task Instance (`TaskInstance`)
An immutable record of a specific attempt at a task.
- **`task_instance_id`**: UUID.
- **`slot_id`**: Link back to the slot.
- **`status`**: `in_progress`, `submitted`, `completed`, `failed`.
- **`payload`**: The user's submission data.

---

## 3. The Task Execution Lifecycle

The system follows a strict cycle: **Start -> Submit -> Evaluate -> Update**.

### 3.1 Step 1: Starting a Slot
**Endpoint**: `POST /roadmap/slot/start`
**Service**: `app.services.slot_start_service.start_slot`

When a user clicks "Start" on a slot:
1.  **Validation**: Checks if the slot is `available` OR `remediation_required`.
2.  **Remediation Check**:
    - If `status == "remediation_required"`, the system **increments `remediation_attempts`**.
    - This is the critical "Restart Flow" logic.
3.  **Task Creation**:
    - A new `TaskInstance` is created with a unique ID.
    - `TaskInstance.status` set to `IN_PROGRESS`.
4.  **State Update**:
    - `Slot.status` becomes `in_progress`.
    - `Slot.active_task_instance_id` is set to the new `TaskInstance.id`.
    - The new `TaskInstance` is appended to `Roadmap.task_instances`.

### 3.2 Step 2: Submission
**Endpoint**: `POST /submissions`
**Service**: `app.api.submissions.submit_task`

When a user submits their work:
1.  **Guard Checks**:
    - Slot must be `in_progress`.
    - Submission `task_instance_id` must match `Slot.active_task_instance_id`.
2.  **Virtual Submission**: A temporary submission object is created for evaluation.
3.  **Handover**: Control is passed to the Evaluation Service.

### 3.3 Step 3: Evaluation & State Mutation
**Service**: `app.services.evaluation_service.evaluate_submission_and_update_roadmap`

This is the brain of the operation.
1.  **AI Evaluation**: The submission is sent to the LLM (Gemini/Groq) for grading.
2.  **Outcome Handling**:

    **Scenario A: PASS**
    - `TaskInstance.status` -> `COMPLETED`.
    - `Slot.status` -> `completed`.
    - **Unlock Logic**: The system calls `_unlock_next_slot_in_phase` to make the next slot `available`.

    **Scenario B: FAIL (Remediation)**
    - `TaskInstance.status` -> `FAILED`.
    - `Slot.status` -> `remediation_required`.
    - **Crucial Note**: We do *not* increment attempts here. Attempts are incremented only when the user *starts* the retry. This prevents double-counting.
    - `Slot.active_task_instance_id` -> `None` (Slot is now idle, waiting for restart).

    **Scenario C: FAIL (Max Attempts Exceeded)**
    - If `Slot.remediation_attempts > MAX_REMEDIATION_ATTEMPTS`:
        - `Slot.status` -> `failed`.
        - `Roadmap.status` -> `locked`.
        - `Roadmap.locked_reason` -> `too_many_remediation_failures`.
        - The user is blocked and requires manual intervention or a roadmap reset.

---

## 4. The Remediation Restart Flow (Detailed)

This specific flow ensures that users can retry failed tasks without getting stuck.

### The Problem
In previous versions, a slot in `remediation_required` was a dead end. The system didn't know how to transition it back to `in_progress`.

### The Solution (Implemented)
We treat `remediation_required` as a valid "startable" state, but with side effects.

### Logic Flow
1.  **User Fails Task 1**
    - Slot Status: `remediation_required`
    - Attempts: 0
    - Active Task: None

2.  **User Clicks "Retry"**
    - API Call: `POST /roadmap/slot/start`
    - **System Action**:
        - Detects `remediation_required`.
        - `attempts` becomes 1.
        - Generates **Task Instance 2** (New UUID).
        - Slot Status: `in_progress`.
        - Active Task: Task Instance 2.

3.  **User Submits Task 2**
    - **If Pass**: Slot Complete.
    - **If Fail**:
        - Slot Status: `remediation_required`.
        - Attempts: 1 (Unchanged during eval).
        - Active Task: None.

4.  **User Clicks "Retry" Again**
    - API Call: `POST /roadmap/slot/start`
    - **System Action**:
        - Detects `remediation_required`.
        - `attempts` becomes 2.
        - Generates **Task Instance 3**.
        - ... Loop continues until success or lock.

---

## 5. Code Reference

### 5.1 Slot Start Service (`app/services/slot_start_service.py`)

```python
def start_slot(...):
    # ...
    if slot.status == "remediation_required":
        slot.remediation_attempts += 1  # <--- The Fix
    # ...
    task_instance = TaskInstance(...)
    roadmap.task_instances.append(task_instance)
```

### 5.2 Evaluation Service (`app/services/evaluation_service.py`)

```python
def evaluate_submission_and_update_roadmap(...):
    # ...
    if evaluation.passed:
        slot.status = "completed"
    else:
        slot.status = "remediation_required"
        # Note: We do NOT increment attempts here anymore.
    
    slot.active_task_instance_id = None
    # ...
```

---

## 6. Database & Persistence

The system uses MongoDB. The `RoadmapState` is stored as a single document per user.

- **Collection**: `user_roadmaps`
- **Concurrency**: Optimistic locking is used via the `version` field to prevent race conditions during rapid submissions or starts.
- **Transactions**: Critical updates (Submission creation + Roadmap update) happen inside a MongoDB ACID transaction.

## 7. Future Improvements

1.  **Dynamic Difficulty Adjustment**: Currently, the retry uses the same difficulty. Future versions could lower the difficulty for remediation attempts.
2.  **Content Injection**: We could inject specific learning resources (Markdown/Video) into the `TaskInstance` payload during a remediation retry.
3.  **Mentor Intervention**: If a user fails 3 times, trigger a notification for a human mentor.

---

## 8. Glossary

- **Remediation**: The process of retrying a failed skill to prove competency.
- **Slot**: A bucket for a skill.
- **Task Instance**: A specific exercise generated for a slot.
- **Roadmap**: The complete graph of skills a user must master.
