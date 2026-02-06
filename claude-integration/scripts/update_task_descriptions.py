#!/usr/bin/env python3
"""
Update all BACON-AI Focalboard tasks with:
- Unique task ID in Number property
- Detailed description with AI agent instructions
- Skills, MCP tools, and system prompts
- Subtask guidance and parallel execution hints
- Lessons learned integration
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuration
FOCALBOARD_URL = "http://localhost:8000"
AUTH_TOKEN = "k77tg84g87pd6tjk7rdho1kqs9h"
BOARD_ID = "bd5mw98s3cjftjnef77q8c4oone"

# Property IDs
NUMBER_PROP_ID = "a5p9bpedehti9yph1uuehqighue"

def get_headers():
    return {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

# Task descriptions with AI agent instructions
TASK_DESCRIPTIONS = {
    # Phase 0: Verification
    "P00": {
        "title": "P00 ── Phase 0: Verification (Critical Pre-Phase)",
        "task_id": 0,
        "description": """# Phase 0: Verification (Critical Pre-Phase)

## Purpose
MANDATORY gate before any work begins. Prevents reinventing the wheel and ensures we build on existing knowledge.

## System Prompt for Lead Agent
```
You are the BACON-AI Verification Agent. Your role is to ensure NO work begins until existing solutions and lessons learned have been thoroughly reviewed. You are the guardian of organizational memory and must enforce the CHECK-FIRST pattern.

CRITICAL: Block progression to Phase 1 until ALL verification tasks show GREEN status.
```

## Phase Completion Criteria
- [ ] All 5 verification tasks completed
- [ ] No existing solution found (or adaptation plan created)
- [ ] Lessons learned documented and applied
- [ ] Current state baseline established

## Parallel Agent Opportunities
- T01-T03 can run in PARALLEL (no dependencies)
- T04-T05 depend on T01-T03 completion

## MCP Tools Required
- `mcp__mcp-bacon-memory__memory_query_proven_approaches`
- `mcp__mcp-bacon-memory__memory_log_lesson_learned`
- `WebSearch` for current best practices
- `groq-chat`, `openai-chat`, `gemini-chat` for AI consultations

## Skills Reference
- `/lessons-learned` - Query and update lessons
- `/groq-chat` - Fast multi-model consultation
- `/cross-model-consultation` - Verify with external AI

## Self-Learning Integration
At phase end, log lessons learned:
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="[What we learned in verification]",
    severity="info",
    context="Phase 0 Verification - Project: [NAME]"
)
```
"""
    },

    "P00-T01": {
        "title": "P00-T01 ── Query lessons learned database",
        "task_id": 1,
        "description": """# Task: Query Lessons Learned Database

## Objective
Search organizational memory for existing solutions, patterns, and gotchas related to current problem.

## System Prompt for Agent
```
You are a Knowledge Retrieval Specialist. Query the lessons learned database comprehensively using multiple search strategies. Your goal is to find ALL relevant prior knowledge that could inform this project.

Search strategies:
1. Direct keyword match on problem domain
2. Related technology patterns
3. Similar project types
4. Known anti-patterns and failures
```

## Execution Steps
1. **Identify search terms** from problem statement
2. **Query proven approaches**:
   ```python
   mcp__mcp-bacon-memory__memory_query_proven_approaches(
       query="[problem domain keywords]",
       tags=["relevant", "tags"],
       min_verification_count=1
   )
   ```
3. **Search lessons learned** with multiple queries
4. **Document findings** in structured format

## Parallel Agent Prompt
```
While main agent searches lessons learned, you should:
1. Prepare summary template for findings
2. Identify knowledge gap areas for web search (T02)
3. Draft questions for external AI consultation (T03)
```

## Expected Output
- List of relevant lessons learned (with IDs)
- Applicable proven approaches
- Identified knowledge gaps
- Recommendations for next tasks

## MCP Tools
- `mcp__mcp-bacon-memory__memory_query_proven_approaches`
- `mcp__mcp-bacon-memory__memory_get_sync_status`

## Success Criteria
- [ ] Minimum 3 search queries executed
- [ ] All relevant lessons documented
- [ ] Knowledge gaps identified
- [ ] Handoff notes prepared for T02/T03

## Lessons Learned Log (End of Task)
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Lessons learned query for [PROJECT]: Found [N] relevant entries. Key insights: [SUMMARY]. Gaps identified: [GAPS]",
    severity="info",
    context="P00-T01 Query Lessons Learned"
)
```
"""
    },

    "P00-T02": {
        "title": "P00-T02 ── Web search current best practices",
        "task_id": 2,
        "description": """# Task: Web Search Current Best Practices

## Objective
Research current industry best practices, recent developments, and state-of-the-art solutions for the problem domain.

## System Prompt for Agent
```
You are a Research Specialist with expertise in finding authoritative, current information. Your training data may be outdated - ALWAYS verify with fresh web searches. Focus on:
1. Official documentation (2024-2026)
2. Industry best practices
3. Recent case studies
4. Known pitfalls and solutions
```

## Execution Steps
1. **Formulate search queries** based on problem + knowledge gaps from T01
2. **Execute web searches**:
   ```python
   WebSearch(query="[topic] best practices 2026")
   WebSearch(query="[technology] implementation guide")
   WebSearch(query="[problem type] common pitfalls")
   ```
3. **Fetch and analyze** key resources:
   ```python
   WebFetch(url="[authoritative source]", prompt="Extract key best practices for [topic]")
   ```
4. **Synthesize findings** into actionable recommendations

## Parallel Agent Prompt
```
While main agent searches web, you should:
1. Monitor for emerging patterns across search results
2. Identify contradictory advice that needs resolution
3. Prepare comparison matrix for T03 AI consultation
4. Draft ultrathink prompts for deep analysis
```

## Expected Output
- Summary of current best practices
- Links to authoritative sources
- Identified trends and patterns
- Contradictions requiring expert resolution

## MCP Tools
- `WebSearch` - Multiple targeted queries
- `WebFetch` - Deep dive on key resources

## Success Criteria
- [ ] Minimum 5 search queries executed
- [ ] 3+ authoritative sources reviewed
- [ ] Best practices documented with sources
- [ ] Contradictions flagged for T03

## Lessons Learned Log (End of Task)
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Web research for [PROJECT]: Key findings - [SUMMARY]. Best sources: [URLS]. Contradictions found: [LIST]",
    severity="info",
    context="P00-T02 Web Search Best Practices"
)
```
"""
    },

    "P00-T03": {
        "title": "P00-T03 ── Consult external AI models",
        "task_id": 3,
        "description": """# Task: Consult External AI Models

## Objective
Get second opinions from multiple AI models to validate understanding and identify blind spots.

## System Prompt for Agent
```
You are a Multi-Model Consultation Coordinator. Your role is to query multiple AI models with the same problem statement and synthesize their diverse perspectives. Each model has different training data and biases - leverage this diversity.

Models to consult:
- GPT-4o/GPT-5 (OpenAI) - Strong reasoning
- Gemini 2.5 (Google) - Recent training data
- Llama 70B/Qwen (Groq) - Fast, diverse perspectives
- Claude (via API) - Nuanced analysis
```

## Execution Steps
1. **Prepare consultation prompt**:
   ```
   Problem: [PROBLEM STATEMENT]
   Context: [RELEVANT CONTEXT]
   Question: What are the key considerations, potential pitfalls, and recommended approaches for this problem?
   ```

2. **Query multiple models**:
   ```python
   # Groq models (fast)
   mcp__groq-chat__llama_33_70b_chat(message="[prompt]", system_prompt="You are a technical advisor...")
   mcp__groq-chat__qwen3_32b_chat(message="[prompt]", system_prompt="...")

   # OpenAI
   mcp__openai-chat__gpt4o_chat(message="[prompt]", system_prompt="...")

   # Gemini
   mcp__gemini-chat__gemini_25_flash_chat(message="[prompt]", system_prompt="...")
   ```

3. **Synthesize responses** into consensus and divergence report

## Parallel Agent Prompt
```
While main agent consults AI models, you should:
1. Prepare a comparison matrix template
2. Identify areas of consensus vs disagreement
3. Flag novel insights not in T01/T02
4. Draft follow-up questions for divergent opinions
```

## Expected Output
- Responses from 4+ AI models
- Consensus summary
- Divergence analysis
- Novel insights identified
- Recommended approach synthesis

## MCP Tools
- `mcp__groq-chat__llama_33_70b_chat`
- `mcp__groq-chat__qwen3_32b_chat`
- `mcp__openai-chat__gpt4o_chat`
- `mcp__gemini-chat__gemini_25_flash_chat`
- `mcp__ai-reasoning__consensus_analysis`

## Success Criteria
- [ ] 4+ models consulted
- [ ] Consensus areas documented
- [ ] Divergent opinions analyzed
- [ ] Novel insights captured

## Lessons Learned Log (End of Task)
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="AI consultation for [PROJECT]: Models agreed on [CONSENSUS]. Disagreed on [DIVERGENCE]. Novel insight: [INSIGHT]",
    severity="info",
    context="P00-T03 External AI Consultation"
)
```
"""
    },

    "P00-T04": {
        "title": "P00-T04 ── Document current state and assumptions",
        "task_id": 4,
        "description": """# Task: Document Current State and Assumptions

## Objective
Create a comprehensive baseline document capturing the current state, all assumptions, and decision rationale.

## System Prompt for Agent
```
You are a Documentation Specialist focused on creating clear, comprehensive baseline documents. Your documentation must be detailed enough that any agent (human or AI) can understand the starting point without additional context.

Document Structure:
1. Current State Assessment
2. Explicit Assumptions (numbered)
3. Implicit Assumptions (identified)
4. Decision Rationale
5. Open Questions
```

## Execution Steps
1. **Compile findings** from T01, T02, T03
2. **Document current state**:
   - System boundaries
   - Existing components
   - Known constraints
   - Available resources

3. **List ALL assumptions**:
   - Technical assumptions
   - Business assumptions
   - Resource assumptions
   - Timeline assumptions

4. **Record decision rationale** for each assumption

## Parallel Agent Prompt
```
While main agent documents, you should:
1. Review T01-T03 outputs for undocumented assumptions
2. Identify potential risks from assumptions
3. Prepare validation questions for T05
4. Draft stakeholder review checklist
```

## Expected Output
- Current State Document (structured markdown)
- Numbered assumptions list with rationale
- Risk register draft
- Open questions for validation

## Template
```markdown
# Current State Baseline - [PROJECT NAME]
Date: [DATE]
Phase: P00-T04

## 1. Current State
### System Context
[Description]

### Existing Components
- Component 1: [status]
- Component 2: [status]

## 2. Explicit Assumptions
| ID | Assumption | Rationale | Risk Level |
|----|------------|-----------|------------|
| A1 | ... | ... | Low/Med/High |

## 3. Open Questions
1. [Question needing validation]
```

## Success Criteria
- [ ] Current state fully documented
- [ ] All assumptions numbered and rationalized
- [ ] Risks identified per assumption
- [ ] Document ready for T05 validation

## Lessons Learned Log (End of Task)
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Baseline documentation for [PROJECT]: [N] assumptions documented, [M] high-risk items identified. Key insight: [INSIGHT]",
    severity="info",
    context="P00-T04 Current State Documentation"
)
```
"""
    },

    "P00-T05": {
        "title": "P00-T05 ── Validate problem not already solved",
        "task_id": 5,
        "description": """# Task: Validate Problem Not Already Solved

## Objective
Final gate check - confirm the problem requires new work and isn't already solved internally or externally.

## System Prompt for Agent
```
You are the Validation Gate Agent. Your role is CRITICAL - you must verify that proceeding to Phase 1 is justified. Ask hard questions:
1. Is there an existing solution we missed?
2. Can we adapt an existing solution instead of building new?
3. Is this problem worth solving given effort vs value?
4. Are we solving the right problem?

Be skeptical. Challenge assumptions. Protect the team from unnecessary work.
```

## Execution Steps
1. **Review all T01-T04 outputs**
2. **Cross-reference** with:
   - Internal tools/systems
   - Commercial solutions
   - Open source options
   - Partner capabilities

3. **Decision matrix**:
   | Option | Effort | Value | Risk | Recommendation |
   |--------|--------|-------|------|----------------|
   | Build new | | | | |
   | Adapt existing | | | | |
   | Buy/license | | | | |
   | Partner | | | | |

4. **Make GO/NO-GO recommendation**

## Parallel Agent Prompt
```
While main agent validates, you should:
1. Prepare Phase 1 kickoff materials (optimistic path)
2. Draft alternative recommendation if NO-GO
3. Identify quick wins regardless of decision
4. Update lessons learned with validation process
```

## Expected Output
- Validation report
- Decision matrix with scores
- GO/NO-GO recommendation with rationale
- Next steps for either decision

## Decision Criteria
**GO if:**
- No existing solution adequately solves problem
- Value justifies effort
- Team has required capabilities
- Timeline is feasible

**NO-GO if:**
- Existing solution found
- Value doesn't justify effort
- Critical capability missing
- Better alternatives available

## Success Criteria
- [ ] All alternatives evaluated
- [ ] Decision matrix completed
- [ ] Recommendation documented with rationale
- [ ] Phase 0 summary prepared

## Lessons Learned Log (End of Task)
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Validation gate for [PROJECT]: Decision [GO/NO-GO]. Rationale: [SUMMARY]. Alternatives considered: [LIST]",
    severity="info",
    context="P00-T05 Validation Gate"
)

# If validated, store as proven approach
mcp__mcp-bacon-memory__memory_store_proven_approach(
    content="Phase 0 verification process completed successfully for [PROJECT TYPE]. Key success factors: [LIST]",
    tags=["phase-0", "verification", "validated"],
    verification_count=1
)
```
"""
    },

    # Phase 1: Problem Definition
    "P01": {
        "title": "P01 ── Phase 1: Problem Definition (Design Thinking)",
        "task_id": 100,
        "description": """# Phase 1: Problem Definition (Design Thinking)

## Purpose
Apply Design Thinking methodology to deeply understand the problem from multiple perspectives before generating solutions.

## System Prompt for Lead Agent
```
You are the BACON-AI Design Thinking Facilitator. Your role is to ensure the team deeply understands the problem BEFORE jumping to solutions. Use empathy mapping, 5W+1H analysis, and Six Thinking Hats to achieve comprehensive problem understanding.

CRITICAL: No solution discussion allowed in this phase. Focus purely on problem understanding.
```

## Phase Completion Criteria
- [ ] Empathy map completed for all stakeholders
- [ ] Problem statement refined using 5W+1H
- [ ] Six Thinking Hats review conducted
- [ ] Success criteria quantified
- [ ] Stakeholder approval obtained

## Parallel Agent Opportunities
- T01-T02 can run in PARALLEL
- T03 depends on T01-T02
- T04-T05 sequential (need T03 output)

## MCP Tools Required
- `mcp__mcp-bacon-memory__*` for lessons learned
- AI chat tools for perspective generation
- `mcp__mcp-etherpad-hub__*` for collaborative documents

## Skills Reference
- `/triz-innovation` - TRIZ methodology
- `/bacon-ai-perspective-analyst` - Six Thinking Hats
- `/bacon-ai-human-experience` - Design Thinking

## Self-Learning Integration
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Problem definition for [PROJECT]: Key insight from empathy mapping - [INSIGHT]. Surprising finding: [FINDING]",
    severity="info",
    context="Phase 1 Problem Definition"
)
```
"""
    },

    "P01-T01": {
        "title": "P01-T01 ── Create empathy map",
        "task_id": 101,
        "description": """# Task: Create Empathy Map

## Objective
Build deep understanding of all stakeholders by mapping what they Think, Feel, Say, and Do.

## System Prompt for Agent
```
You are an Empathy Mapping Specialist. Your role is to understand stakeholders deeply - not just their stated needs but their underlying motivations, fears, and aspirations.

For each stakeholder, explore:
- THINK: What occupies their mind? Worries? Aspirations?
- FEEL: Emotions about current situation and desired future
- SAY: What do they express to others?
- DO: Observable behaviors and actions
- PAIN: Frustrations, obstacles, fears
- GAIN: Wants, needs, measures of success
```

## Execution Steps
1. **Identify all stakeholders**:
   - Primary users
   - Secondary users
   - Administrators
   - Business sponsors
   - Technical team

2. **For each stakeholder**, complete empathy map:
   ```markdown
   ## Stakeholder: [NAME/ROLE]

   ### THINK
   - [What are they thinking about?]

   ### FEEL
   - [Emotional state and drivers]

   ### SAY
   - [Direct quotes or paraphrased statements]

   ### DO
   - [Observable actions]

   ### PAINS
   - [Frustrations and fears]

   ### GAINS
   - [Desired outcomes]
   ```

3. **Synthesize insights** across all stakeholders

## Parallel Agent Prompt
```
While main agent creates empathy maps, you should:
1. Research personas similar to identified stakeholders
2. Prepare questions for 5W+1H analysis (T02)
3. Identify potential conflicts between stakeholder needs
4. Draft preliminary user journey outline
```

## MCP Tools
- `mcp__ai-reasoning__ask_gemini_detailed` - Deep persona analysis
- `mcp__bacon-chat__send_message` - Stakeholder consultation
- `mcp__mcp-etherpad-hub__etherpad_write_pad` - Collaborative documentation

## Success Criteria
- [ ] All stakeholder groups identified
- [ ] Empathy map completed for each
- [ ] Cross-stakeholder insights synthesized
- [ ] Conflicts and alignments documented

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Empathy mapping for [PROJECT]: Identified [N] stakeholder groups. Key insight: [INSIGHT]. Conflict area: [CONFLICT]",
    severity="info",
    context="P01-T01 Empathy Mapping"
)
```
"""
    },

    "P01-T02": {
        "title": "P01-T02 ── Define problem using 5W+1H framework",
        "task_id": 102,
        "description": """# Task: Define Problem Using 5W+1H Framework

## Objective
Create a precise, comprehensive problem statement using the 5W+1H (Who, What, When, Where, Why, How) framework.

## System Prompt for Agent
```
You are a Problem Definition Specialist. Your role is to ensure the problem is defined with crystal clarity before any solution work begins. Ambiguity in problem definition leads to wasted effort.

Apply rigorous questioning:
- WHO is affected? Who causes it? Who cares?
- WHAT exactly is the problem? What is NOT the problem?
- WHEN does it occur? When did it start? When is it worst?
- WHERE does it happen? Where does it NOT happen?
- WHY does it matter? Why now? Why this priority?
- HOW does it manifest? How severe? How frequent?
```

## Execution Steps
1. **Answer each W+H dimension**:
   ```markdown
   ## Problem Definition: 5W+1H Analysis

   ### WHO
   - Affected: [List all affected parties]
   - Causes: [Who/what causes the problem]
   - Stakeholders: [Who has interest in solution]

   ### WHAT
   - Problem: [Precise problem statement]
   - NOT the problem: [What's out of scope]
   - Symptoms vs Root Cause: [Distinguish them]

   ### WHEN
   - Timeline: [When problem occurs]
   - Trigger: [What triggers it]
   - Pattern: [Frequency and regularity]

   ### WHERE
   - Location: [Where problem manifests]
   - Boundaries: [Where it doesn't occur]
   - Context: [Environmental factors]

   ### WHY
   - Impact: [Why this matters]
   - Urgency: [Why solve now]
   - Priority: [Why this over other problems]

   ### HOW
   - Manifestation: [How problem appears]
   - Severity: [Impact measurement]
   - Current workarounds: [How people cope]
   ```

2. **Synthesize into problem statement**:
   "For [WHO], who [PAIN/NEED], the [SOLUTION] is a [CATEGORY] that [KEY BENEFIT]. Unlike [ALTERNATIVES], our solution [DIFFERENTIATOR]."

## Parallel Agent Prompt
```
While main agent applies 5W+1H, you should:
1. Validate answers against empathy maps (T01)
2. Identify gaps requiring more research
3. Prepare Six Thinking Hats prompts (T03)
4. Draft success metrics based on WHO/WHY
```

## Success Criteria
- [ ] All 6 dimensions thoroughly answered
- [ ] Problem statement synthesized
- [ ] Scope boundaries clear
- [ ] Root cause vs symptoms distinguished

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="5W+1H analysis for [PROJECT]: Root cause identified as [CAUSE]. Problem scoped to [BOUNDARIES]. Key insight: [INSIGHT]",
    severity="info",
    context="P01-T02 5W+1H Problem Definition"
)
```
"""
    },

    "P01-T03": {
        "title": "P01-T03 ── Apply Six Thinking Hats review",
        "task_id": 103,
        "description": """# Task: Apply Six Thinking Hats Review

## Objective
Review problem definition from six distinct perspectives to ensure comprehensive understanding and identify blind spots.

## System Prompt for Agent
```
You are a Six Thinking Hats Facilitator. Your role is to ensure the problem has been examined from ALL perspectives before proceeding. Each hat represents a different thinking mode:

⚪ WHITE HAT: Facts, data, information
🔴 RED HAT: Emotions, intuition, gut feelings
⚫ BLACK HAT: Caution, risks, problems
🟡 YELLOW HAT: Benefits, optimism, opportunities
🟢 GREEN HAT: Creativity, alternatives, new ideas
🔵 BLUE HAT: Process, meta-thinking, next steps

CRITICAL: Process each hat FULLY before moving to the next. No mixing perspectives.
```

## Execution Steps
1. **For each hat, conduct dedicated analysis**:

   ```markdown
   ## Six Thinking Hats Analysis

   ### ⚪ WHITE HAT (Facts)
   - What data do we have?
   - What data is missing?
   - What are the verified facts?
   - What assumptions need validation?

   ### 🔴 RED HAT (Emotions)
   - How do stakeholders FEEL about this?
   - What's our gut reaction?
   - What emotional resistance might exist?
   - What excites people about solving this?

   ### ⚫ BLACK HAT (Risks)
   - What could go wrong?
   - What are the dangers?
   - What obstacles exist?
   - Why might solutions fail?

   ### 🟡 YELLOW HAT (Benefits)
   - What are the potential benefits?
   - Who gains from solving this?
   - What opportunities does this create?
   - Best case scenario?

   ### 🟢 GREEN HAT (Creativity)
   - Alternative ways to frame the problem?
   - Unconventional approaches?
   - What if assumptions were different?
   - Creative connections to other domains?

   ### 🔵 BLUE HAT (Process)
   - What have we learned?
   - What's the next step?
   - Who needs to be involved?
   - What's our timeline?
   ```

2. **Synthesize insights** from all hats

## Parallel Agent Prompt
```
Run parallel analysis with different AI models for each hat:
- GPT-5 for WHITE HAT (analytical)
- Gemini for GREEN HAT (creative)
- Claude for BLACK HAT (critical)
- Groq/Llama for RED HAT (diverse perspectives)

Synthesize their outputs for comprehensive coverage.
```

## MCP Tools
- `mcp__ai-reasoning__consensus_analysis` - Multi-model synthesis
- `mcp__groq-chat__*` - Multiple perspectives
- `Task` agent with `bacon-ai-perspective-analyst`

## Success Criteria
- [ ] All six hats applied thoroughly
- [ ] Key insights documented per hat
- [ ] Blind spots identified
- [ ] Synthesis completed

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Six Hats for [PROJECT]: BLACK HAT revealed [RISK]. GREEN HAT suggested [ALTERNATIVE]. Key blind spot: [BLINDSPOT]",
    severity="info",
    context="P01-T03 Six Thinking Hats"
)
```
"""
    },

    "P01-T04": {
        "title": "P01-T04 ── Document success criteria and constraints",
        "task_id": 104,
        "description": """# Task: Document Success Criteria and Constraints

## Objective
Define measurable success criteria and identify all constraints that will bound the solution space.

## System Prompt for Agent
```
You are a Requirements Engineer. Your role is to define MEASURABLE success criteria and identify ALL constraints. Vague criteria lead to scope creep and failed projects.

Apply SMART criteria:
- Specific: Exactly what must be achieved
- Measurable: How will we know it's achieved
- Achievable: Is it realistic
- Relevant: Does it address the problem
- Time-bound: By when

Also document:
- Must-have vs Nice-to-have
- Technical constraints
- Business constraints
- Resource constraints
```

## Execution Steps
1. **Define success criteria**:
   ```markdown
   ## Success Criteria (SMART)

   ### Must-Have (P0)
   | ID | Criterion | Measure | Target | Deadline |
   |----|-----------|---------|--------|----------|
   | SC1 | ... | ... | ... | ... |

   ### Should-Have (P1)
   | ID | Criterion | Measure | Target | Deadline |
   |----|-----------|---------|--------|----------|

   ### Nice-to-Have (P2)
   | ID | Criterion | Measure | Target | Deadline |
   |----|-----------|---------|--------|----------|
   ```

2. **Document constraints**:
   ```markdown
   ## Constraints

   ### Technical Constraints
   - [Technology stack limitations]
   - [Integration requirements]
   - [Performance requirements]

   ### Business Constraints
   - [Budget: $X]
   - [Timeline: X weeks]
   - [Regulatory requirements]

   ### Resource Constraints
   - [Team size and skills]
   - [Tool availability]
   - [External dependencies]
   ```

3. **Create acceptance test outline** for each criterion

## Parallel Agent Prompt
```
While main agent documents criteria, you should:
1. Research industry benchmarks for similar projects
2. Identify metrics collection mechanisms
3. Draft acceptance test cases for P0 criteria
4. Prepare stakeholder approval presentation (T05)
```

## Success Criteria (Meta)
- [ ] All criteria are SMART
- [ ] Constraints categorized and documented
- [ ] Acceptance tests outlined
- [ ] Stakeholder review ready

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Success criteria for [PROJECT]: [N] P0 criteria defined. Key constraint: [CONSTRAINT]. Measurement approach: [APPROACH]",
    severity="info",
    context="P01-T04 Success Criteria"
)
```
"""
    },

    "P01-T05": {
        "title": "P01-T05 ── Get stakeholder approval",
        "task_id": 105,
        "description": """# Task: Get Stakeholder Approval

## Objective
Present problem definition to stakeholders and obtain formal approval before proceeding to solution generation.

## System Prompt for Agent
```
You are a Stakeholder Communication Specialist. Your role is to present the problem definition clearly and obtain explicit approval. This is a GATE - no proceeding without approval.

Prepare for:
- Questions and challenges
- Scope negotiation
- Priority discussions
- Timeline concerns

Document ALL feedback, even if not incorporated.
```

## Execution Steps
1. **Prepare presentation**:
   ```markdown
   ## Problem Definition Review

   ### Executive Summary
   [1-paragraph problem statement]

   ### Stakeholder Impact
   [Who is affected and how]

   ### Proposed Scope
   [What's in and out of scope]

   ### Success Criteria
   [Key measurable outcomes]

   ### Constraints
   [Key limitations]

   ### Timeline
   [High-level phases]

   ### Request for Approval
   - [ ] Problem statement approved
   - [ ] Scope approved
   - [ ] Criteria approved
   - [ ] Proceed to Phase 2 approved
   ```

2. **Conduct review** (human in the loop)
3. **Document feedback** and decisions
4. **Update documents** based on feedback

## Parallel Agent Prompt
```
While awaiting stakeholder response, you should:
1. Prepare Phase 2 kickoff materials (optimistic)
2. Draft alternative scopes if negotiation needed
3. Identify Phase 2 quick-start tasks
4. Update lessons learned with preparation insights
```

## Success Criteria
- [ ] Presentation delivered
- [ ] All questions addressed
- [ ] Explicit approval obtained
- [ ] Feedback documented

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Stakeholder approval for [PROJECT]: Approved with [MODIFICATIONS]. Key feedback: [FEEDBACK]. Negotiation points: [POINTS]",
    severity="info",
    context="P01-T05 Stakeholder Approval"
)

# Phase 1 completion
mcp__mcp-bacon-memory__memory_store_proven_approach(
    content="Phase 1 Design Thinking approach for [PROJECT TYPE]: Effective techniques - [LIST]. Time spent: [HOURS]. Key success factor: [FACTOR]",
    tags=["phase-1", "design-thinking", "problem-definition"],
    verification_count=1
)
```
"""
    },

    # Phase 2: Data Gathering
    "P02": {
        "title": "P02 ── Phase 2: Data Gathering (Systems Thinking)",
        "task_id": 200,
        "description": """# Phase 2: Data Gathering (Systems Thinking)

## Purpose
Apply Systems Thinking to understand the broader context, boundaries, and interconnections of the problem space.

## System Prompt for Lead Agent
```
You are the BACON-AI Systems Thinking Facilitator. Your role is to ensure the team understands the SYSTEM context, not just the immediate problem. Map boundaries, stakeholders, feedback loops, and interconnections.

Key Systems Thinking principles:
1. Everything is connected
2. Look for patterns, not just events
3. Consider unintended consequences
4. Identify feedback loops (reinforcing and balancing)
5. Seek leverage points
```

## Phase Completion Criteria
- [ ] Context map with system boundaries
- [ ] Stakeholder analysis completed
- [ ] Data from all sources collected
- [ ] Existing documentation reviewed
- [ ] Data gaps identified and addressed

## Parallel Agent Opportunities
- T01-T02 can run in PARALLEL
- T03-T04 can run in PARALLEL
- T05 depends on all above

## MCP Tools Required
- `mcp__mcp-bacon-memory__*` for lessons learned
- `WebFetch` for documentation
- `Read`, `Glob`, `Grep` for codebase analysis

## Skills Reference
- `/bacon-ai-systems-architect` - Systems analysis
- `/documentation-writer` - Documentation review
- `/lessons-learned` - Knowledge integration

## Self-Learning Integration
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Systems analysis for [PROJECT]: Key feedback loop identified - [LOOP]. System boundary: [BOUNDARY]. Leverage point: [POINT]",
    severity="info",
    context="Phase 2 Data Gathering"
)
```
"""
    },

    "P02-T01": {
        "title": "P02-T01 ── Create context map of system boundaries",
        "task_id": 201,
        "description": """# Task: Create Context Map of System Boundaries

## Objective
Map the system boundaries, external interfaces, and context in which the solution will operate.

## System Prompt for Agent
```
You are a Systems Boundary Analyst. Your role is to clearly define what's INSIDE vs OUTSIDE the system boundary. Identify all interfaces, data flows, and external dependencies.

Key questions:
- What systems does this interact with?
- What data flows in and out?
- Who/what controls the interfaces?
- What assumptions about external systems?
```

## Execution Steps
1. **Draw context diagram**:
   ```
   +------------------+
   |  External        |
   |  System A   <----+---> [Our System] <---+--> External
   +------------------+                      |    System B
                                             v
                                       External System C
   ```

2. **Document each interface**:
   ```markdown
   ## System Interfaces

   ### Interface: [Name]
   - **Direction**: In/Out/Bidirectional
   - **Type**: API/File/Message/Manual
   - **Data**: [What flows]
   - **Owner**: [Who controls]
   - **SLA**: [Availability/Performance]
   - **Risk**: [What if fails]
   ```

3. **Identify boundary decisions**:
   - What's in scope to modify
   - What's fixed/given
   - What's negotiable

## Parallel Agent Prompt
```
While main agent maps boundaries, you should:
1. Research interface documentation for external systems
2. Identify similar integration patterns from lessons learned
3. Draft interface risk assessment
4. Prepare stakeholder interview questions (T02)
```

## Success Criteria
- [ ] Context diagram created
- [ ] All interfaces documented
- [ ] Boundary decisions explicit
- [ ] Risks per interface identified

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Context mapping for [PROJECT]: [N] external interfaces. Key risk: [INTERFACE] with [RISK]. Boundary decision: [DECISION]",
    severity="info",
    context="P02-T01 Context Mapping"
)
```
"""
    },

    "P02-T02": {
        "title": "P02-T02 ── Conduct stakeholder analysis",
        "task_id": 202,
        "description": """# Task: Conduct Stakeholder Analysis

## Objective
Identify and analyze all stakeholders, their interests, influence, and engagement strategy.

## System Prompt for Agent
```
You are a Stakeholder Analyst. Map all stakeholders by their interest and influence. Develop appropriate engagement strategies for each.

Stakeholder matrix:
- High Interest + High Influence = Manage Closely
- High Interest + Low Influence = Keep Informed
- Low Interest + High Influence = Keep Satisfied
- Low Interest + Low Influence = Monitor
```

## Execution Steps
1. **Identify all stakeholders**:
   - Direct users
   - Indirect users
   - System owners
   - Business sponsors
   - Technical team
   - Operations
   - Compliance/Security
   - External partners

2. **For each stakeholder**:
   ```markdown
   ## Stakeholder: [NAME/ROLE]

   - **Interest Level**: High/Medium/Low
   - **Influence Level**: High/Medium/Low
   - **Key Interests**: [What they care about]
   - **Potential Concerns**: [What might worry them]
   - **Current Engagement**: [How they're involved]
   - **Strategy**: [How to engage them]
   - **Communication Frequency**: [How often]
   ```

3. **Create stakeholder map** (visual matrix)

## Parallel Agent Prompt
```
While main agent analyzes stakeholders, you should:
1. Research organizational structure for stakeholder identification
2. Prepare interview questions per stakeholder type
3. Identify RACI matrix candidates
4. Draft communication plan template
```

## Success Criteria
- [ ] All stakeholders identified
- [ ] Interest/influence mapped
- [ ] Engagement strategy per stakeholder
- [ ] Communication plan drafted

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Stakeholder analysis for [PROJECT]: [N] stakeholders identified. Key influencer: [STAKEHOLDER]. Engagement insight: [INSIGHT]",
    severity="info",
    context="P02-T02 Stakeholder Analysis"
)
```
"""
    },

    "P02-T03": {
        "title": "P02-T03 ── Collect data from all sources",
        "task_id": 203,
        "description": """# Task: Collect Data from All Sources

## Objective
Gather all relevant data from identified sources to inform analysis and solution design.

## System Prompt for Agent
```
You are a Data Collection Specialist. Your role is to systematically gather data from all identified sources. Be thorough - missing data leads to flawed analysis.

Data categories:
- Quantitative: Metrics, logs, statistics
- Qualitative: Feedback, interviews, observations
- Historical: Past attempts, previous solutions
- Comparative: Benchmarks, industry data
```

## Execution Steps
1. **Identify data sources**:
   - System logs and metrics
   - User feedback
   - Support tickets
   - Performance data
   - Usage analytics
   - External benchmarks

2. **For each source**:
   ```markdown
   ## Data Source: [NAME]

   - **Type**: Quantitative/Qualitative
   - **Access Method**: [How to get it]
   - **Time Range**: [Period covered]
   - **Quality**: High/Medium/Low
   - **Gaps**: [What's missing]
   - **Key Findings**: [Summary]
   ```

3. **Aggregate and organize** data for analysis

## Parallel Agent Prompt
```
While main agent collects data, you should:
1. Set up data validation checks
2. Create data quality scorecard
3. Identify patterns in collected data
4. Prepare visualization templates for T04
```

## MCP Tools
- `Read`, `Glob`, `Grep` - Codebase analysis
- `WebFetch` - External documentation
- `Bash` - Log analysis commands

## Success Criteria
- [ ] All identified sources accessed
- [ ] Data quality assessed
- [ ] Gaps documented
- [ ] Data organized for analysis

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Data collection for [PROJECT]: [N] sources accessed. Data quality: [ASSESSMENT]. Key gap: [GAP]. Unexpected finding: [FINDING]",
    severity="info",
    context="P02-T03 Data Collection"
)
```
"""
    },

    "P02-T04": {
        "title": "P02-T04 ── Review existing documentation",
        "task_id": 204,
        "description": """# Task: Review Existing Documentation

## Objective
Thoroughly review all existing documentation related to the system and problem domain.

## System Prompt for Agent
```
You are a Documentation Analyst. Review all existing documentation to extract relevant information and identify gaps. Don't reinvent - leverage existing knowledge.

Documentation types to review:
- Architecture documents
- API specifications
- User guides
- Technical specifications
- Historical decisions (ADRs)
- Meeting notes
- Support documentation
```

## Execution Steps
1. **Locate all documentation**:
   ```bash
   # Find documentation files
   Glob("**/*.md")
   Glob("**/docs/**/*")
   Glob("**/*.adoc")
   Grep("README|ARCHITECTURE|DESIGN")
   ```

2. **For each document**:
   ```markdown
   ## Document: [NAME]

   - **Type**: Architecture/API/User/Technical
   - **Last Updated**: [Date]
   - **Relevance**: High/Medium/Low
   - **Key Information**: [Summary]
   - **Gaps/Issues**: [What's missing or outdated]
   - **Action Needed**: [Update/Archive/Reference]
   ```

3. **Create knowledge map** of documentation

## Parallel Agent Prompt
```
While main agent reviews docs, you should:
1. Index documentation for searchability
2. Identify contradictions between documents
3. Flag outdated information
4. Prepare documentation improvement list
```

## Success Criteria
- [ ] All relevant docs identified
- [ ] Each document reviewed and summarized
- [ ] Knowledge gaps documented
- [ ] Contradictions flagged

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Documentation review for [PROJECT]: [N] documents reviewed. Key finding: [FINDING]. Gap: [GAP]. Outdated: [LIST]",
    severity="info",
    context="P02-T04 Documentation Review"
)
```
"""
    },

    "P02-T05": {
        "title": "P02-T05 ── Identify data gaps and plan collection",
        "task_id": 205,
        "description": """# Task: Identify Data Gaps and Plan Collection

## Objective
Analyze collected data for gaps and create plan to address missing information.

## System Prompt for Agent
```
You are a Data Gap Analyst. Your role is to identify what's missing and create a practical plan to fill gaps. Not all gaps need filling - prioritize based on impact on decision-making.

Gap categories:
- Critical: Cannot proceed without
- Important: Significantly impacts decisions
- Nice-to-have: Would improve confidence
```

## Execution Steps
1. **Analyze data completeness**:
   ```markdown
   ## Data Gap Analysis

   ### Critical Gaps
   | Gap | Impact | Collection Method | Owner | Timeline |
   |-----|--------|-------------------|-------|----------|

   ### Important Gaps
   | Gap | Impact | Collection Method | Owner | Timeline |
   |-----|--------|-------------------|-------|----------|

   ### Nice-to-have Gaps
   | Gap | Impact | Collection Method | Owner | Timeline |
   |-----|--------|-------------------|-------|----------|
   ```

2. **Create collection plan**:
   - Methods: Surveys, interviews, experiments, research
   - Resources needed
   - Timeline
   - Success criteria

3. **Execute critical gap collection**

## Parallel Agent Prompt
```
While main agent analyzes gaps, you should:
1. Research alternative data sources
2. Design lightweight collection methods
3. Prepare Phase 3 analysis framework
4. Document data limitations for Phase 3
```

## Success Criteria
- [ ] All gaps categorized
- [ ] Collection plan for critical gaps
- [ ] Resources allocated
- [ ] Phase 3 readiness assessed

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Gap analysis for [PROJECT]: [N] critical gaps. Collection plan: [SUMMARY]. Limitation to acknowledge: [LIMITATION]",
    severity="info",
    context="P02-T05 Gap Analysis"
)

# Phase 2 completion
mcp__mcp-bacon-memory__memory_store_proven_approach(
    content="Phase 2 Systems Thinking data gathering for [PROJECT TYPE]: Effective sources - [LIST]. Gap handling: [APPROACH]",
    tags=["phase-2", "systems-thinking", "data-gathering"],
    verification_count=1
)
```
"""
    },

    # Continue with remaining phases...
    # Phase 3-12 follow similar detailed pattern
}

# Add remaining phase descriptions (abbreviated for space, following same pattern)
PHASE_TEMPLATES = {
    "P03": ("Phase 3: Analysis (TRIZ + Systems Thinking)", 300, "🔬", "Apply analytical frameworks to understand root causes and system dynamics."),
    "P03-T01": ("Create causal loop diagrams", 301, "🔄", "Map cause-effect relationships and feedback loops in the system."),
    "P03-T02": ("Apply TRIZ contradiction matrix", 302, "⚡", "Identify technical/physical contradictions and TRIZ solutions."),
    "P03-T03": ("Identify patterns from data", 303, "🔍", "Extract patterns and trends from collected data."),
    "P03-T04": ("Deep analysis (mindmaps, diagrams)", 304, "🧠", "Create visual analysis artifacts for comprehensive understanding."),
    "P03-T05": ("QA review with confidence levels", 305, "✅", "Review analysis quality and assign confidence levels."),

    "P04": ("Phase 4: Solution Generation (TRIZ 40 Principles)", 400, "💡", "Generate diverse solution ideas using TRIZ and parallel agents."),
    "P04-T01": ("Apply TRIZ 40 Inventive Principles", 401, "🛠️", "Systematically apply TRIZ principles to generate solutions."),
    "P04-T02": ("Parallel agent generation (5-10 agents)", 402, "🤖", "Spawn parallel AI agents for diverse solution generation."),
    "P04-T03": ("Collective discussion for more ideas", 403, "💬", "Facilitate cross-agent discussion to build on ideas."),
    "P04-T04": ("Compile master solution list (min 20)", 404, "📝", "Consolidate all solutions into comprehensive list."),
    "P04-T05": ("Enforce NO EVALUATION rule", 405, "🚫", "Ensure no premature evaluation during ideation."),

    "P05": ("Phase 5: Evaluation (Multi-Criteria Analysis)", 500, "⚖️", "Systematically evaluate solutions against criteria."),
    "P05-T01": ("Apply feasibility filtering", 501, "🔍", "Filter out infeasible solutions."),
    "P05-T02": ("Create multi-criteria scoring matrix", 502, "📊", "Build weighted scoring matrix."),
    "P05-T03": ("Apply Six Thinking Hats (Yellow/Black)", 503, "🎩", "Review solutions for benefits and risks."),
    "P05-T04": ("Conduct weighted voting by agents", 504, "🗳️", "Multi-agent voting on solutions."),
    "P05-T05": ("Identify top 3 solutions with scores", 505, "🏆", "Select top solutions for consensus."),

    "P06": ("Phase 6: Consensus Voting (Multi-Model + Human)", 600, "🗳️", "Achieve consensus through multi-model and human voting."),
    "P06-T01": ("Collect votes from BACON-AI agents", 601, "🤖", "Gather agent votes with reasoning."),
    "P06-T02": ("Consult external AI models", 602, "🌐", "Get external AI perspective."),
    "P06-T03": ("Get human vote (final authority)", 603, "👤", "Human decision maker casts deciding vote."),
    "P06-T04": ("Calculate consensus percentage", 604, "📊", "Compute consensus metrics."),
    "P06-T05": ("Apply decision rules", 605, "📋", "Apply predefined decision rules."),

    "P07": ("Phase 7: Design Excellence (Architecture)", 700, "🏗️", "Create excellent technical design."),
    "P07-T01": ("Create Architecture Decision Records", 701, "📄", "Document architectural decisions."),
    "P07-T02": ("Draw system architecture diagrams", 702, "📐", "Create visual architecture."),
    "P07-T03": ("Define component responsibilities", 703, "🧩", "Assign clear responsibilities."),
    "P07-T04": ("Identify design patterns to apply", 704, "🔧", "Select appropriate patterns."),
    "P07-T05": ("Specify quality attributes", 705, "⭐", "Define quality requirements."),

    "P08": ("Phase 8: Implementation Planning (Execution)", 800, "📋", "Plan implementation execution."),
    "P08-T01": ("Create Work Breakdown Structure", 801, "📝", "Break down work into tasks."),
    "P08-T02": ("Create dependency graph (Gantt)", 802, "📊", "Map task dependencies."),
    "P08-T03": ("Allocate resources (team, tools)", 803, "👥", "Assign resources to tasks."),
    "P08-T04": ("Document risk mitigation plan", 804, "⚠️", "Plan for known risks."),
    "P08-T05": ("Define success criteria & acceptance", 805, "✅", "Define done criteria."),

    "P09": ("Phase 9: TDD Build (Test-Driven Development)", 900, "🧪", "Build with TDD methodology."),
    "P09-T01": ("Establish test baseline", 901, "📊", "Set up testing infrastructure."),
    "P09-T02": ("RED: Write failing tests first", 902, "🔴", "Write tests before code."),
    "P09-T03": ("GREEN: Write code to pass tests", 903, "🟢", "Implement to pass tests."),
    "P09-T04": ("REFACTOR: Improve code quality", 904, "🔵", "Refactor while green."),
    "P09-T05": ("V-Model progression (TUT→FUT→SIT→UAT)", 905, "📈", "Progress through test levels."),
    "P09-T06": ("Verify >90% code coverage", 906, "✅", "Ensure adequate coverage."),

    "P10": ("Phase 10: Change Management (User Adoption)", 1000, "📣", "Manage organizational change."),
    "P10-T01": ("Create user training materials", 1001, "📚", "Develop training content."),
    "P10-T02": ("Prepare demo video/walkthrough", 1002, "🎬", "Create demo materials."),
    "P10-T03": ("Set up feedback collection", 1003, "💬", "Enable feedback mechanisms."),
    "P10-T04": ("Execute communication plan", 1004, "📢", "Communicate changes."),
    "P10-T05": ("Track adoption metrics", 1005, "📊", "Monitor adoption."),

    "P11": ("Phase 11: Deployment (Production Rollout)", 1100, "🚀", "Deploy to production."),
    "P11-T01": ("Complete pre-deployment checklist", 1101, "📋", "Verify deployment readiness."),
    "P11-T02": ("Run deployment automation", 1102, "⚙️", "Execute deployment."),
    "P11-T03": ("Execute health checks", 1103, "🏥", "Verify system health."),
    "P11-T04": ("Verify monitoring and alerting", 1104, "📡", "Confirm observability."),
    "P11-T05": ("Run smoke tests in production", 1105, "🧪", "Validate in production."),
    "P11-T06": ("Get UAT approval", 1106, "✔️", "Obtain final approval."),

    "P12": ("Phase 12: SSC Retrospective (Learning)", 1200, "🔄", "Learn and improve."),
    "P12-T01": ("Collect human feedback", 1201, "👤", "Gather human perspectives."),
    "P12-T02": ("Run agent SSC (Stop/Start/Continue)", 1202, "🤖", "Agent retrospective."),
    "P12-T03": ("Update SE-Agent trajectory memory", 1203, "🧠", "Update learning systems."),
    "P12-T04": ("Add lessons to database (min 3)", 1204, "📚", "Document lessons."),
    "P12-T05": ("Document proven patterns (min 4)", 1205, "📝", "Capture patterns."),
    "P12-T06": ("Assess organizational impact", 1206, "📊", "Measure impact."),
    "P12-T07": ("Execute dissemination plan", 1207, "📣", "Share learnings."),
}

def generate_detailed_description(task_key: str, title: str, task_id: int, icon: str, brief: str) -> str:
    """Generate detailed description for tasks not in TASK_DESCRIPTIONS."""

    # Determine phase from task_key
    phase_num = int(task_key[1:3]) if task_key[1:3].isdigit() else int(task_key[1:2])
    is_phase = "-" not in task_key

    if is_phase:
        return f"""# {title}

## Purpose
{brief}

## System Prompt for Lead Agent
```
You are the BACON-AI Phase {phase_num} Lead Agent. Your role is to orchestrate all tasks in this phase, ensure quality gates are met, and coordinate parallel execution where possible.

CRITICAL: Ensure all tasks complete with documented outputs before phase transition.
```

## Phase Completion Criteria
- [ ] All tasks in phase completed
- [ ] Quality review passed
- [ ] Lessons learned documented
- [ ] Ready for next phase

## MCP Tools Required
- `mcp__mcp-bacon-memory__*` for lessons learned
- Phase-specific tools as documented in tasks

## Skills Reference
- Check `/skills` directory for relevant skills
- `/lessons-learned` - Always query before starting

## Self-Learning Integration
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="Phase {phase_num} completed for [PROJECT]: Key outcomes - [OUTCOMES]. Time: [HOURS]. Improvement: [SUGGESTION]",
    severity="info",
    context="Phase {phase_num} Completion"
)
```
"""
    else:
        return f"""# Task: {title.split('── ')[1] if '── ' in title else title}

## Objective
{brief}

## System Prompt for Agent
```
You are a BACON-AI Task Agent executing {task_key}. Follow the execution steps precisely and document all outputs. Query lessons learned BEFORE starting and log lessons AFTER completing.

Task ID: {task_id}
Phase: {phase_num}
```

## Execution Steps
1. **Query lessons learned** for similar tasks
2. **Execute task** following standard methodology
3. **Document outputs** in structured format
4. **Log lessons learned** with insights

## Parallel Agent Prompt
```
While main agent executes this task, you should:
1. Prepare inputs for dependent tasks
2. Research best practices for this task type
3. Identify optimization opportunities
4. Draft lessons learned summary
```

## MCP Tools
- `mcp__mcp-bacon-memory__memory_query_proven_approaches`
- Task-specific tools as needed

## Skills Reference
- Query `/skills` for relevant capabilities
- `/lessons-learned` - Check before and log after

## Success Criteria
- [ ] Task objective achieved
- [ ] Output documented
- [ ] Quality verified
- [ ] Lessons logged

## Lessons Learned Log
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="{task_key} completed: [SUMMARY]. Insight: [INSIGHT]. Improvement: [SUGGESTION]",
    severity="info",
    context="{task_key}"
)
```
"""

async def update_card(client: httpx.AsyncClient, card_id: str, title: str, task_id: int, description: str) -> bool:
    """Update a single card with task ID and description."""
    url = f"{FOCALBOARD_URL}/api/v2/cards/{card_id}"

    # Update properties with task ID in Number field
    data = {
        "properties": {
            NUMBER_PROP_ID: str(task_id)
        }
    }

    try:
        response = await client.patch(url, headers=get_headers(), json=data)
        if response.status_code == 200:
            print(f"✅ Updated: {title} (ID: {task_id})")
            return True
        else:
            print(f"❌ Failed: {title} - {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {title} - {e}")
        return False

async def update_card_content(client: httpx.AsyncClient, card_id: str, description: str) -> bool:
    """Update card content/description via blocks API."""
    # First get the card to find content block
    url = f"{FOCALBOARD_URL}/api/v2/cards/{card_id}"

    try:
        response = await client.get(url, headers=get_headers())
        if response.status_code != 200:
            return False

        card = response.json()
        board_id = card.get("boardId", BOARD_ID)

        # Create or update content block
        content_block = {
            "type": "text",
            "parentId": card_id,
            "boardId": board_id,
            "title": description,
            "fields": {}
        }

        # Check for existing content blocks
        blocks_url = f"{FOCALBOARD_URL}/api/v2/boards/{board_id}/blocks?parent_id={card_id}"
        blocks_response = await client.get(blocks_url, headers=get_headers())

        if blocks_response.status_code == 200:
            blocks = blocks_response.json()
            text_blocks = [b for b in blocks if b.get("type") == "text"]

            if text_blocks:
                # Update existing
                block_id = text_blocks[0]["id"]
                update_url = f"{FOCALBOARD_URL}/api/v2/blocks/{block_id}"
                content_block["id"] = block_id
                await client.patch(update_url, headers=get_headers(), json=content_block)
            else:
                # Create new
                create_url = f"{FOCALBOARD_URL}/api/v2/blocks"
                await client.post(create_url, headers=get_headers(), json=[content_block])

        return True
    except Exception as e:
        print(f"Content update error: {e}")
        return False

async def main():
    """Main update function."""
    print("=" * 60)
    print("BACON-AI Task Description Updater")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get all cards
        url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/cards"
        response = await client.get(url, headers=get_headers())

        if response.status_code != 200:
            print(f"Failed to get cards: {response.status_code}")
            return

        cards = response.json()
        print(f"Found {len(cards)} cards to update")

        # Build card lookup by title prefix
        card_lookup = {}
        for card in cards:
            title = card.get("title", "")
            # Extract task key (e.g., "P00-T01" from "P00-T01 ── Query...")
            if title.startswith("P"):
                parts = title.split(" ── ")
                if parts:
                    key = parts[0].strip()
                    card_lookup[key] = card

        print(f"Matched {len(card_lookup)} task cards")

        # Update cards with detailed descriptions
        updated = 0
        failed = 0

        # First update cards with full descriptions from TASK_DESCRIPTIONS
        for key, desc_data in TASK_DESCRIPTIONS.items():
            if key in card_lookup:
                card = card_lookup[key]
                success = await update_card(
                    client,
                    card["id"],
                    desc_data["title"],
                    desc_data["task_id"],
                    desc_data["description"]
                )
                if success:
                    updated += 1
                else:
                    failed += 1

        # Then update remaining cards from PHASE_TEMPLATES
        for key, (title, task_id, icon, brief) in PHASE_TEMPLATES.items():
            if key in card_lookup and key not in TASK_DESCRIPTIONS:
                card = card_lookup[key]
                description = generate_detailed_description(key, title, task_id, icon, brief)
                success = await update_card(
                    client,
                    card["id"],
                    f"{key} ── {title}",
                    task_id,
                    description
                )
                if success:
                    updated += 1
                else:
                    failed += 1

        print()
        print("=" * 60)
        print(f"Update Complete: {updated} updated, {failed} failed")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
