#!/usr/bin/env python3
"""
Complete BACON-AI Task Update with:
1. Due dates (project starts 01.02.2026)
2. Comprehensive descriptions with deterministic control
3. Self-annealing instructions for AI agents
4. Detailed checklists with subtasks
5. Comments with execution context
"""

import asyncio
import httpx
import time
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Configuration
FOCALBOARD_URL = "http://localhost:8000"
AUTH_TOKEN = "k77tg84g87pd6tjk7rdho1kqs9h"
BOARD_ID = "bd5mw98s3cjftjnef77q8c4oone"

# Property IDs
NUMBER_PROP_ID = "a5p9bpedehti9yph1uuehqighue"
STATUS_PROP_ID = "a972dc7a-5f4c-45d2-8044-8c28c69717f1"
PRIORITY_PROP_ID = "d3d682bf-e074-49d9-8df5-7320921c2d23"
HOURS_PROP_ID = "a8daz81s4xjgke1ww6cwik5w7ye"
DUE_DATE_PROP_ID = "a3zsw7xs8sxy7atj8b6totp3mby"

# Status options
STATUS_NOT_STARTED = "ayz81h9f3dwp7rzzbdebesc7ute"
STATUS_IN_PROGRESS = "ar6b8m3jxr3asyxhr8iucdbo6yc"
STATUS_BLOCKED = "afi4o5nhnqc3smtzs1hs3ij34dh"
STATUS_COMPLETED = "adeo5xuwne3qjue83fcozekz8ko"

# Priority options
PRIORITY_HIGH = "d3bfb50f-f569-4bad-8a3a-dd15c3f60101"
PRIORITY_MEDIUM = "87f59784-b859-4c24-8ebe-17c766e081dd"
PRIORITY_LOW = "98a57627-0f76-471d-850d-91f3ed9fd213"

# Project start date
PROJECT_START = datetime(2026, 2, 1)

def get_headers():
    return {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

def generate_block_id():
    """Generate a valid Focalboard block ID."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(27))

# Phase definitions with durations (in days) and detailed info
PHASES = {
    "P0000": {
        "name": "Verification",
        "duration_days": 2,
        "methodology": "Critical Pre-Phase",
        "description": "MANDATORY gate before ANY work begins. Prevents reinventing the wheel.",
        "skills": ["/lessons-learned", "/cross-model-consultation", "/groq-chat"],
        "tools": ["mcp__mcp-bacon-memory__memory_query_proven_approaches", "WebSearch", "mcp__groq-chat__*"],
    },
    "P0001": {
        "name": "Problem Definition",
        "duration_days": 3,
        "methodology": "Design Thinking",
        "description": "Apply Design Thinking to deeply understand the problem from multiple perspectives.",
        "skills": ["/triz-innovation", "/bacon-ai-perspective-analyst", "/bacon-ai-human-experience"],
        "tools": ["mcp__mcp-bacon-memory__*", "mcp__mcp-etherpad-hub__*", "mcp__ai-reasoning__*"],
    },
    "P0002": {
        "name": "Data Gathering",
        "duration_days": 4,
        "methodology": "Systems Thinking",
        "description": "Collect and organize all relevant data using systems thinking approach.",
        "skills": ["/lessons-learned", "/documentation-writer"],
        "tools": ["WebSearch", "WebFetch", "mcp__mcp-bacon-memory__*"],
    },
    "P0003": {
        "name": "Analysis",
        "duration_days": 5,
        "methodology": "TRIZ + Systems Thinking",
        "description": "Deep analysis using TRIZ contradiction matrix and systems thinking.",
        "skills": ["/triz-innovation", "/bacon-ai-systems-architect"],
        "tools": ["mcp__ai-reasoning__*", "mcp__mcp-bacon-memory__*"],
    },
    "P0004": {
        "name": "Solution Generation",
        "duration_days": 4,
        "methodology": "TRIZ 40 Principles",
        "description": "Generate 20+ solutions using TRIZ inventive principles. NO EVALUATION allowed.",
        "skills": ["/triz-innovation", "/parallel-swarm-orchestrator", "/autogen-orchestrator"],
        "tools": ["mcp__bacon-swarm-orchestrator__*", "mcp__ai-reasoning__*"],
    },
    "P0005": {
        "name": "Evaluation",
        "duration_days": 4,
        "methodology": "Multi-Criteria Analysis",
        "description": "Evaluate solutions using weighted scoring and Six Thinking Hats.",
        "skills": ["/bacon-ai-perspective-analyst", "/triz-innovation"],
        "tools": ["mcp__ai-reasoning__*", "mcp__mcp-bacon-memory__*"],
    },
    "P0006": {
        "name": "Consensus Voting",
        "duration_days": 2,
        "methodology": "Multi-Model + Human",
        "description": "Collect votes from AI agents and human stakeholder for final decision.",
        "skills": ["/cross-model-consultation", "/groq-chat"],
        "tools": ["mcp__openai-chat__*", "mcp__gemini-chat__*", "mcp__groq-chat__*", "mcp__ai-reasoning__consensus_analysis"],
    },
    "P0007": {
        "name": "Design Excellence",
        "duration_days": 6,
        "methodology": "Architecture",
        "description": "Create detailed architecture with ADRs, diagrams, and quality attributes.",
        "skills": ["/bacon-ai-systems-architect", "/documentation-writer"],
        "tools": ["mcp__mcp-etherpad-hub__*", "mcp__mcp-bacon-memory__*"],
    },
    "P0008": {
        "name": "Implementation Planning",
        "duration_days": 4,
        "methodology": "Execution",
        "description": "Create WBS, Gantt chart, resource allocation, and risk mitigation plan.",
        "skills": ["/documentation-writer", "/bacon-ai-deterministic-framework"],
        "tools": ["mcp__mcp-bacon-memory__*"],
    },
    "P0009": {
        "name": "TDD Build",
        "duration_days": 10,
        "methodology": "Test-Driven Development",
        "description": "Build using RED-GREEN-REFACTOR cycle with V-Model test progression.",
        "skills": ["/test-strategist", "/code-reviewer", "/bacon-evolutionary-coding"],
        "tools": ["Bash", "Read", "Write", "Edit", "mcp__mcp-bacon-memory__*"],
    },
    "P0010": {
        "name": "Change Management",
        "duration_days": 4,
        "methodology": "User Adoption",
        "description": "Create training materials, demos, and execute communication plan.",
        "skills": ["/documentation-writer", "/bacon-ai-marketing-officer"],
        "tools": ["mcp__mcp-etherpad-hub__*", "mcp__edge-tts__*"],
    },
    "P0011": {
        "name": "Deployment",
        "duration_days": 3,
        "methodology": "Production Rollout",
        "description": "Deploy with health checks, monitoring, smoke tests, and UAT approval.",
        "skills": ["/infrastructure-admin", "/server-admin-local"],
        "tools": ["Bash", "mcp__mcp-bacon-memory__*"],
    },
    "P0012": {
        "name": "SSC Retrospective",
        "duration_days": 2,
        "methodology": "Learning",
        "description": "Stop/Start/Continue retrospective with lessons learned documentation.",
        "skills": ["/lessons-learned", "/bacon-memory-manager"],
        "tools": ["mcp__mcp-bacon-memory__memory_store_proven_approach", "mcp__mcp-bacon-memory__memory_log_lesson_learned"],
    },
}

# Subtask definitions per phase with hours
SUBTASKS = {
    "P0000": [
        ("T0001", "Query lessons learned database", 2, PRIORITY_HIGH),
        ("T0002", "Web search current best practices", 3, PRIORITY_HIGH),
        ("T0003", "Consult external AI models", 3, PRIORITY_HIGH),
        ("T0004", "Document current state and assumptions", 4, PRIORITY_HIGH),
        ("T0005", "Validate problem not already solved", 2, PRIORITY_HIGH),
    ],
    "P0001": [
        ("T0001", "Create empathy map", 4, PRIORITY_HIGH),
        ("T0002", "Define problem using 5W+1H framework", 3, PRIORITY_HIGH),
        ("T0003", "Apply Six Thinking Hats review", 4, PRIORITY_MEDIUM),
        ("T0004", "Document success criteria and constraints", 4, PRIORITY_HIGH),
        ("T0005", "Get stakeholder approval", 3, PRIORITY_HIGH),
    ],
    "P0002": [
        ("T0001", "Create context map of system boundaries", 5, PRIORITY_HIGH),
        ("T0002", "Conduct stakeholder analysis", 4, PRIORITY_HIGH),
        ("T0003", "Collect data from all sources", 6, PRIORITY_HIGH),
        ("T0004", "Review existing documentation", 4, PRIORITY_MEDIUM),
        ("T0005", "Identify data gaps and plan collection", 4, PRIORITY_HIGH),
    ],
    "P0003": [
        ("T0001", "Create causal loop diagrams", 6, PRIORITY_HIGH),
        ("T0002", "Apply TRIZ contradiction matrix", 6, PRIORITY_HIGH),
        ("T0003", "Identify patterns from data", 6, PRIORITY_HIGH),
        ("T0004", "Deep analysis (mindmaps, diagrams)", 6, PRIORITY_MEDIUM),
        ("T0005", "QA review with confidence levels", 6, PRIORITY_HIGH),
    ],
    "P0004": [
        ("T0001", "Apply TRIZ 40 Inventive Principles", 6, PRIORITY_HIGH),
        ("T0002", "Parallel agent generation (5-10 agents)", 6, PRIORITY_HIGH),
        ("T0003", "Collective discussion for more ideas", 4, PRIORITY_MEDIUM),
        ("T0004", "Compile master solution list (min 20)", 4, PRIORITY_HIGH),
        ("T0005", "Enforce NO EVALUATION rule", 2, PRIORITY_HIGH),
    ],
    "P0005": [
        ("T0001", "Apply feasibility filtering", 4, PRIORITY_HIGH),
        ("T0002", "Create multi-criteria scoring matrix", 6, PRIORITY_HIGH),
        ("T0003", "Apply Six Thinking Hats (Yellow/Black)", 4, PRIORITY_MEDIUM),
        ("T0004", "Conduct weighted voting by agents", 4, PRIORITY_HIGH),
        ("T0005", "Identify top 3 solutions with scores", 4, PRIORITY_HIGH),
    ],
    "P0006": [
        ("T0001", "Collect votes from BACON-AI agents", 3, PRIORITY_HIGH),
        ("T0002", "Consult external AI models", 3, PRIORITY_HIGH),
        ("T0003", "Get human vote (final authority)", 2, PRIORITY_HIGH),
        ("T0004", "Calculate consensus percentage", 2, PRIORITY_MEDIUM),
        ("T0005", "Apply decision rules", 3, PRIORITY_HIGH),
    ],
    "P0007": [
        ("T0001", "Create Architecture Decision Records", 8, PRIORITY_HIGH),
        ("T0002", "Draw system architecture diagrams", 10, PRIORITY_HIGH),
        ("T0003", "Define component responsibilities", 6, PRIORITY_HIGH),
        ("T0004", "Identify design patterns to apply", 6, PRIORITY_MEDIUM),
        ("T0005", "Specify quality attributes", 8, PRIORITY_HIGH),
    ],
    "P0008": [
        ("T0001", "Create Work Breakdown Structure", 6, PRIORITY_HIGH),
        ("T0002", "Create dependency graph (Gantt)", 5, PRIORITY_HIGH),
        ("T0003", "Allocate resources (team, tools)", 4, PRIORITY_HIGH),
        ("T0004", "Document risk mitigation plan", 5, PRIORITY_HIGH),
        ("T0005", "Define success criteria & acceptance", 5, PRIORITY_HIGH),
    ],
    "P0009": [
        ("T0001", "Establish test baseline", 6, PRIORITY_HIGH),
        ("T0002", "RED: Write failing tests first", 16, PRIORITY_HIGH),
        ("T0003", "GREEN: Write code to pass tests", 24, PRIORITY_HIGH),
        ("T0004", "REFACTOR: Improve code quality", 16, PRIORITY_MEDIUM),
        ("T0005", "V-Model progression (TUT→FUT→SIT→UAT)", 12, PRIORITY_HIGH),
        ("T0006", "Verify >90% code coverage", 4, PRIORITY_HIGH),
    ],
    "P0010": [
        ("T0001", "Create user training materials", 8, PRIORITY_HIGH),
        ("T0002", "Prepare demo video/walkthrough", 6, PRIORITY_MEDIUM),
        ("T0003", "Set up feedback collection", 3, PRIORITY_HIGH),
        ("T0004", "Execute communication plan", 5, PRIORITY_HIGH),
        ("T0005", "Track adoption metrics", 4, PRIORITY_HIGH),
    ],
    "P0011": [
        ("T0001", "Complete pre-deployment checklist", 3, PRIORITY_HIGH),
        ("T0002", "Run deployment automation", 6, PRIORITY_HIGH),
        ("T0003", "Execute health checks", 3, PRIORITY_HIGH),
        ("T0004", "Verify monitoring and alerting", 4, PRIORITY_HIGH),
        ("T0005", "Run smoke tests in production", 3, PRIORITY_HIGH),
        ("T0006", "Get UAT approval", 4, PRIORITY_HIGH),
    ],
    "P0012": [
        ("T0001", "Collect human feedback", 2, PRIORITY_HIGH),
        ("T0002", "Run agent SSC (Stop/Start/Continue)", 3, PRIORITY_HIGH),
        ("T0003", "Update SE-Agent trajectory memory", 2, PRIORITY_HIGH),
        ("T0004", "Add lessons to database (min 3)", 2, PRIORITY_HIGH),
        ("T0005", "Document proven patterns (min 4)", 2, PRIORITY_HIGH),
        ("T0006", "Assess organizational impact", 2, PRIORITY_MEDIUM),
        ("T0007", "Execute dissemination plan", 2, PRIORITY_MEDIUM),
    ],
}

def calculate_due_dates() -> Dict[str, datetime]:
    """Calculate due dates for all phases and tasks."""
    due_dates = {}
    current_date = PROJECT_START

    for phase_id in sorted(PHASES.keys()):
        phase = PHASES[phase_id]
        phase_duration = phase["duration_days"]
        phase_end = current_date + timedelta(days=phase_duration)

        # Phase header due date (end of phase)
        due_dates[f"{phase_id}-0000"] = phase_end

        # Calculate subtask due dates within phase
        subtasks = SUBTASKS.get(phase_id, [])
        if subtasks:
            total_hours = sum(s[2] for s in subtasks)
            hours_per_day = total_hours / phase_duration

            task_start = current_date
            for task_id, _, hours, _ in subtasks:
                task_duration = max(1, hours / hours_per_day)
                task_end = task_start + timedelta(days=task_duration)
                due_dates[f"{phase_id}-{task_id}"] = min(task_end, phase_end)
                task_start = task_end

        current_date = phase_end

    return due_dates


def generate_phase_description(phase_id: str, phase: Dict) -> str:
    """Generate comprehensive phase description with deterministic control."""
    phase_num = phase_id[-2:].lstrip("0") or "0"

    return f"""# Phase {phase_num}: {phase['name']} ({phase['methodology']})

## 🎯 PURPOSE
{phase['description']}

## 🤖 PHASE LEAD AGENT SYSTEM PROMPT
```
You are the BACON-AI Phase {phase_num} Lead Agent.
Phase ID: {phase_id}-0000
Methodology: {phase['methodology']}

AUTHORITY LEVEL: Phase Gate Controller
- Can BLOCK progression to Phase {int(phase_num)+1}
- Must ensure ALL subtasks complete with GREEN status
- Responsible for phase-level lessons learned

DETERMINISTIC EXECUTION PROTOCOL:
1. VERIFY previous phase completion (Phase {int(phase_num)-1} if applicable)
2. LOAD all outputs from previous phase
3. BRIEF team on phase objectives and constraints
4. MONITOR subtask execution and dependencies
5. RESOLVE blockers and escalate if needed
6. VALIDATE all subtask outputs meet quality standards
7. LOG phase lessons to bacon-memory
8. GATE CHECK before allowing Phase {int(phase_num)+1}

SELF-ANNEALING BEHAVIOR:
- On ERROR: Query bacon-memory for similar errors
- On SUCCESS: Store proven approach for future use
- On COMPLETION: Update SE-Agent trajectory memory
- ALWAYS: Log decisions with rationale for learning
```

## 📋 PHASE DEPENDENCIES
- **Blocks**: Phase {int(phase_num)+1} (Cannot start until this phase completes)
- **Blocked By**: Phase {int(phase_num)-1} (Must complete before this starts)

## 🔧 REQUIRED MCP TOOLS
{chr(10).join(f"- `{tool}`" for tool in phase['tools'])}

## 📚 SKILLS TO LOAD
{chr(10).join(f"- `{skill}`" for skill in phase['skills'])}

## ⚡ PARALLEL EXECUTION RULES
Subtasks within this phase may run in parallel ONLY if:
1. No data dependency exists between them
2. Resource constraints allow parallel execution
3. Output quality is not compromised

## 🔄 SELF-ANNEALING CHECKPOINT
At phase completion, execute:
```python
# Store proven approach
mcp__mcp-bacon-memory__memory_store_proven_approach(
    content="{phase_id}-0000 Phase {phase_num} ({phase['name']}): [SUMMARY]. "
            "Key decisions: [DECISIONS]. Outcomes: [OUTCOMES]",
    tags=["phase-{phase_num}", "{phase['methodology'].lower().replace(' ', '-')}", "bacon-ai"],
    verification_count=1
)

# Log lesson learned
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Phase {phase_num} complete. What worked: [WHAT_WORKED]. "
            "What didn't: [WHAT_DIDNT]. Improvements: [IMPROVEMENTS]",
    severity="info",
    context="{phase_id}-0000 {phase['name']}"
)
```

## 🚦 PHASE GATE CRITERIA
Before proceeding to next phase, ALL must be true:
- [ ] All subtasks show COMPLETED status
- [ ] No BLOCKED tasks remain
- [ ] All outputs documented and validated
- [ ] Lessons learned logged to bacon-memory
- [ ] Stakeholder approval obtained (if required)
- [ ] Phase retrospective completed
"""


def generate_task_description(phase_id: str, task_id: str, task_name: str, hours: int, phase: Dict) -> str:
    """Generate comprehensive task description with deterministic control."""
    phase_num = phase_id[-2:].lstrip("0") or "0"
    task_num = task_id[-4:].lstrip("0") or "0"
    full_task_id = f"{phase_id}-{task_id}"

    # Get previous and next tasks
    subtasks = SUBTASKS.get(phase_id, [])
    task_index = next((i for i, t in enumerate(subtasks) if t[0] == task_id), 0)
    prev_task = subtasks[task_index - 1][0] if task_index > 0 else None
    next_task = subtasks[task_index + 1][0] if task_index < len(subtasks) - 1 else None

    # Determine parallel tasks
    parallel_tasks = []
    if task_index > 0 and task_index < len(subtasks) - 1:
        parallel_tasks = [t[0] for i, t in enumerate(subtasks) if i != task_index and i > 0 and i < len(subtasks) - 1]

    return f"""# Task: {task_name}

## 🎯 OBJECTIVE
Execute this task as part of Phase {phase_num}: {phase['name']} ({phase['methodology']}).
Estimated effort: {hours} hours.

## 🤖 AGENT SYSTEM PROMPT
```
You are a BACON-AI Task Execution Agent.
Task ID: {full_task_id}
Phase: {phase_num} - {phase['name']}
Methodology: {phase['methodology']}

EXECUTION AUTHORITY:
- Execute task within defined scope
- Request clarification if requirements unclear
- Escalate blockers to Phase Lead
- Log all decisions and outcomes

DETERMINISTIC EXECUTION SEQUENCE:
1. VERIFY prerequisites
   {"- Wait for " + f"{phase_id}-{prev_task}" + " to complete" if prev_task else "- No prior task dependency"}
   - Confirm required inputs available
   - Check resource availability

2. QUERY lessons learned
   ```python
   mcp__mcp-bacon-memory__memory_query_proven_approaches(
       query="{task_name}",
       tags=["phase-{phase_num}", "{phase['methodology'].lower().replace(' ', '-')}"],
       min_verification_count=0
   )
   ```

3. EXECUTE task steps (see checklist below)

4. VALIDATE outputs
   - Meet acceptance criteria
   - Quality standards satisfied
   - Documentation complete

5. PREPARE handoff
   {"- Notify " + f"{phase_id}-{next_task}" + " ready to start" if next_task else "- Notify Phase Lead of completion"}
   - Update task status
   - Log lessons learned

SELF-ANNEALING BEHAVIOR:
- On ERROR:
  1. Query bacon-memory: "error {task_name}"
  2. If solution found: Apply and continue
  3. If not found: Log error, try alternative, escalate if needed

- On SUCCESS:
  1. Document what worked
  2. Store proven approach if novel
  3. Update task confidence score

- On BLOCKED:
  1. Document blocker details
  2. Query bacon-memory for similar blockers
  3. Notify Phase Lead with proposed solutions
```

## 📋 TASK DEPENDENCIES
- **Blocks**: {f"{phase_id}-{next_task}" if next_task else "Phase completion"}
- **Blocked By**: {f"{phase_id}-{prev_task}" if prev_task else "Phase start"}
- **Can Parallel With**: {", ".join([f"{phase_id}-{t}" for t in parallel_tasks[:3]]) if parallel_tasks else "None (sequential dependency)"}

## 🔧 REQUIRED MCP TOOLS
{chr(10).join(f"- `{tool}`" for tool in phase['tools'][:4])}

## 📚 SKILLS TO REFERENCE
{chr(10).join(f"- `{skill}`" for skill in phase['skills'][:3])}

## 🔄 PARALLEL AGENT PROMPT
While executing primary task, spawn parallel agents for:
1. Pre-fetch documentation for next task ({f"{phase_id}-{next_task}" if next_task else "Phase summary"})
2. Monitor for blocking issues and prepare mitigations
3. Prepare handoff summary as work progresses
4. Cache relevant resources for dependent tasks

```python
# Example parallel agent spawn
Task(
    subagent_type="general-purpose",
    description="Prepare {next_task if next_task else 'phase summary'}",
    prompt="While primary agent works on {task_name}, prepare inputs for next step..."
)
```

## 📝 LESSON LEARNED TEMPLATE
Execute at task completion:
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="{full_task_id} ({task_name}): "
            "Completed in [ACTUAL_HOURS]h (estimated {hours}h). "
            "Key insight: [KEY_INSIGHT]. "
            "What worked: [WHAT_WORKED]. "
            "Improvement: [IMPROVEMENT]",
    severity="info",
    context="{full_task_id} Phase {phase_num}"
)
```

## ✅ SUCCESS CRITERIA
Task is COMPLETE when ALL are true:
- [ ] Prerequisites verified and satisfied
- [ ] All execution steps completed in order
- [ ] Outputs documented with evidence
- [ ] Quality standards met (no rework needed)
- [ ] Handoff notes prepared for next task
- [ ] Lesson learned logged to bacon-memory
- [ ] Status updated to COMPLETED
"""


def generate_phase_checklist(phase_id: str, phase: Dict) -> List[str]:
    """Generate checklist for phase header."""
    phase_num = phase_id[-2:].lstrip("0") or "0"
    prev_phase = int(phase_num) - 1

    checklist = [
        f"🚦 GATE IN: Confirm Phase {prev_phase} complete (if applicable)" if prev_phase >= 0 else "🚦 GATE IN: Project kickoff confirmed",
        f"📥 Load Phase {prev_phase} outputs and lessons learned" if prev_phase >= 0 else "📥 Load project charter and initial context",
        f"👥 Brief team on Phase {phase_num} objectives",
        "📋 Verify all resources available",
    ]

    # Add subtask references
    subtasks = SUBTASKS.get(phase_id, [])
    for task_id, task_name, _, _ in subtasks:
        checklist.append(f"⬜ Execute {phase_id}-{task_id}: {task_name}")

    checklist.extend([
        "📊 Validate all subtask outputs",
        "📝 Conduct phase retrospective",
        "📝 Log phase lessons to bacon-memory",
        "📝 Store proven approaches",
        f"🚦 GATE OUT: All criteria met for Phase {int(phase_num)+1}",
    ])

    return checklist


def generate_task_checklist(phase_id: str, task_id: str, task_name: str, phase: Dict) -> List[str]:
    """Generate detailed checklist for task."""
    full_task_id = f"{phase_id}-{task_id}"

    # Base checklist
    checklist = [
        "📥 INIT: Verify prerequisites complete",
        "🔍 Query bacon-memory for similar tasks/approaches",
        "📋 Review task requirements and constraints",
        "📖 Load relevant documentation and context",
    ]

    # Task-specific items based on task name
    if "Create" in task_name or "Draw" in task_name or "Write" in task_name:
        checklist.extend([
            f"📝 Create initial draft/outline for {task_name.lower()}",
            "📝 Complete full deliverable with all sections",
            "🔍 Self-review for completeness and accuracy",
            "👥 Peer review (if available)",
        ])
    elif "Apply" in task_name or "Execute" in task_name or "Run" in task_name:
        checklist.extend([
            "⚙️ Prepare inputs and configuration",
            f"⚙️ Execute: {task_name}",
            "📊 Capture outputs and metrics",
            "✅ Validate execution results",
        ])
    elif "Review" in task_name or "Verify" in task_name or "Check" in task_name:
        checklist.extend([
            "📋 Define review criteria and checklist",
            f"🔍 Execute: {task_name}",
            "📝 Document findings and issues",
            "📊 Assign confidence/quality scores",
        ])
    elif "Collect" in task_name or "Gather" in task_name or "Identify" in task_name:
        checklist.extend([
            "📍 Identify all relevant sources",
            f"📥 {task_name}",
            "📊 Organize and categorize findings",
            "✅ Validate completeness",
        ])
    elif "Define" in task_name or "Document" in task_name:
        checklist.extend([
            "📋 Review existing definitions/documentation",
            f"📝 {task_name}",
            "🔍 Validate against requirements",
            "👥 Get stakeholder input",
        ])
    elif "Get" in task_name and "approval" in task_name.lower():
        checklist.extend([
            "📄 Prepare approval package",
            "📧 Schedule review with stakeholders",
            "🎤 Present and address questions",
            "✅ Obtain explicit sign-off",
        ])
    else:
        checklist.extend([
            f"📋 Step 1: Analyze requirements for {task_name.lower()}",
            f"📋 Step 2: Execute {task_name.lower()}",
            "📋 Step 3: Validate results",
            "📋 Step 4: Document outcomes",
        ])

    # Standard completion items
    checklist.extend([
        "📝 Document all outputs with evidence",
        "📝 Prepare handoff notes for next task",
        "📝 Log lesson learned to bacon-memory",
        "📝 Update task status in Focalboard",
        f"✅ VERIFY: {full_task_id} meets all success criteria",
    ])

    return checklist


def generate_comment(phase_id: str, task_id: str, task_name: str, due_date: datetime, phase: Dict) -> str:
    """Generate comment with execution context."""
    full_task_id = f"{phase_id}-{task_id}" if task_id else f"{phase_id}-0000"
    phase_num = phase_id[-2:].lstrip("0") or "0"

    return f"""## Execution Context

**Task ID**: {full_task_id}
**Due Date**: {due_date.strftime('%Y-%m-%d')}
**Phase**: {phase_num} - {phase['name']}
**Methodology**: {phase['methodology']}

### Quick Reference

**Before Starting**:
```python
# Always query lessons learned first
mcp__mcp-bacon-memory__memory_query_proven_approaches(
    query="{task_name}",
    tags=["phase-{phase_num}"]
)
```

**On Completion**:
```python
# Log what you learned
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="{full_task_id}: [SUMMARY]",
    severity="info",
    context="{full_task_id}"
)
```

**On Error**:
```python
# Check if solution exists
mcp__mcp-bacon-memory__memory_query_proven_approaches(
    query="error {task_name}",
    tags=["troubleshooting"]
)
```

### AI Agent Notes
- Follow deterministic execution sequence
- Use self-annealing on errors
- Always document for future agents
- Parallel agents can prepare next steps
"""


async def main():
    print("=" * 70)
    print("BACON-AI Complete Task Update")
    print("Adding due dates, descriptions, and deterministic control")
    print(f"Project Start: {PROJECT_START.strftime('%Y-%m-%d')}")
    print("=" * 70)

    # Calculate all due dates
    due_dates = calculate_due_dates()

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Get all blocks
        blocks_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks"
        response = await client.get(blocks_url, headers=get_headers())

        if response.status_code != 200:
            print(f"Failed to get blocks: {response.status_code}")
            return

        blocks = response.json()

        # Find BACON-AI task cards
        task_cards = [b for b in blocks if b.get("type") == "card" and b.get("title", "").startswith("P0")]
        print(f"Found {len(task_cards)} BACON-AI task cards")

        updated = 0
        content_updated = 0

        for card in task_cards:
            card_id = card["id"]
            title = card["title"]
            title_parts = title.split(" ── ")
            task_id_full = title_parts[0]

            # Parse task ID
            if "-0000" in task_id_full:
                # Phase header
                phase_id = task_id_full.split("-")[0]
                task_id = None
                is_phase = True
            elif "-T" in task_id_full:
                # Subtask
                parts = task_id_full.split("-")
                phase_id = parts[0]
                task_id = parts[1]
                is_phase = False
            else:
                continue

            # Get phase info
            phase = PHASES.get(phase_id)
            if not phase:
                continue

            # Get due date
            due_date = due_dates.get(task_id_full)
            if not due_date:
                continue

            # Get task name
            task_name = title_parts[1] if len(title_parts) > 1 else ""

            # Get hours and priority from subtask definition
            if is_phase:
                hours = phase["duration_days"] * 8
                priority = PRIORITY_HIGH
            else:
                subtask_info = next((s for s in SUBTASKS.get(phase_id, []) if s[0] == task_id), None)
                if subtask_info:
                    hours = subtask_info[2]
                    priority = subtask_info[3]
                else:
                    hours = 4
                    priority = PRIORITY_MEDIUM

            # Update card properties
            current_props = card.get("fields", {}).get("properties", {})
            current_props[DUE_DATE_PROP_ID] = str(int(due_date.timestamp() * 1000))
            current_props[HOURS_PROP_ID] = str(hours)
            current_props[PRIORITY_PROP_ID] = priority
            current_props[STATUS_PROP_ID] = STATUS_NOT_STARTED

            patch_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks/{card_id}"
            patch_data = {
                "updatedFields": {
                    "properties": current_props
                }
            }

            patch_response = await client.patch(patch_url, headers=get_headers(), json=patch_data)

            if patch_response.status_code == 200:
                updated += 1
                print(f"✅ {task_id_full}: Due {due_date.strftime('%Y-%m-%d')}, {hours}h")

            # Delete existing content blocks
            existing_content = [b for b in blocks if b.get("parentId") == card_id and b.get("type") in ["text", "checkbox", "comment"]]
            for block in existing_content:
                await client.delete(f"{blocks_url}/{block['id']}", headers=get_headers())

            # Generate new content
            if is_phase:
                description = generate_phase_description(phase_id, phase)
                checklist = generate_phase_checklist(phase_id, phase)
            else:
                description = generate_task_description(phase_id, task_id, task_name, hours, phase)
                checklist = generate_task_checklist(phase_id, task_id, task_name, phase)

            comment = generate_comment(phase_id, task_id, task_name, due_date, phase)

            now = int(time.time() * 1000)
            new_blocks = []
            content_order = []

            # Description block
            desc_id = generate_block_id()
            new_blocks.append({
                "id": desc_id,
                "type": "text",
                "parentId": card_id,
                "boardId": BOARD_ID,
                "title": description,
                "fields": {},
                "schema": 1,
                "createAt": now,
                "updateAt": now,
            })
            content_order.append(desc_id)

            # Divider
            div_id = generate_block_id()
            new_blocks.append({
                "id": div_id,
                "type": "divider",
                "parentId": card_id,
                "boardId": BOARD_ID,
                "title": "",
                "fields": {},
                "schema": 1,
                "createAt": now,
                "updateAt": now,
            })
            content_order.append(div_id)

            # Checklist header
            header_id = generate_block_id()
            new_blocks.append({
                "id": header_id,
                "type": "text",
                "parentId": card_id,
                "boardId": BOARD_ID,
                "title": "## 📋 Subtasks Checklist",
                "fields": {},
                "schema": 1,
                "createAt": now,
                "updateAt": now,
            })
            content_order.append(header_id)

            # Checklist items
            for item in checklist:
                checkbox_id = generate_block_id()
                new_blocks.append({
                    "id": checkbox_id,
                    "type": "checkbox",
                    "parentId": card_id,
                    "boardId": BOARD_ID,
                    "title": item,
                    "fields": {"value": False},
                    "schema": 1,
                    "createAt": now,
                    "updateAt": now,
                })
                content_order.append(checkbox_id)

            # Another divider
            div2_id = generate_block_id()
            new_blocks.append({
                "id": div2_id,
                "type": "divider",
                "parentId": card_id,
                "boardId": BOARD_ID,
                "title": "",
                "fields": {},
                "schema": 1,
                "createAt": now,
                "updateAt": now,
            })
            content_order.append(div2_id)

            # Comment/context block
            comment_id = generate_block_id()
            new_blocks.append({
                "id": comment_id,
                "type": "text",
                "parentId": card_id,
                "boardId": BOARD_ID,
                "title": comment,
                "fields": {},
                "schema": 1,
                "createAt": now,
                "updateAt": now,
            })
            content_order.append(comment_id)

            # Post blocks
            post_response = await client.post(blocks_url, headers=get_headers(), json=new_blocks)

            if post_response.status_code in [200, 201]:
                # Update contentOrder
                existing_order = card.get("fields", {}).get("contentOrder", [])
                new_order = content_order

                patch_data = {
                    "updatedFields": {
                        "contentOrder": new_order
                    }
                }
                await client.patch(patch_url, headers=get_headers(), json=patch_data)
                content_updated += 1

        print()
        print("=" * 70)
        print(f"Complete: {updated} with due dates, {content_updated} with full content")
        print(f"Project timeline: {PROJECT_START.strftime('%Y-%m-%d')} to {max(due_dates.values()).strftime('%Y-%m-%d')}")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
