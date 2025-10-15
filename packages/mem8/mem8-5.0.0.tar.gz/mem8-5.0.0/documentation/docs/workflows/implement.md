---
sidebar_position: 3
---

# Phase 3: Implement with `/m8-implement`
Execute the plan with full context, checking off steps as you go.

### Implementation Flow

```mermaid
stateDiagram-v2
    [*] --> ReadPlan: /m8-implement path/to/plan.md
    ReadPlan --> ReadFiles: Read all mentioned files fully
    ReadFiles --> CreateTodos: Create todo list from checkboxes
    CreateTodos --> Implement: Start implementing

    Implement --> CheckSuccess: Complete a phase
    CheckSuccess --> UpdatePlan: Update checkboxes in plan
    UpdatePlan --> NextPhase: Move to next phase
    NextPhase --> Implement: Continue

    Implement --> Problem: Issue found
    Problem --> Ask: Present mismatch to user
    Ask --> Implement: User provides guidance

    NextPhase --> [*]: All phases complete
```

### Key Behaviors

**Plan-Aware Implementation:**
- Reads plan and understands context
- Trusts completed checkboxes (resumable)
- Updates plan file as work progresses
- Asks for guidance when reality differs from plan

**Success Criteria:**
- Runs tests after each phase
- Fixes issues before proceeding
- Maintains forward momentum
