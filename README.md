# SkillForgeAI — Invariant-Driven Adaptive Learning System

SkillForgeAI is not a generic "AI learning app." It is an **invariant-driven adaptive learning system** that models a learner's evolving skill state, generates constrained roadmaps, and orchestrates AI-evaluated tasks while preserving **roadmap consistency, phase correctness, and skill-vector integrity** under retries, failures, and remediation.

This project was designed to solve the hard systems problems most AI learning platforms ignore:  
**State corruption, unreliable AI output, non-deterministic evaluation, and uncontrolled progression.**

---

## Executive Summary

SkillForgeAI implements a full end-to-end learning control system:

- A strict **Roadmap State Engine** with immutable transitions  
- A **slot-based execution model** governing task lifecycle  
- A **unified AI evaluation pipeline** with contract-enforced outputs  
- A **skill-delta engine** that updates learner state only on genuine attempts  
- A **domain validator layer** that enforces all system invariants before persistence  

Every roadmap mutation, task resolution, and phase transition is **schema-validated, invariant-checked, and version-controlled.**

This system is engineered to remain correct even when:
- AI responses are malformed
- Users retry or abandon tasks
- Evaluations contradict expectations
- Or partial failures occur

---

## The Core Problem

Most "AI learning platforms" are thin CRUD apps wrapped around LLM calls.

They fail because they:
- Trust non-deterministic AI output  
- Allow uncontrolled progression  
- Mutate roadmap state freely  
- Lose consistency under retries  
- Cannot guarantee learning correctness  

SkillForgeAI was built to explicitly solve:
1. **How do you evolve a learner's roadmap without breaking phase logic?** 2. **How do you evaluate tasks with AI while enforcing deterministic contracts?** 3. **How do you update skill state only from valid, verified attempts?** 4. **How do you prevent roadmap corruption under concurrent actions?**

The answer is not "more prompts."  
The answer is **systems engineering.**

---

## System Architecture

SkillForgeAI is organized as a layered control system:

```text
Client (Next.js)
  ↓
API Layer (FastAPI routers)
  ↓
Application Services
  ↓
Domain Layer (Authoritative)
  ↓
Invariant Validator
  ↓
Persistence (MongoDB)
```

### Core Subsystems:
- **Roadmap State Engine** — authoritative learning state
- **Slot Lifecycle Controller** — governs task execution
- **Evaluation Orchestrator** — routes submissions to strict evaluators
- **AI Adapter Layer** — isolates all model interactions
- **Skill Delta Engine** — computes bounded, normalized updates
- **Domain Validator** — blocks illegal state transitions
- **Repository Layer** — persistence with post-mutation validation

All mutations flow through the domain layer and are rejected if **any invariant is violated.**

---

## Core Architectural Components

### 1. Roadmap State Engine
- Immutable roadmap contract
- Phase → slot → task instance hierarchy
- Versioned mutations
- Deterministic phase transitions
- Locking and remediation support

### 2. Slot Lifecycle Controller
- Enforces: `idle` → `in_progress` → `completed/locked`
- Prevents parallel execution conflicts
- Guarantees one active slot at a time
- Tracks attempt history and resolution paths

### 3. Unified Evaluation Pipeline
- Routes MCQ, coding, and explanation tasks
- Strict JSON-only AI responses
- Sanitization and schema enforcement
- Context-aware evaluation prompts
- Pass/fail coherence checks

### 4. Skill Delta Engine
- Converts evaluation results into bounded deltas
- Normalizes floating-point instability
- Clamps values to domain limits
- Applies updates only after validator approval

### 5. Domain Validator Layer
The most critical system component.

Before any roadmap is persisted, the validator enforces:
- Roadmap structural integrity  
- Slot state correctness  
- Phase completion rules  
- Task resolution consistency  
- Skill-vector bounds  
- Timestamp monotonicity  

If any rule fails, the mutation is rejected.

---

## System Invariants (Guarantees)

SkillForgeAI enforces hard guarantees, including:
- A roadmap can only evolve through validated transitions  
- A slot cannot complete without evaluated task instances  
- Only one slot may be active at any time  
- Phase completion is deterministic  
- Skill vectors only update on genuine attempts  
- Failed or malformed AI output cannot corrupt state  
- All roadmap persistence is post-validation  

These invariants are enforced at the **domain level**, not in the UI.

---

## Failure Handling & Governance

SkillForgeAI explicitly models failure:
- Malformed AI responses are rejected and retried
- Evaluation inconsistencies are blocked
- Weak performance triggers remediation slots
- Locked slots prevent premature advancement
- Re-attempts do not overwrite historical state
- Skill updates are applied only after validator approval

This transforms AI from a trusted oracle into a **constrained subsystem.**

---

## Technology Stack

### Backend
- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Validation:** Pydantic (strict domain models)
- **Database:** MongoDB (Motor)
- **Auth:** JWT authentication
- **AI:** LangChain adapters, Google GenAI / Groq
- **Testing:** Pytest

### Frontend
- **Framework:** Next.js (App Router)
- **Library:** React
- **Styling:** Tailwind CSS
- **Network:** Axios

The frontend is intentionally thin.  
The backend is the source of truth.

---

## Project Structure

```bash
backend/
├── app/
│   ├── ai/          # model adapters, prompt isolation
│   ├── api/         # HTTP layer only
│   ├── core/        # config, logging, exceptions
│   ├── domain/      # authoritative business logic
│   ├── services/    # orchestration layer
│   ├── schemas/     # strict Pydantic contracts
│   ├── db/          # repositories and persistence
│   └── utils/       # helpers
└── tests/           # deterministic system tests

frontend/
├── app/
├── components/
├── services/
└── store/
```

Domain logic never depends on HTTP, UI, or AI providers.

---

## Why This Project Is Hard

- Non-deterministic AI output under strict system guarantees  
- Invariant-preserving roadmap evolution  
- Multi-layer validation before persistence  
- Adaptive task injection under phase constraints  
- Failure-first system design  
- Floating-point stability in skill modeling  

SkillForgeAI is engineered as a **state machine**, not a feature app.

---

## Setup Instructions

### Backend
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
npm install
npm run dev
```

---

## Roadmap

- [ ] Architecture diagrams & lifecycle visuals
- [ ] Public demo deployment
- [ ] Observability dashboard
- [ ] Stress testing and adversarial simulation
- [ ] Multi-track learning engines

---

## Author

Built and architected by **Mohamed Fateen** Focus: backend systems, invariant design, and AI governance.

## License

MIT
