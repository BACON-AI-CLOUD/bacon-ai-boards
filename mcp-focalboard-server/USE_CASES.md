# Focalboard MCP Server: 30 Use Cases

## Overview
This document describes 30 use cases for the Focalboard MCP Server with BACON-AI 12-Phase template support, covering both happy paths (normal operation) and unhappy paths (error handling).

---

## Happy Path Use Cases (26)

### Template Operations
| # | Use Case | Description | Tools Used |
|---|----------|-------------|------------|
| 1 | Template Tracking Setup | Link a board to its source template for version tracking | `focalboard_set_board_tracking`, `focalboard_get_board_tracking` |
| 2 | List Templates | Discover available templates in the template directory | `focalboard_list_templates` |
| 3 | Get Template Details | View full template configuration including phases and tasks | `focalboard_get_template` |
| 4 | Get Template JSON | Retrieve template in machine-readable format | `focalboard_get_template(response_format=JSON)` |
| 5 | List by Category | Filter templates by category (framework, sprint, project) | `focalboard_list_templates(category=...)` |

### Board Creation & Management
| # | Use Case | Description | Tools Used |
|---|----------|-------------|------------|
| 6 | Create Board from Template | Instantiate a new project board from a template | `focalboard_instantiate_template` |
| 7 | Sync Dry Run | Preview differences between board and template | `focalboard_sync_template(dry_run=True)` |
| 8 | List with Pagination | Navigate large card sets with pagination | `focalboard_list_cards(limit, offset)` |
| 9 | Board Statistics | Get status distribution and progress metrics | `focalboard_get_board_statistics` |
| 10 | Search by Title | Find cards matching a search query | `focalboard_search_cards` |

### Phase-Based Operations
| # | Use Case | Description | Tools Used |
|---|----------|-------------|------------|
| 11 | Get Phase Tasks | List all tasks in a specific BACON-AI phase | `focalboard_get_phase_tasks` |
| 12 | Filter by Phase | View tasks filtered by phase number | `focalboard_get_phase_tasks(phase_number=5)` |
| 13 | Phase Agent Context | Get complete context for sub-agent injection | `focalboard_get_phase_agent_context` |

### Deterministic Workflow Execution
| # | Use Case | Description | Tools Used |
|---|----------|-------------|------------|
| 14 | Phase 0 Execution | Execute Verification Protocol phase | `focalboard_get_phase_agent_context`, `focalboard_update_card_properties` |
| 15 | Phase 1 Execution | Execute Empathetic Problem Definition | `focalboard_get_phase_agent_context`, `focalboard_update_card_properties` |
| 16 | Phase 2 Execution | Execute Data Gathering phase | `focalboard_get_phase_agent_context`, `focalboard_update_card_properties` |

### Agent Context for All Phases (21-30)
| # | Phase | Leader | Use Case |
|---|-------|--------|----------|
| 21 | 3 | George (Systems Architect) | Systematic Analysis & Insights |
| 22 | 4 | Finn (Innovation Engineer) | Creative Solution Generation |
| 23 | 5 | Perspective Analyst | Systematic Solution Evaluation |
| 24 | 6 | Elisabeth (Orchestrator) | Consensus & Solution Selection |
| 25 | 7 | Giuseppe (Documentation) | Design Excellence (WRICEF) |
| 26 | 8 | Elisabeth + Lily | Implementation Planning |
| 27 | 9 | Lily (Quality Assurance) | Build → Test (TDD) |
| 28 | 10 | Elisabeth + Connor | Go-Live Prep & Change Management |
| 29 | 11 | Connor (DevOps) | Production Deployment |
| 30 | 12 | SE-Agent Observer | Reflection & Learning (SSC) |

---

## Unhappy Path Use Cases (4)

| # | Use Case | Description | Expected Behavior |
|---|----------|-------------|-------------------|
| 7 | Invalid Board ID | Request tracking for non-existent board | Returns clear "not found" error |
| 8 | Invalid Template ID | Request non-existent template | Returns "template not found" message |
| 9 | Phase Out of Range | Request phase number > 12 | Validation error or empty result |
| 10 | Sync Non-matching Template | Sync board with wrong template | Returns "not found" error |

---

## Deterministic Workflow Pattern

### Sub-Agent Orchestration Flow
```
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN ORCHESTRATOR AGENT                       │
│  (Elisabeth - Manages overall workflow and handoffs)             │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Phase 0     │   │   Phase 1     │   │   Phase 2     │
│  Sub-Agent    │──▶│  Sub-Agent    │──▶│  Sub-Agent    │──▶ ...
│  (Research)   │   │  (Elisabeth)  │   │  (Research)   │
└───────────────┘   └───────────────┘   └───────────────┘
```

### Handoff Protocol
1. **Orchestrator** calls `focalboard_get_phase_agent_context(phase_number=N)`
2. **Orchestrator** spawns sub-agent with returned context as system prompt
3. **Sub-Agent** executes phase tasks:
   - Updates task status to "In Progress"
   - Completes work
   - Updates status to "Completed"
   - Documents findings
4. **Sub-Agent** returns completion report to orchestrator
5. **Orchestrator** advances to Phase N+1

### Context Injection Example
```python
# Orchestrator gets context for Phase 4
context = await focalboard_get_phase_agent_context(
    board_id="bd5mw98s3cjftjnef77q8c4oone",
    phase_number=4
)

# Spawn sub-agent with context
sub_agent = Task(
    subagent_type="bacon-ai-innovation-engineer",
    prompt=f"""
    {context}

    Execute all pending tasks in this phase and report back when complete.
    """,
    description="Phase 4: Creative Solution Generation"
)
```

---

## Test Results Summary

```
📊 Results:
   Happy Paths:   25/26 passed
   Unhappy Paths: 4/4 passed
   Total:         29/30 passed (96.7%)
```

### Notes
- Template tracking via board properties requires Focalboard API enhancement
- Current workaround: Use template's `instances` array for tracking
- All core workflow functionality is operational
