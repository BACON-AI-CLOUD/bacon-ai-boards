#!/usr/bin/env python3
"""
Comprehensive BACON-AI Task Updater

Updates all Focalboard tasks with:
- New naming convention: P0000, P0000-T0001, P0001-T0001, etc.
- Matching task IDs in Number property
- Detailed descriptions with AI agent instructions
- Content blocks with subtask checklists
- Deterministic control instructions
"""

import asyncio
import httpx
import json
import re
from typing import Dict, Any, List, Optional

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

def get_headers():
    return {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

# ============================================================================
# TASK DEFINITIONS with new naming convention
# ============================================================================

TASKS = {
    # ========== PHASE 0: VERIFICATION ==========
    "P0000": {
        "old_pattern": "P00 ",
        "title": "P0000 ── Phase 0: Verification (Critical Pre-Phase)",
        "icon": "🔍",
        "task_id": "P0000",
        "priority": PRIORITY_HIGH,
        "hours": "8",
        "description": """# Phase 0: Verification (Critical Pre-Phase)

## 🎯 PURPOSE
MANDATORY gate before ANY work begins. Prevents reinventing the wheel and ensures we build on existing knowledge.

## 🤖 SYSTEM PROMPT FOR LEAD AGENT
```
You are the BACON-AI Verification Lead Agent.
Role: Guardian of organizational memory
Authority: Can BLOCK progression to Phase 1
Responsibility: Ensure ALL verification tasks complete with GREEN status

CRITICAL RULES:
1. Query lessons learned BEFORE any analysis
2. Search web for current best practices (training data may be outdated)
3. Consult external AI models for diverse perspectives
4. Document ALL assumptions explicitly
5. Validate problem is not already solved

DO NOT proceed to Phase 1 until:
- All 5 subtasks show COMPLETED status
- No existing solution found OR adaptation plan created
- Current state baseline documented
```

## 📋 PHASE DEPENDENCIES
- **Blocks**: P0001 (Problem Definition)
- **Blocked By**: None (Entry point)

## 🔧 REQUIRED MCP TOOLS
1. `mcp__mcp-bacon-memory__memory_query_proven_approaches` - Query lessons
2. `mcp__mcp-bacon-memory__memory_log_lesson_learned` - Log findings
3. `WebSearch` - Current best practices
4. `mcp__groq-chat__*` / `mcp__openai-chat__*` / `mcp__gemini-chat__*` - AI consultation

## 📚 SKILLS TO LOAD
- `/lessons-learned` - Knowledge base access
- `/cross-model-consultation` - Multi-AI verification
- `/groq-chat` - Fast model queries

## ⚡ PARALLEL EXECUTION MATRIX
| Task | Can Run With | Must Wait For |
|------|--------------|---------------|
| T0001 | T0002, T0003 | None |
| T0002 | T0001, T0003 | None |
| T0003 | T0001, T0002 | None |
| T0004 | None | T0001, T0002, T0003 |
| T0005 | None | T0004 |

## 🔄 SELF-LEARNING CHECKPOINT
At phase completion, execute:
```python
mcp__mcp-bacon-memory__memory_store_proven_approach(
    content="Phase 0 verification for [PROJECT_TYPE]: [SUMMARY]",
    tags=["phase-0", "verification", "bacon-ai"],
    verification_count=1
)
```
""",
        "checklist": [
            {"text": "🔍 GATE CHECK: Confirm this is Phase 0 entry point", "checked": False},
            {"text": "📚 Query lessons learned database (P0000-T0001)", "checked": False},
            {"text": "🌐 Web search current best practices (P0000-T0002)", "checked": False},
            {"text": "🤖 Consult external AI models (P0000-T0003)", "checked": False},
            {"text": "📝 Document current state and assumptions (P0000-T0004)", "checked": False},
            {"text": "✅ Validate problem not already solved (P0000-T0005)", "checked": False},
            {"text": "🚦 GATE CHECK: All subtasks GREEN before proceeding", "checked": False},
            {"text": "📊 Log phase lessons learned to bacon-memory", "checked": False},
        ]
    },

    "P0000-T0001": {
        "old_pattern": "P00-T01",
        "title": "P0000-T0001 ── Query lessons learned database",
        "icon": "📚",
        "task_id": "P0000-T0001",
        "priority": PRIORITY_HIGH,
        "hours": "1",
        "description": """# Task: Query Lessons Learned Database

## 🎯 OBJECTIVE
Search organizational memory for existing solutions, patterns, and gotchas related to the current problem.

## 🤖 AGENT SYSTEM PROMPT
```
You are a Knowledge Retrieval Specialist.
Task ID: P0000-T0001
Phase: 0 - Verification

DETERMINISTIC EXECUTION SEQUENCE:
1. Extract keywords from problem statement
2. Execute EXACTLY 5 search queries (see below)
3. Document ALL results in structured format
4. Identify knowledge gaps for T0002
5. Flag contradictions for T0003 resolution

MANDATORY SEARCH QUERIES:
Query 1: "[problem domain] lessons learned"
Query 2: "[technology stack] proven approaches"
Query 3: "[project type] anti-patterns"
Query 4: "[similar past project] outcomes"
Query 5: "[error patterns] from [domain]"

OUTPUT FORMAT:
- Relevant lessons: [LIST with IDs]
- Applicable patterns: [LIST]
- Knowledge gaps: [LIST for T0002]
- Contradictions: [LIST for T0003]
```

## 🔧 MCP TOOL SEQUENCE (Execute in order)
```python
# Step 1: Query proven approaches
result1 = mcp__mcp-bacon-memory__memory_query_proven_approaches(
    query="[PROBLEM_DOMAIN]",
    tags=["verified", "proven"],
    min_verification_count=1
)

# Step 2: Query lessons learned
result2 = mcp__mcp-bacon-memory__memory_query_proven_approaches(
    query="[TECHNOLOGY] lessons",
    tags=["lessons-learned"],
    min_verification_count=0
)

# Step 3: Check sync status
status = mcp__mcp-bacon-memory__memory_get_sync_status()

# Step 4: Log search activity
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content=f"P0000-T0001: Queried {len(result1)+len(result2)} entries for [PROJECT]",
    severity="info",
    context="P0000-T0001 Knowledge Query"
)
```

## 📋 DEPENDENCIES
- **Blocks**: P0000-T0004, P0000-T0005
- **Blocked By**: None
- **Can Parallel With**: P0000-T0002, P0000-T0003

## 🔄 PARALLEL AGENT PROMPT
```
While I query lessons learned, spawn a parallel agent to:
1. Prepare summary template for findings
2. Pre-fetch documentation links from results
3. Create comparison matrix template
4. Draft gap analysis format for T0002 handoff
```

## ✅ SUCCESS CRITERIA
- [ ] Minimum 5 search queries executed
- [ ] All relevant lessons documented with IDs
- [ ] Knowledge gaps identified and listed
- [ ] Handoff notes prepared for T0002/T0003
- [ ] Lesson logged to bacon-memory
""",
        "checklist": [
            {"text": "📥 INIT: Load bacon-memory MCP tool", "checked": False},
            {"text": "🔍 Execute Query 1: [problem domain] lessons learned", "checked": False},
            {"text": "🔍 Execute Query 2: [technology] proven approaches", "checked": False},
            {"text": "🔍 Execute Query 3: [project type] anti-patterns", "checked": False},
            {"text": "🔍 Execute Query 4: [similar project] outcomes", "checked": False},
            {"text": "🔍 Execute Query 5: [error patterns] from [domain]", "checked": False},
            {"text": "📊 Compile results in structured format", "checked": False},
            {"text": "🔗 Identify gaps for P0000-T0002", "checked": False},
            {"text": "⚠️ Flag contradictions for P0000-T0003", "checked": False},
            {"text": "📝 Log lesson learned to bacon-memory", "checked": False},
            {"text": "✅ VERIFY: All criteria met before marking complete", "checked": False},
        ]
    },

    "P0000-T0002": {
        "old_pattern": "P00-T02",
        "title": "P0000-T0002 ── Web search current best practices",
        "icon": "🌐",
        "task_id": "P0000-T0002",
        "priority": PRIORITY_HIGH,
        "hours": "2",
        "description": """# Task: Web Search Current Best Practices

## 🎯 OBJECTIVE
Research current industry best practices, recent developments, and state-of-the-art solutions. Training data may be outdated - ALWAYS verify with fresh searches.

## 🤖 AGENT SYSTEM PROMPT
```
You are a Research Specialist.
Task ID: P0000-T0002
Phase: 0 - Verification

CRITICAL: Your training data may be outdated. Today is 2026.
ALWAYS search for information dated 2024-2026.

DETERMINISTIC EXECUTION SEQUENCE:
1. Review knowledge gaps from T0001
2. Execute EXACTLY 6 web searches (see below)
3. Fetch and analyze top 3 sources per search
4. Synthesize into actionable recommendations
5. Flag contradictions for T0003

MANDATORY SEARCH QUERIES (include year):
Query 1: "[technology] best practices 2026"
Query 2: "[problem domain] implementation guide 2025-2026"
Query 3: "[topic] common pitfalls avoid"
Query 4: "[technology] vs alternatives comparison 2026"
Query 5: "[domain] architecture patterns modern"
Query 6: "[problem type] case study success"

OUTPUT FORMAT:
- Best practices: [NUMBERED LIST with sources]
- Recent developments: [LIST with dates]
- Authoritative sources: [URLs]
- Contradictions found: [LIST for T0003]
```

## 🔧 MCP TOOL SEQUENCE
```python
# Step 1: Execute searches
search_results = []
for query in MANDATORY_QUERIES:
    result = WebSearch(query=query)
    search_results.append(result)

# Step 2: Fetch authoritative sources
for url in top_sources:
    content = WebFetch(
        url=url,
        prompt="Extract key best practices, warnings, and recommendations"
    )

# Step 3: Log activity
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content=f"P0000-T0002: Researched {len(search_results)} queries, found [KEY_INSIGHTS]",
    severity="info",
    context="P0000-T0002 Web Research"
)
```

## 📋 DEPENDENCIES
- **Blocks**: P0000-T0004, P0000-T0005
- **Blocked By**: None (but benefits from T0001 gaps)
- **Can Parallel With**: P0000-T0001, P0000-T0003

## 🔄 PARALLEL AGENT PROMPT
```
Spawn parallel agent to:
1. Monitor search result patterns
2. Identify contradictory advice across sources
3. Prepare comparison matrix for T0003
4. Cache authoritative documentation links
```

## ✅ SUCCESS CRITERIA
- [ ] 6 search queries executed
- [ ] 3+ authoritative sources reviewed per query
- [ ] Best practices documented with source URLs
- [ ] Contradictions flagged for T0003
- [ ] Lesson logged to bacon-memory
""",
        "checklist": [
            {"text": "📥 INIT: Review T0001 knowledge gaps (if available)", "checked": False},
            {"text": "🔍 Search 1: [technology] best practices 2026", "checked": False},
            {"text": "🔍 Search 2: [domain] implementation guide 2025-2026", "checked": False},
            {"text": "🔍 Search 3: [topic] common pitfalls avoid", "checked": False},
            {"text": "🔍 Search 4: [technology] vs alternatives 2026", "checked": False},
            {"text": "🔍 Search 5: [domain] architecture patterns modern", "checked": False},
            {"text": "🔍 Search 6: [problem type] case study success", "checked": False},
            {"text": "📖 WebFetch top 3 sources from each search", "checked": False},
            {"text": "📊 Synthesize findings into recommendations", "checked": False},
            {"text": "⚠️ Flag contradictions for P0000-T0003", "checked": False},
            {"text": "📝 Log lesson learned to bacon-memory", "checked": False},
            {"text": "✅ VERIFY: Include source URLs in all findings", "checked": False},
        ]
    },

    "P0000-T0003": {
        "old_pattern": "P00-T03",
        "title": "P0000-T0003 ── Consult external AI models",
        "icon": "🤖",
        "task_id": "P0000-T0003",
        "priority": PRIORITY_HIGH,
        "hours": "2",
        "description": """# Task: Consult External AI Models

## 🎯 OBJECTIVE
Get second opinions from multiple AI models to validate understanding, resolve contradictions, and identify blind spots.

## 🤖 AGENT SYSTEM PROMPT
```
You are a Multi-Model Consultation Coordinator.
Task ID: P0000-T0003
Phase: 0 - Verification

DETERMINISTIC EXECUTION SEQUENCE:
1. Prepare standardized consultation prompt
2. Query EXACTLY 4 different AI models
3. Document each response separately
4. Identify consensus vs divergence
5. Synthesize into recommendations

MODELS TO CONSULT (in order):
1. GPT-4o/GPT-5 via mcp__openai-chat__gpt4o_chat
2. Gemini 2.5 via mcp__gemini-chat__gemini_25_flash_chat
3. Llama 70B via mcp__groq-chat__llama_33_70b_chat
4. Qwen 32B via mcp__groq-chat__qwen3_32b_chat

CONSULTATION PROMPT TEMPLATE:
"Problem: [PROBLEM_STATEMENT]
Context: [RELEVANT_CONTEXT]
Contradictions from research: [FROM_T0001_T0002]

Questions:
1. What are the key considerations for this problem?
2. What pitfalls should we avoid?
3. What approach do you recommend and why?
4. Are there recent developments I should know about?"
```

## 🔧 MCP TOOL SEQUENCE
```python
# Prepare prompt
consultation_prompt = f\"\"\"
Problem: {PROBLEM_STATEMENT}
Context: {CONTEXT}
Research contradictions: {T0002_CONTRADICTIONS}

Questions:
1. Key considerations?
2. Pitfalls to avoid?
3. Recommended approach?
4. Recent developments?
\"\"\"

# Query models in sequence
responses = {}

# Model 1: GPT-4o
responses['gpt4o'] = mcp__openai-chat__gpt4o_chat(
    message=consultation_prompt,
    system_prompt="You are a technical advisor. Be specific and cite recent developments."
)

# Model 2: Gemini
responses['gemini'] = mcp__gemini-chat__gemini_25_flash_chat(
    message=consultation_prompt,
    system_prompt="You are a technical advisor with access to recent information."
)

# Model 3: Llama
responses['llama'] = mcp__groq-chat__llama_33_70b_chat(
    message=consultation_prompt,
    system_prompt="You are a technical advisor. Focus on practical implementation."
)

# Model 4: Qwen
responses['qwen'] = mcp__groq-chat__qwen3_32b_chat(
    message=consultation_prompt,
    system_prompt="You are a technical advisor. Provide alternative perspectives."
)

# Consensus analysis
consensus = mcp__ai-reasoning__consensus_analysis(
    responses=json.dumps(responses),
    question="What is the recommended approach?"
)

# Log findings
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content=f"P0000-T0003: Consulted 4 models. Consensus: {consensus['agreement_areas']}. Divergence: {consensus['disagreement_areas']}",
    severity="info",
    context="P0000-T0003 Multi-Model Consultation"
)
```

## 📋 DEPENDENCIES
- **Blocks**: P0000-T0004, P0000-T0005
- **Blocked By**: None (but benefits from T0001, T0002 contradictions)
- **Can Parallel With**: P0000-T0001, P0000-T0002

## ✅ SUCCESS CRITERIA
- [ ] 4+ models consulted with same prompt
- [ ] Each response documented separately
- [ ] Consensus areas identified
- [ ] Divergent opinions analyzed
- [ ] Lesson logged to bacon-memory
""",
        "checklist": [
            {"text": "📥 INIT: Collect contradictions from T0001/T0002", "checked": False},
            {"text": "📝 Prepare standardized consultation prompt", "checked": False},
            {"text": "🤖 Query GPT-4o via mcp__openai-chat__gpt4o_chat", "checked": False},
            {"text": "🤖 Query Gemini via mcp__gemini-chat__gemini_25_flash_chat", "checked": False},
            {"text": "🤖 Query Llama via mcp__groq-chat__llama_33_70b_chat", "checked": False},
            {"text": "🤖 Query Qwen via mcp__groq-chat__qwen3_32b_chat", "checked": False},
            {"text": "📊 Document each response separately", "checked": False},
            {"text": "✅ Identify consensus areas", "checked": False},
            {"text": "⚠️ Analyze divergent opinions", "checked": False},
            {"text": "📝 Synthesize recommendations", "checked": False},
            {"text": "📝 Log lesson learned to bacon-memory", "checked": False},
        ]
    },

    "P0000-T0004": {
        "old_pattern": "P00-T04",
        "title": "P0000-T0004 ── Document current state and assumptions",
        "icon": "📝",
        "task_id": "P0000-T0004",
        "priority": PRIORITY_HIGH,
        "hours": "2",
        "description": """# Task: Document Current State and Assumptions

## 🎯 OBJECTIVE
Create comprehensive baseline document capturing current state, all assumptions, and decision rationale.

## 🤖 AGENT SYSTEM PROMPT
```
You are a Documentation Specialist.
Task ID: P0000-T0004
Phase: 0 - Verification

DEPENDENCIES: Wait for T0001, T0002, T0003 to complete.

DETERMINISTIC EXECUTION SEQUENCE:
1. Compile findings from T0001, T0002, T0003
2. Document current system state
3. List ALL assumptions (explicit and implicit)
4. Assign risk level to each assumption
5. Record decision rationale

OUTPUT DOCUMENT STRUCTURE:
1. Executive Summary
2. Current State Assessment
3. Assumptions Table (ID, Assumption, Rationale, Risk)
4. Knowledge Base (from T0001-T0003)
5. Open Questions
6. Risk Register
```

## 📋 DEPENDENCIES
- **Blocks**: P0000-T0005
- **Blocked By**: P0000-T0001, P0000-T0002, P0000-T0003
- **Can Parallel With**: None (requires input from all prior tasks)

## 📄 DOCUMENT TEMPLATE
```markdown
# Current State Baseline
Project: [PROJECT_NAME]
Date: [DATE]
Task ID: P0000-T0004

## 1. Executive Summary
[1-2 paragraph summary]

## 2. Current State
### System Context
[Description of existing system/environment]

### Existing Components
| Component | Status | Notes |
|-----------|--------|-------|
| ... | ... | ... |

## 3. Assumptions
| ID | Assumption | Rationale | Risk | Mitigation |
|----|------------|-----------|------|------------|
| A001 | ... | ... | High/Med/Low | ... |

## 4. Knowledge Base
### From Lessons Learned (T0001)
[Summary]

### From Web Research (T0002)
[Summary with links]

### From AI Consultation (T0003)
[Consensus and divergence]

## 5. Open Questions
1. [Question needing resolution]

## 6. Risk Register
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
```

## ✅ SUCCESS CRITERIA
- [ ] Findings from T0001-T0003 compiled
- [ ] Current state fully documented
- [ ] All assumptions numbered and rationalized
- [ ] Risk levels assigned
- [ ] Document ready for T0005 validation
""",
        "checklist": [
            {"text": "⏳ WAIT: Confirm T0001, T0002, T0003 complete", "checked": False},
            {"text": "📥 Compile T0001 lessons learned findings", "checked": False},
            {"text": "📥 Compile T0002 web research findings", "checked": False},
            {"text": "📥 Compile T0003 AI consultation findings", "checked": False},
            {"text": "📝 Document current system state", "checked": False},
            {"text": "📋 List ALL explicit assumptions", "checked": False},
            {"text": "🔍 Identify implicit assumptions", "checked": False},
            {"text": "⚠️ Assign risk level to each assumption", "checked": False},
            {"text": "📝 Record decision rationale", "checked": False},
            {"text": "❓ Document open questions", "checked": False},
            {"text": "📊 Create risk register", "checked": False},
            {"text": "📝 Log lesson learned to bacon-memory", "checked": False},
        ]
    },

    "P0000-T0005": {
        "old_pattern": "P00-T05",
        "title": "P0000-T0005 ── Validate problem not already solved",
        "icon": "✅",
        "task_id": "P0000-T0005",
        "priority": PRIORITY_HIGH,
        "hours": "1",
        "description": """# Task: Validate Problem Not Already Solved

## 🎯 OBJECTIVE
Final gate check - confirm problem requires new work and isn't already solved internally or externally.

## 🤖 AGENT SYSTEM PROMPT
```
You are the Validation Gate Agent.
Task ID: P0000-T0005
Phase: 0 - Verification

CRITICAL ROLE: You are the FINAL GATE before Phase 1.
Your job is to be SKEPTICAL and challenge assumptions.

DETERMINISTIC DECISION MATRIX:
1. Evaluate: Build New vs Adapt Existing vs Buy vs Partner
2. Score each option: Effort (1-10), Value (1-10), Risk (1-10)
3. Calculate: Score = Value / (Effort * Risk)
4. Recommend highest score option

GO CRITERIA (ALL must be true):
- No existing solution adequately solves problem
- Value justifies effort (Value/Effort > 1.5)
- Team has required capabilities
- Timeline is feasible

NO-GO CRITERIA (ANY triggers NO-GO):
- Existing solution found that's good enough
- Value doesn't justify effort (Value/Effort < 1.0)
- Critical capability missing
- Better alternatives available
```

## 🔧 DECISION MATRIX TEMPLATE
```markdown
## Decision Matrix

| Option | Effort (1-10) | Value (1-10) | Risk (1-10) | Score |
|--------|---------------|--------------|-------------|-------|
| Build New | | | | |
| Adapt [X] | | | | |
| Buy [Y] | | | | |
| Partner [Z] | | | | |

Score = Value / (Effort * Risk)
Highest score wins.

## Recommendation
- **Decision**: GO / NO-GO
- **Rationale**: [Explanation]
- **Conditions**: [If any]
```

## 📋 DEPENDENCIES
- **Blocks**: P0001 (Phase 1: Problem Definition)
- **Blocked By**: P0000-T0004
- **Can Parallel With**: None (final gate)

## ✅ SUCCESS CRITERIA
- [ ] All T0001-T0004 outputs reviewed
- [ ] Decision matrix completed with scores
- [ ] GO/NO-GO recommendation documented
- [ ] Rationale clear and defensible
- [ ] Phase 0 lessons stored in bacon-memory
""",
        "checklist": [
            {"text": "⏳ WAIT: Confirm T0004 complete", "checked": False},
            {"text": "📥 Review T0004 baseline document", "checked": False},
            {"text": "🔍 Check internal tools/systems for existing solutions", "checked": False},
            {"text": "🔍 Check commercial solutions available", "checked": False},
            {"text": "🔍 Check open source options", "checked": False},
            {"text": "🔍 Check partner capabilities", "checked": False},
            {"text": "📊 Complete decision matrix with scores", "checked": False},
            {"text": "🧮 Calculate Score = Value / (Effort * Risk)", "checked": False},
            {"text": "✅ Make GO/NO-GO recommendation", "checked": False},
            {"text": "📝 Document rationale", "checked": False},
            {"text": "📝 Store Phase 0 proven approach in bacon-memory", "checked": False},
            {"text": "🚦 GATE: Update phase status based on decision", "checked": False},
        ]
    },

    # ========== PHASE 1: PROBLEM DEFINITION ==========
    "P0001": {
        "old_pattern": "P01 ",
        "title": "P0001 ── Phase 1: Problem Definition (Design Thinking)",
        "icon": "🎯",
        "task_id": "P0001",
        "priority": PRIORITY_HIGH,
        "hours": "16",
        "description": """# Phase 1: Problem Definition (Design Thinking)

## 🎯 PURPOSE
Apply Design Thinking methodology to deeply understand the problem from multiple perspectives BEFORE generating solutions.

## 🤖 SYSTEM PROMPT FOR LEAD AGENT
```
You are the BACON-AI Design Thinking Facilitator.
Phase: 1 - Problem Definition
Authority: Can request return to Phase 0 if gaps found

CRITICAL RULES:
1. NO solution discussion allowed in this phase
2. Focus purely on problem UNDERSTANDING
3. Use empathy mapping for stakeholder insight
4. Apply 5W+1H for comprehensive definition
5. Use Six Thinking Hats for perspective coverage

Phase Entry Criteria:
- Phase 0 completed with GO decision
- Baseline document available

Phase Exit Criteria:
- Empathy maps for all stakeholder groups
- Problem statement refined and approved
- Success criteria quantified and measurable
- Stakeholder sign-off obtained
```

## 📋 PHASE DEPENDENCIES
- **Blocks**: P0002 (Data Gathering)
- **Blocked By**: P0000 (Verification)

## ⚡ PARALLEL EXECUTION MATRIX
| Task | Can Run With | Must Wait For |
|------|--------------|---------------|
| T0001 | T0002 | P0000 complete |
| T0002 | T0001 | P0000 complete |
| T0003 | None | T0001, T0002 |
| T0004 | None | T0003 |
| T0005 | None | T0004 |

## 🔧 REQUIRED MCP TOOLS
- `mcp__mcp-bacon-memory__*` - Knowledge management
- `mcp__mcp-etherpad-hub__*` - Collaborative documents
- `mcp__ai-reasoning__*` - Deep analysis

## 📚 SKILLS TO LOAD
- `/triz-innovation` - TRIZ methodology
- `/bacon-ai-perspective-analyst` - Six Thinking Hats
- `/bacon-ai-human-experience` - Design Thinking
""",
        "checklist": [
            {"text": "🚦 GATE: Confirm P0000 complete with GO decision", "checked": False},
            {"text": "📥 Load P0000 baseline document", "checked": False},
            {"text": "💭 Create empathy maps (P0001-T0001)", "checked": False},
            {"text": "❓ Define problem with 5W+1H (P0001-T0002)", "checked": False},
            {"text": "🎩 Apply Six Thinking Hats (P0001-T0003)", "checked": False},
            {"text": "📋 Document success criteria (P0001-T0004)", "checked": False},
            {"text": "✔️ Get stakeholder approval (P0001-T0005)", "checked": False},
            {"text": "📝 Log phase lessons to bacon-memory", "checked": False},
            {"text": "🚦 GATE: All subtasks complete before P0002", "checked": False},
        ]
    },

    "P0001-T0001": {
        "old_pattern": "P01-T01",
        "title": "P0001-T0001 ── Create empathy map",
        "icon": "💭",
        "task_id": "P0001-T0001",
        "priority": PRIORITY_HIGH,
        "hours": "3",
        "description": """# Task: Create Empathy Map

## 🎯 OBJECTIVE
Build deep understanding of all stakeholders by mapping what they Think, Feel, Say, and Do.

## 🤖 AGENT SYSTEM PROMPT
```
You are an Empathy Mapping Specialist.
Task ID: P0001-T0001
Phase: 1 - Problem Definition

DETERMINISTIC EXECUTION SEQUENCE:
1. Identify ALL stakeholder groups (min 3)
2. For EACH stakeholder, complete full empathy map
3. Identify PAINS and GAINS for each
4. Synthesize cross-stakeholder insights
5. Flag conflicts between stakeholder needs

EMPATHY MAP TEMPLATE (per stakeholder):
- THINK: What occupies their mind?
- FEEL: Emotions about situation
- SAY: What they express to others
- DO: Observable behaviors
- PAINS: Frustrations, fears, obstacles
- GAINS: Wants, needs, success measures
```

## 📋 STAKEHOLDER GROUPS TO MAP
1. Primary users (direct users of solution)
2. Secondary users (indirect beneficiaries)
3. Administrators/operators
4. Business sponsors
5. Technical team
6. External partners (if applicable)

## 📄 OUTPUT TEMPLATE
```markdown
# Empathy Maps - [PROJECT]
Date: [DATE]
Task ID: P0001-T0001

## Stakeholder 1: [ROLE]

### THINK
- [What occupies their mind daily?]
- [What worries them?]

### FEEL
- [Current emotional state]
- [Desired emotional state]

### SAY
- [Direct quotes or paraphrased]

### DO
- [Observable behaviors]

### PAINS
- [Frustrations]
- [Fears]
- [Obstacles]

### GAINS
- [Desired outcomes]
- [Success measures]

---
[Repeat for each stakeholder]

## Cross-Stakeholder Insights
- Alignments: [Where needs align]
- Conflicts: [Where needs conflict]
- Priorities: [What matters most to most]
```

## ✅ SUCCESS CRITERIA
- [ ] 3+ stakeholder groups identified
- [ ] Complete empathy map for each
- [ ] PAINS and GAINS documented
- [ ] Cross-stakeholder insights synthesized
- [ ] Conflicts flagged for resolution
""",
        "checklist": [
            {"text": "📥 INIT: Load P0000 baseline for context", "checked": False},
            {"text": "👥 Identify primary user stakeholder group", "checked": False},
            {"text": "👥 Identify secondary user stakeholder group", "checked": False},
            {"text": "👥 Identify admin/operator stakeholder group", "checked": False},
            {"text": "👥 Identify additional stakeholder groups", "checked": False},
            {"text": "💭 Complete empathy map: Primary users", "checked": False},
            {"text": "💭 Complete empathy map: Secondary users", "checked": False},
            {"text": "💭 Complete empathy map: Admins", "checked": False},
            {"text": "💭 Complete empathy map: Other groups", "checked": False},
            {"text": "📊 Identify PAINS for each group", "checked": False},
            {"text": "📊 Identify GAINS for each group", "checked": False},
            {"text": "🔗 Synthesize cross-stakeholder insights", "checked": False},
            {"text": "⚠️ Flag stakeholder conflicts", "checked": False},
            {"text": "📝 Log lesson learned to bacon-memory", "checked": False},
        ]
    },

    "P0001-T0002": {
        "old_pattern": "P01-T02",
        "title": "P0001-T0002 ── Define problem using 5W+1H framework",
        "icon": "❓",
        "task_id": "P0001-T0002",
        "priority": PRIORITY_HIGH,
        "hours": "2",
        "description": """# Task: Define Problem Using 5W+1H Framework

## 🎯 OBJECTIVE
Create precise, comprehensive problem statement using Who, What, When, Where, Why, How framework.

## 🤖 AGENT SYSTEM PROMPT
```
You are a Problem Definition Specialist.
Task ID: P0001-T0002
Phase: 1 - Problem Definition

DETERMINISTIC EXECUTION SEQUENCE:
1. Answer EACH of the 6 dimensions thoroughly
2. For each dimension, document what IS and what IS NOT
3. Distinguish symptoms from root causes
4. Synthesize into problem statement
5. Validate against empathy maps (T0001)

5W+1H QUESTIONS:
- WHO: Who is affected? Who causes it? Who cares?
- WHAT: What exactly is the problem? What is NOT the problem?
- WHEN: When does it occur? When did it start? When is it worst?
- WHERE: Where does it happen? Where does it NOT happen?
- WHY: Why does it matter? Why now? Why this priority?
- HOW: How does it manifest? How severe? How frequent?
```

## 📄 OUTPUT TEMPLATE
```markdown
# 5W+1H Problem Definition
Project: [PROJECT]
Task ID: P0001-T0002

## WHO
### IS affected:
- [List all affected parties]

### IS NOT affected:
- [Explicitly exclude]

### Causes the problem:
- [Root cause actors/systems]

## WHAT
### IS the problem:
- [Precise description]

### IS NOT the problem:
- [Out of scope items]

### Symptoms:
- [Observable symptoms]

### Root Cause:
- [Underlying cause]

## WHEN
### Occurs:
- [Timing, frequency]

### Started:
- [Origin point]

### Is worst:
- [Peak conditions]

## WHERE
### Happens:
- [Locations, contexts]

### Does NOT happen:
- [Excluded contexts]

## WHY
### Matters:
- [Business impact]

### Now:
- [Urgency drivers]

### This priority:
- [Prioritization rationale]

## HOW
### Manifests:
- [Observable signs]

### Severity:
- [Impact measurement]

### Frequency:
- [Occurrence rate]

---

## SYNTHESIZED PROBLEM STATEMENT
"For [WHO], who [PAIN/NEED], the [SOLUTION CATEGORY] that [KEY BENEFIT]. Unlike [ALTERNATIVES], our solution [DIFFERENTIATOR]."
```

## ✅ SUCCESS CRITERIA
- [ ] All 6 dimensions thoroughly answered
- [ ] IS/IS NOT documented for each
- [ ] Root cause vs symptoms distinguished
- [ ] Problem statement synthesized
- [ ] Validated against T0001 empathy maps
""",
        "checklist": [
            {"text": "📥 INIT: Review T0001 empathy maps", "checked": False},
            {"text": "👥 WHO: Document who IS affected", "checked": False},
            {"text": "👥 WHO: Document who IS NOT affected", "checked": False},
            {"text": "📋 WHAT: Define what IS the problem", "checked": False},
            {"text": "📋 WHAT: Define what IS NOT the problem", "checked": False},
            {"text": "⏰ WHEN: Document timing and frequency", "checked": False},
            {"text": "📍 WHERE: Document locations/contexts", "checked": False},
            {"text": "❓ WHY: Document business impact", "checked": False},
            {"text": "❓ WHY: Document urgency drivers", "checked": False},
            {"text": "🔧 HOW: Document manifestation", "checked": False},
            {"text": "🔧 HOW: Document severity and frequency", "checked": False},
            {"text": "🔍 Distinguish symptoms from root cause", "checked": False},
            {"text": "📝 Synthesize problem statement", "checked": False},
            {"text": "✅ Validate against empathy maps", "checked": False},
            {"text": "📝 Log lesson learned to bacon-memory", "checked": False},
        ]
    },

    "P0001-T0003": {
        "old_pattern": "P01-T03",
        "title": "P0001-T0003 ── Apply Six Thinking Hats review",
        "icon": "🎩",
        "task_id": "P0001-T0003",
        "priority": PRIORITY_MEDIUM,
        "hours": "2",
        "description": """# Task: Apply Six Thinking Hats Review

## 🎯 OBJECTIVE
Review problem definition from six distinct perspectives to ensure comprehensive understanding and identify blind spots.

## 🤖 AGENT SYSTEM PROMPT
```
You are a Six Thinking Hats Facilitator.
Task ID: P0001-T0003
Phase: 1 - Problem Definition

DETERMINISTIC EXECUTION SEQUENCE:
Process EACH hat FULLY before moving to next.
Order: White → Red → Black → Yellow → Green → Blue

HAT DEFINITIONS:
⚪ WHITE: Facts, data, information only
🔴 RED: Emotions, intuition, gut feelings
⚫ BLACK: Caution, risks, problems, criticism
🟡 YELLOW: Benefits, optimism, opportunities
🟢 GREEN: Creativity, alternatives, new ideas
🔵 BLUE: Process, meta-thinking, conclusions
```

## 🔧 MULTI-MODEL HAT ASSIGNMENT
```python
# Assign different AI models to different hats for diversity

# WHITE HAT - Facts (analytical model)
white_result = mcp__openai-chat__gpt4o_chat(
    message=f"WHITE HAT ONLY: What are the verified facts about: {PROBLEM}",
    system_prompt="You are thinking with the WHITE HAT. Only state facts and data. No opinions."
)

# RED HAT - Emotions (diverse model)
red_result = mcp__groq-chat__llama_33_70b_chat(
    message=f"RED HAT ONLY: What emotional reactions exist about: {PROBLEM}",
    system_prompt="You are thinking with the RED HAT. Express emotions and intuitions only."
)

# BLACK HAT - Risks (critical model)
black_result = mcp__gemini-chat__gemini_25_flash_chat(
    message=f"BLACK HAT ONLY: What are the risks and problems with: {PROBLEM}",
    system_prompt="You are thinking with the BLACK HAT. Be critical and identify risks."
)

# Continue for Yellow, Green, Blue...
```

## 📄 OUTPUT TEMPLATE
```markdown
# Six Thinking Hats Analysis
Project: [PROJECT]
Task ID: P0001-T0003

## ⚪ WHITE HAT (Facts)
- Verified facts:
- Data available:
- Data missing:
- Assumptions needing validation:

## 🔴 RED HAT (Emotions)
- Stakeholder feelings:
- Team intuitions:
- Emotional resistance anticipated:
- Excitement factors:

## ⚫ BLACK HAT (Risks)
- What could go wrong:
- Obstacles identified:
- Why solutions might fail:
- Critical risks:

## 🟡 YELLOW HAT (Benefits)
- Potential benefits:
- Who gains:
- Opportunities created:
- Best case scenario:

## 🟢 GREEN HAT (Creativity)
- Alternative framings:
- Unconventional approaches:
- Cross-domain connections:
- What-if scenarios:

## 🔵 BLUE HAT (Process)
- Key learnings:
- Next steps:
- Who to involve:
- Timeline implications:

## SYNTHESIS
- Blind spots identified:
- Key insights:
- Recommendations:
```

## ✅ SUCCESS CRITERIA
- [ ] All 6 hats applied in sequence
- [ ] Each hat has 3+ insights
- [ ] Multiple AI models used for diversity
- [ ] Blind spots explicitly identified
- [ ] Synthesis completed
""",
        "checklist": [
            {"text": "⏳ WAIT: Confirm T0001, T0002 complete", "checked": False},
            {"text": "⚪ WHITE HAT: Document all verified facts", "checked": False},
            {"text": "⚪ WHITE HAT: List data available and missing", "checked": False},
            {"text": "🔴 RED HAT: Capture emotional reactions", "checked": False},
            {"text": "🔴 RED HAT: Note intuitions and gut feelings", "checked": False},
            {"text": "⚫ BLACK HAT: Identify all risks", "checked": False},
            {"text": "⚫ BLACK HAT: Document potential failures", "checked": False},
            {"text": "🟡 YELLOW HAT: List all benefits", "checked": False},
            {"text": "🟡 YELLOW HAT: Describe best case scenario", "checked": False},
            {"text": "🟢 GREEN HAT: Generate creative alternatives", "checked": False},
            {"text": "🟢 GREEN HAT: Explore unconventional approaches", "checked": False},
            {"text": "🔵 BLUE HAT: Synthesize learnings", "checked": False},
            {"text": "🔵 BLUE HAT: Define next steps", "checked": False},
            {"text": "📊 Identify blind spots from analysis", "checked": False},
            {"text": "📝 Log lesson learned to bacon-memory", "checked": False},
        ]
    },

    "P0001-T0004": {
        "old_pattern": "P01-T04",
        "title": "P0001-T0004 ── Document success criteria and constraints",
        "icon": "📋",
        "task_id": "P0001-T0004",
        "priority": PRIORITY_HIGH,
        "hours": "2",
        "description": """# Task: Document Success Criteria and Constraints

## 🎯 OBJECTIVE
Define MEASURABLE success criteria and identify ALL constraints that will bound the solution space.

## 🤖 AGENT SYSTEM PROMPT
```
You are a Requirements Engineer.
Task ID: P0001-T0004
Phase: 1 - Problem Definition

DETERMINISTIC CRITERIA FRAMEWORK:
All criteria MUST be SMART:
- Specific: Exactly what must be achieved
- Measurable: Quantified target
- Achievable: Realistic given constraints
- Relevant: Addresses the problem
- Time-bound: Has a deadline

PRIORITY LEVELS:
- P0 (Must-Have): Failure without these = project failure
- P1 (Should-Have): Significant value, but workarounds exist
- P2 (Nice-to-Have): Enhancement, not critical
```

## 📄 OUTPUT TEMPLATE
```markdown
# Success Criteria & Constraints
Project: [PROJECT]
Task ID: P0001-T0004

## SUCCESS CRITERIA

### P0 - Must Have (Failure without = project failure)
| ID | Criterion | Measure | Target | Deadline | Acceptance Test |
|----|-----------|---------|--------|----------|-----------------|
| SC-001 | | | | | |

### P1 - Should Have (Significant value)
| ID | Criterion | Measure | Target | Deadline | Acceptance Test |
|----|-----------|---------|--------|----------|-----------------|

### P2 - Nice to Have (Enhancement)
| ID | Criterion | Measure | Target | Deadline | Acceptance Test |
|----|-----------|---------|--------|----------|-----------------|

## CONSTRAINTS

### Technical Constraints
| ID | Constraint | Rationale | Negotiable? |
|----|------------|-----------|-------------|
| TC-001 | | | Yes/No |

### Business Constraints
| ID | Constraint | Rationale | Negotiable? |
|----|------------|-----------|-------------|
| BC-001 | Budget: $X | | |
| BC-002 | Timeline: X weeks | | |

### Resource Constraints
| ID | Constraint | Rationale | Negotiable? |
|----|------------|-----------|-------------|
| RC-001 | Team size: X | | |

## ACCEPTANCE TESTS
For each P0 criterion, define:
```
Test ID: AT-001
Criterion: SC-001
Preconditions: [Setup required]
Steps:
1. [Step 1]
2. [Step 2]
Expected Result: [What success looks like]
```
```

## ✅ SUCCESS CRITERIA
- [ ] All criteria are SMART
- [ ] P0/P1/P2 prioritization complete
- [ ] All constraint types documented
- [ ] Acceptance tests for P0 criteria
- [ ] Ready for stakeholder approval
""",
        "checklist": [
            {"text": "⏳ WAIT: Confirm T0003 complete", "checked": False},
            {"text": "📥 Review empathy maps for stakeholder needs", "checked": False},
            {"text": "📥 Review 5W+1H for problem scope", "checked": False},
            {"text": "📥 Review Six Hats for risks/benefits", "checked": False},
            {"text": "📋 Define P0 (Must-Have) criteria", "checked": False},
            {"text": "📋 Define P1 (Should-Have) criteria", "checked": False},
            {"text": "📋 Define P2 (Nice-to-Have) criteria", "checked": False},
            {"text": "✅ Verify ALL criteria are SMART", "checked": False},
            {"text": "🔧 Document technical constraints", "checked": False},
            {"text": "💼 Document business constraints", "checked": False},
            {"text": "👥 Document resource constraints", "checked": False},
            {"text": "📝 Write acceptance tests for P0 criteria", "checked": False},
            {"text": "📝 Log lesson learned to bacon-memory", "checked": False},
        ]
    },

    "P0001-T0005": {
        "old_pattern": "P01-T05",
        "title": "P0001-T0005 ── Get stakeholder approval",
        "icon": "✔️",
        "task_id": "P0001-T0005",
        "priority": PRIORITY_HIGH,
        "hours": "2",
        "description": """# Task: Get Stakeholder Approval

## 🎯 OBJECTIVE
Present problem definition to stakeholders and obtain FORMAL approval before proceeding.

## 🤖 AGENT SYSTEM PROMPT
```
You are a Stakeholder Communication Specialist.
Task ID: P0001-T0005
Phase: 1 - Problem Definition

CRITICAL: This is a GATE task.
NO proceeding to Phase 2 without explicit approval.

DETERMINISTIC EXECUTION SEQUENCE:
1. Prepare executive summary presentation
2. Schedule review with stakeholders
3. Present and gather feedback
4. Document all feedback (even if not incorporated)
5. Obtain explicit sign-off
6. Update documents based on feedback
```

## 📄 PRESENTATION TEMPLATE
```markdown
# Problem Definition Review
Project: [PROJECT]
Date: [DATE]

## Executive Summary
[1 paragraph: Problem, impact, proposed scope]

## Stakeholder Impact Matrix
| Stakeholder | Current Pain | Expected Benefit |
|-------------|--------------|------------------|
| | | |

## Problem Statement
[From T0002]

## Success Criteria Summary
### Must-Have (P0)
- [Criterion 1]
- [Criterion 2]

### Key Constraints
- Budget: $X
- Timeline: X weeks
- Team: X people

## Request for Approval
[ ] Problem statement accurately reflects the issue
[ ] Scope is appropriate
[ ] Success criteria are acceptable
[ ] Constraints are understood
[ ] Proceed to Phase 2: Data Gathering

Approved by: _________________ Date: _______
```

## 📋 DEPENDENCIES
- **Blocks**: P0002 (Phase 2)
- **Blocked By**: P0001-T0004
- **REQUIRES**: Human stakeholder interaction

## ✅ SUCCESS CRITERIA
- [ ] Presentation prepared
- [ ] All stakeholders reviewed
- [ ] Feedback documented
- [ ] Explicit approval obtained
- [ ] Phase 1 lessons stored
""",
        "checklist": [
            {"text": "⏳ WAIT: Confirm T0004 complete", "checked": False},
            {"text": "📄 Prepare executive summary", "checked": False},
            {"text": "📊 Create stakeholder impact matrix", "checked": False},
            {"text": "📝 Compile problem statement from T0002", "checked": False},
            {"text": "📋 Summarize success criteria from T0004", "checked": False},
            {"text": "📅 Schedule stakeholder review", "checked": False},
            {"text": "🎤 Conduct presentation", "checked": False},
            {"text": "📝 Document ALL feedback received", "checked": False},
            {"text": "✏️ Update documents based on feedback", "checked": False},
            {"text": "✅ Obtain explicit sign-off", "checked": False},
            {"text": "📝 Store Phase 1 proven approach in bacon-memory", "checked": False},
            {"text": "🚦 GATE: Approval received - ready for P0002", "checked": False},
        ]
    },
}

# Add remaining phases with similar structure...
# Phases 2-12 follow the same detailed pattern

REMAINING_PHASES = {
    # Phase 2
    "P0002": ("Phase 2: Data Gathering (Systems Thinking)", "📊", "P0002", PRIORITY_HIGH, "16"),
    "P0002-T0001": ("Create context map of system boundaries", "🗺️", "P0002-T0001", PRIORITY_HIGH, "3"),
    "P0002-T0002": ("Conduct stakeholder analysis", "👥", "P0002-T0002", PRIORITY_HIGH, "3"),
    "P0002-T0003": ("Collect data from all sources", "📥", "P0002-T0003", PRIORITY_HIGH, "4"),
    "P0002-T0004": ("Review existing documentation", "📖", "P0002-T0004", PRIORITY_MEDIUM, "3"),
    "P0002-T0005": ("Identify data gaps and plan collection", "🔎", "P0002-T0005", PRIORITY_HIGH, "3"),

    # Phase 3
    "P0003": ("Phase 3: Analysis (TRIZ + Systems Thinking)", "🔬", "P0003", PRIORITY_HIGH, "20"),
    "P0003-T0001": ("Create causal loop diagrams", "🔄", "P0003-T0001", PRIORITY_HIGH, "4"),
    "P0003-T0002": ("Apply TRIZ contradiction matrix", "⚡", "P0003-T0002", PRIORITY_HIGH, "4"),
    "P0003-T0003": ("Identify patterns from data", "🔍", "P0003-T0003", PRIORITY_HIGH, "4"),
    "P0003-T0004": ("Deep analysis (mindmaps, diagrams)", "🧠", "P0003-T0004", PRIORITY_MEDIUM, "4"),
    "P0003-T0005": ("QA review with confidence levels", "✅", "P0003-T0005", PRIORITY_HIGH, "4"),

    # Phase 4
    "P0004": ("Phase 4: Solution Generation (TRIZ 40 Principles)", "💡", "P0004", PRIORITY_HIGH, "16"),
    "P0004-T0001": ("Apply TRIZ 40 Inventive Principles", "🛠️", "P0004-T0001", PRIORITY_HIGH, "4"),
    "P0004-T0002": ("Parallel agent generation (5-10 agents)", "🤖", "P0004-T0002", PRIORITY_HIGH, "4"),
    "P0004-T0003": ("Collective discussion for more ideas", "💬", "P0004-T0003", PRIORITY_MEDIUM, "3"),
    "P0004-T0004": ("Compile master solution list (min 20)", "📝", "P0004-T0004", PRIORITY_HIGH, "3"),
    "P0004-T0005": ("Enforce NO EVALUATION rule", "🚫", "P0004-T0005", PRIORITY_HIGH, "2"),

    # Phase 5
    "P0005": ("Phase 5: Evaluation (Multi-Criteria Analysis)", "⚖️", "P0005", PRIORITY_HIGH, "16"),
    "P0005-T0001": ("Apply feasibility filtering", "🔍", "P0005-T0001", PRIORITY_HIGH, "3"),
    "P0005-T0002": ("Create multi-criteria scoring matrix", "📊", "P0005-T0002", PRIORITY_HIGH, "4"),
    "P0005-T0003": ("Apply Six Thinking Hats (Yellow/Black)", "🎩", "P0005-T0003", PRIORITY_MEDIUM, "3"),
    "P0005-T0004": ("Conduct weighted voting by agents", "🗳️", "P0005-T0004", PRIORITY_HIGH, "3"),
    "P0005-T0005": ("Identify top 3 solutions with scores", "🏆", "P0005-T0005", PRIORITY_HIGH, "3"),

    # Phase 6
    "P0006": ("Phase 6: Consensus Voting (Multi-Model + Human)", "🗳️", "P0006", PRIORITY_HIGH, "8"),
    "P0006-T0001": ("Collect votes from BACON-AI agents", "🤖", "P0006-T0001", PRIORITY_HIGH, "2"),
    "P0006-T0002": ("Consult external AI models", "🌐", "P0006-T0002", PRIORITY_HIGH, "2"),
    "P0006-T0003": ("Get human vote (final authority)", "👤", "P0006-T0003", PRIORITY_HIGH, "1"),
    "P0006-T0004": ("Calculate consensus percentage", "📊", "P0006-T0004", PRIORITY_MEDIUM, "1"),
    "P0006-T0005": ("Apply decision rules", "📋", "P0006-T0005", PRIORITY_HIGH, "2"),

    # Phase 7
    "P0007": ("Phase 7: Design Excellence (Architecture)", "🏗️", "P0007", PRIORITY_HIGH, "24"),
    "P0007-T0001": ("Create Architecture Decision Records", "📄", "P0007-T0001", PRIORITY_HIGH, "4"),
    "P0007-T0002": ("Draw system architecture diagrams", "📐", "P0007-T0002", PRIORITY_HIGH, "6"),
    "P0007-T0003": ("Define component responsibilities", "🧩", "P0007-T0003", PRIORITY_HIGH, "4"),
    "P0007-T0004": ("Identify design patterns to apply", "🔧", "P0007-T0004", PRIORITY_MEDIUM, "4"),
    "P0007-T0005": ("Specify quality attributes", "⭐", "P0007-T0005", PRIORITY_HIGH, "6"),

    # Phase 8
    "P0008": ("Phase 8: Implementation Planning (Execution)", "📋", "P0008", PRIORITY_HIGH, "16"),
    "P0008-T0001": ("Create Work Breakdown Structure", "📝", "P0008-T0001", PRIORITY_HIGH, "4"),
    "P0008-T0002": ("Create dependency graph (Gantt)", "📊", "P0008-T0002", PRIORITY_HIGH, "3"),
    "P0008-T0003": ("Allocate resources (team, tools)", "👥", "P0008-T0003", PRIORITY_HIGH, "3"),
    "P0008-T0004": ("Document risk mitigation plan", "⚠️", "P0008-T0004", PRIORITY_HIGH, "3"),
    "P0008-T0005": ("Define success criteria & acceptance", "✅", "P0008-T0005", PRIORITY_HIGH, "3"),

    # Phase 9
    "P0009": ("Phase 9: TDD Build (Test-Driven Development)", "🧪", "P0009", PRIORITY_HIGH, "40"),
    "P0009-T0001": ("Establish test baseline", "📊", "P0009-T0001", PRIORITY_HIGH, "4"),
    "P0009-T0002": ("RED: Write failing tests first", "🔴", "P0009-T0002", PRIORITY_HIGH, "8"),
    "P0009-T0003": ("GREEN: Write code to pass tests", "🟢", "P0009-T0003", PRIORITY_HIGH, "12"),
    "P0009-T0004": ("REFACTOR: Improve code quality", "🔵", "P0009-T0004", PRIORITY_MEDIUM, "8"),
    "P0009-T0005": ("V-Model progression (TUT→FUT→SIT→UAT)", "📈", "P0009-T0005", PRIORITY_HIGH, "6"),
    "P0009-T0006": ("Verify >90% code coverage", "✅", "P0009-T0006", PRIORITY_HIGH, "2"),

    # Phase 10
    "P0010": ("Phase 10: Change Management (User Adoption)", "📣", "P0010", PRIORITY_HIGH, "16"),
    "P0010-T0001": ("Create user training materials", "📚", "P0010-T0001", PRIORITY_HIGH, "4"),
    "P0010-T0002": ("Prepare demo video/walkthrough", "🎬", "P0010-T0002", PRIORITY_MEDIUM, "4"),
    "P0010-T0003": ("Set up feedback collection", "💬", "P0010-T0003", PRIORITY_HIGH, "2"),
    "P0010-T0004": ("Execute communication plan", "📢", "P0010-T0004", PRIORITY_HIGH, "3"),
    "P0010-T0005": ("Track adoption metrics", "📊", "P0010-T0005", PRIORITY_HIGH, "3"),

    # Phase 11
    "P0011": ("Phase 11: Deployment (Production Rollout)", "🚀", "P0011", PRIORITY_HIGH, "16"),
    "P0011-T0001": ("Complete pre-deployment checklist", "📋", "P0011-T0001", PRIORITY_HIGH, "2"),
    "P0011-T0002": ("Run deployment automation", "⚙️", "P0011-T0002", PRIORITY_HIGH, "4"),
    "P0011-T0003": ("Execute health checks", "🏥", "P0011-T0003", PRIORITY_HIGH, "2"),
    "P0011-T0004": ("Verify monitoring and alerting", "📡", "P0011-T0004", PRIORITY_HIGH, "3"),
    "P0011-T0005": ("Run smoke tests in production", "🧪", "P0011-T0005", PRIORITY_HIGH, "2"),
    "P0011-T0006": ("Get UAT approval", "✔️", "P0011-T0006", PRIORITY_HIGH, "3"),

    # Phase 12
    "P0012": ("Phase 12: SSC Retrospective (Learning)", "🔄", "P0012", PRIORITY_HIGH, "8"),
    "P0012-T0001": ("Collect human feedback", "👤", "P0012-T0001", PRIORITY_HIGH, "1"),
    "P0012-T0002": ("Run agent SSC (Stop/Start/Continue)", "🤖", "P0012-T0002", PRIORITY_HIGH, "2"),
    "P0012-T0003": ("Update SE-Agent trajectory memory", "🧠", "P0012-T0003", PRIORITY_HIGH, "1"),
    "P0012-T0004": ("Add lessons to database (min 3)", "📚", "P0012-T0004", PRIORITY_HIGH, "1"),
    "P0012-T0005": ("Document proven patterns (min 4)", "📝", "P0012-T0005", PRIORITY_HIGH, "1"),
    "P0012-T0006": ("Assess organizational impact", "📊", "P0012-T0006", PRIORITY_MEDIUM, "1"),
    "P0012-T0007": ("Execute dissemination plan", "📣", "P0012-T0007", PRIORITY_MEDIUM, "1"),
}

def generate_standard_description(task_id: str, title: str) -> str:
    """Generate standard description for remaining tasks."""
    phase_num = task_id.split("-")[0] if "-" in task_id else task_id
    is_task = "-T" in task_id

    if is_task:
        return f"""# Task: {title}

## 🎯 OBJECTIVE
Execute this task following BACON-AI deterministic methodology.

## 🤖 AGENT SYSTEM PROMPT
```
You are a BACON-AI Task Execution Agent.
Task ID: {task_id}
Phase: {phase_num}

DETERMINISTIC EXECUTION:
1. Check prerequisites/dependencies
2. Execute task steps in order
3. Document all outputs
4. Log lessons learned
5. Update task status
```

## 🔧 STANDARD MCP TOOLS
- `mcp__mcp-bacon-memory__memory_query_proven_approaches` - Check existing solutions
- `mcp__mcp-bacon-memory__memory_log_lesson_learned` - Log findings

## 📝 LESSON LEARNED TEMPLATE
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="{task_id}: [SUMMARY]. Insight: [KEY_INSIGHT]",
    severity="info",
    context="{task_id}"
)
```

## ✅ SUCCESS CRITERIA
- [ ] Prerequisites verified
- [ ] Task executed completely
- [ ] Outputs documented
- [ ] Lesson logged
"""
    else:
        return f"""# {title}

## 🎯 PURPOSE
Phase {phase_num[-4:]} of the BACON-AI 12-Phase Framework.

## 🤖 PHASE LEAD AGENT PROMPT
```
You are the BACON-AI Phase {phase_num[-4:]} Lead.
Ensure all subtasks complete before phase transition.
```

## 📋 PHASE COMPLETION
- All subtasks must show COMPLETED status
- Lessons learned logged
- Ready for next phase

## 🔄 SELF-LEARNING
```python
mcp__mcp-bacon-memory__memory_store_proven_approach(
    content="{phase_num} completed: [SUMMARY]",
    tags=["phase-{phase_num[-4:]}", "bacon-ai"],
    verification_count=1
)
```
"""

def generate_standard_checklist(task_id: str) -> List[Dict]:
    """Generate standard checklist for remaining tasks."""
    is_task = "-T" in task_id

    if is_task:
        return [
            {"text": "📥 INIT: Check prerequisites/dependencies", "checked": False},
            {"text": "🔍 Query lessons learned for similar tasks", "checked": False},
            {"text": "📋 Execute task step 1", "checked": False},
            {"text": "📋 Execute task step 2", "checked": False},
            {"text": "📋 Execute task step 3", "checked": False},
            {"text": "📝 Document outputs", "checked": False},
            {"text": "📝 Log lesson learned to bacon-memory", "checked": False},
            {"text": "✅ VERIFY: All criteria met", "checked": False},
        ]
    else:
        return [
            {"text": "🚦 GATE: Confirm previous phase complete", "checked": False},
            {"text": "📥 Load previous phase outputs", "checked": False},
            {"text": "📋 Execute all subtasks", "checked": False},
            {"text": "📝 Log phase lessons to bacon-memory", "checked": False},
            {"text": "🚦 GATE: All subtasks complete before next phase", "checked": False},
        ]


async def main():
    print("=" * 70)
    print("BACON-AI Comprehensive Task Updater")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Get all existing cards
        url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks?type=card"
        response = await client.get(url, headers=get_headers())

        if response.status_code != 200:
            print(f"Failed to get blocks: {response.status_code}")
            return

        blocks = response.json()
        print(f"Found {len(blocks)} existing cards")

        # Build lookup by old pattern
        card_lookup = {}
        for block in blocks:
            title = block.get("title", "")
            card_lookup[title] = block

        # Process detailed tasks
        updated = 0
        for task_key, task_data in TASKS.items():
            old_pattern = task_data.get("old_pattern", task_key)

            # Find matching card
            matching_card = None
            for title, block in card_lookup.items():
                if title.startswith(old_pattern):
                    matching_card = block
                    break

            if matching_card:
                card_id = matching_card["id"]
                success = await update_card(
                    client, card_id, task_data["title"], task_data["icon"],
                    task_data["task_id"], task_data["priority"], task_data["hours"],
                    task_data["description"], task_data["checklist"]
                )
                if success:
                    updated += 1
                    print(f"✅ {task_data['task_id']}: {task_data['title'][:40]}...")
            else:
                print(f"⚠️ Not found: {old_pattern}")

        # Process remaining phases
        for task_key, (title, icon, task_id, priority, hours) in REMAINING_PHASES.items():
            # Map old pattern
            old_key = task_key.replace("P000", "P0").replace("P001", "P1").replace("P002", "P2")
            old_key = old_key.replace("P003", "P3").replace("P004", "P4").replace("P005", "P5")
            old_key = old_key.replace("P006", "P6").replace("P007", "P7").replace("P008", "P8")
            old_key = old_key.replace("P009", "P9").replace("P0010", "P10").replace("P0011", "P11")
            old_key = old_key.replace("P0012", "P12")

            old_pattern = old_key + " " if "-" not in old_key else old_key.replace("-T", "-T0")

            # Find matching card
            matching_card = None
            for card_title, block in card_lookup.items():
                if card_title.startswith(old_pattern.strip()):
                    matching_card = block
                    break

            if matching_card:
                card_id = matching_card["id"]
                new_title = f"{task_id} ── {title}"
                description = generate_standard_description(task_id, title)
                checklist = generate_standard_checklist(task_id)

                success = await update_card(
                    client, card_id, new_title, icon,
                    task_id, priority, hours,
                    description, checklist
                )
                if success:
                    updated += 1
                    print(f"✅ {task_id}: {title[:40]}...")

        print()
        print("=" * 70)
        print(f"Update Complete: {updated} tasks updated")
        print("=" * 70)


async def update_card(
    client: httpx.AsyncClient,
    card_id: str,
    title: str,
    icon: str,
    task_id: str,
    priority: str,
    hours: str,
    description: str,
    checklist: List[Dict]
) -> bool:
    """Update a card with all details."""

    # Update card properties
    patch_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks/{card_id}"

    # Get current card to preserve existing properties
    get_response = await client.get(
        f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks?type=card",
        headers=get_headers()
    )

    current_card = None
    if get_response.status_code == 200:
        for block in get_response.json():
            if block["id"] == card_id:
                current_card = block
                break

    if not current_card:
        return False

    # Merge properties
    current_props = current_card.get("fields", {}).get("properties", {})
    current_props[NUMBER_PROP_ID] = task_id
    current_props[PRIORITY_PROP_ID] = priority
    current_props[HOURS_PROP_ID] = hours

    # Update card
    patch_data = {
        "title": title,
        "updatedFields": {
            "icon": icon,
            "properties": current_props
        }
    }

    patch_response = await client.patch(patch_url, headers=get_headers(), json=patch_data)

    if patch_response.status_code != 200:
        return False

    # Create/update content blocks for description and checklist
    await create_content_blocks(client, card_id, description, checklist)

    return True


async def create_content_blocks(
    client: httpx.AsyncClient,
    card_id: str,
    description: str,
    checklist: List[Dict]
) -> None:
    """Create content blocks for description and checklist."""

    # Get existing blocks for this card
    blocks_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks"
    response = await client.get(blocks_url, headers=get_headers())

    existing_blocks = []
    if response.status_code == 200:
        existing_blocks = [b for b in response.json() if b.get("parentId") == card_id]

    # Delete existing content blocks (we'll recreate them)
    for block in existing_blocks:
        if block.get("type") in ["text", "checkbox"]:
            delete_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks/{block['id']}"
            await client.delete(delete_url, headers=get_headers())

    # Create description text block
    desc_block = {
        "type": "text",
        "parentId": card_id,
        "boardId": BOARD_ID,
        "title": description,
        "fields": {}
    }

    await client.post(blocks_url, headers=get_headers(), json=[desc_block])

    # Create checklist blocks
    for item in checklist:
        checkbox_block = {
            "type": "checkbox",
            "parentId": card_id,
            "boardId": BOARD_ID,
            "title": item["text"],
            "fields": {"value": item.get("checked", False)}
        }
        await client.post(blocks_url, headers=get_headers(), json=[checkbox_block])


if __name__ == "__main__":
    asyncio.run(main())
