#!/usr/bin/env python3
"""
Fix remaining BACON-AI tasks that weren't updated.

This script targets the subtasks that still have old naming format:
P02-T01 -> P0002-T0001
P03-T01 -> P0003-T0001
etc.
"""

import asyncio
import httpx
import re
from typing import Dict, List, Optional

# Configuration
FOCALBOARD_URL = "http://localhost:8000"
AUTH_TOKEN = "k77tg84g87pd6tjk7rdho1kqs9h"
BOARD_ID = "bd5mw98s3cjftjnef77q8c4oone"

# Property IDs
NUMBER_PROP_ID = "a5p9bpedehti9yph1uuehqighue"
PRIORITY_PROP_ID = "d3d682bf-e074-49d9-8df5-7320921c2d23"
HOURS_PROP_ID = "a8daz81s4xjgke1ww6cwik5w7ye"

# Priority options
PRIORITY_HIGH = "d3bfb50f-f569-4bad-8a3a-dd15c3f60101"
PRIORITY_MEDIUM = "87f59784-b859-4c24-8ebe-17c766e081dd"

def get_headers():
    return {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

# Mapping from old format to new format with details
# Format: old_prefix -> (new_task_id, title_suffix, icon, priority, hours)
TASK_MAPPING = {
    # Phase 2 subtasks
    "P02-T01": ("P0002-T0001", "Create context map of system boundaries", "🗺️", PRIORITY_HIGH, "3"),
    "P02-T02": ("P0002-T0002", "Conduct stakeholder analysis", "👥", PRIORITY_HIGH, "3"),
    "P02-T03": ("P0002-T0003", "Collect data from all sources", "📥", PRIORITY_HIGH, "4"),
    "P02-T04": ("P0002-T0004", "Review existing documentation", "📖", PRIORITY_MEDIUM, "3"),
    "P02-T05": ("P0002-T0005", "Identify data gaps and plan collection", "🔎", PRIORITY_HIGH, "3"),

    # Phase 3 subtasks
    "P03-T01": ("P0003-T0001", "Create causal loop diagrams", "🔄", PRIORITY_HIGH, "4"),
    "P03-T02": ("P0003-T0002", "Apply TRIZ contradiction matrix", "⚡", PRIORITY_HIGH, "4"),
    "P03-T03": ("P0003-T0003", "Identify patterns from data", "🔍", PRIORITY_HIGH, "4"),
    "P03-T04": ("P0003-T0004", "Deep analysis (mindmaps, diagrams)", "🧠", PRIORITY_MEDIUM, "4"),
    "P03-T05": ("P0003-T0005", "QA review with confidence levels", "✅", PRIORITY_HIGH, "4"),

    # Phase 4 subtasks
    "P04-T01": ("P0004-T0001", "Apply TRIZ 40 Inventive Principles", "🛠️", PRIORITY_HIGH, "4"),
    "P04-T02": ("P0004-T0002", "Parallel agent generation (5-10 agents)", "🤖", PRIORITY_HIGH, "4"),
    "P04-T03": ("P0004-T0003", "Collective discussion for more ideas", "💬", PRIORITY_MEDIUM, "3"),
    "P04-T04": ("P0004-T0004", "Compile master solution list (min 20)", "📝", PRIORITY_HIGH, "3"),
    "P04-T05": ("P0004-T0005", "Enforce NO EVALUATION rule", "🚫", PRIORITY_HIGH, "2"),

    # Phase 5 subtasks
    "P05-T01": ("P0005-T0001", "Apply feasibility filtering", "🔍", PRIORITY_HIGH, "3"),
    "P05-T02": ("P0005-T0002", "Create multi-criteria scoring matrix", "📊", PRIORITY_HIGH, "4"),
    "P05-T03": ("P0005-T0003", "Apply Six Thinking Hats (Yellow/Black)", "🎩", PRIORITY_MEDIUM, "3"),
    "P05-T04": ("P0005-T0004", "Conduct weighted voting by agents", "🗳️", PRIORITY_HIGH, "3"),
    "P05-T05": ("P0005-T0005", "Identify top 3 solutions with scores", "🏆", PRIORITY_HIGH, "3"),

    # Phase 6 subtasks
    "P06-T01": ("P0006-T0001", "Collect votes from BACON-AI agents", "🤖", PRIORITY_HIGH, "2"),
    "P06-T02": ("P0006-T0002", "Consult external AI models", "🌐", PRIORITY_HIGH, "2"),
    "P06-T03": ("P0006-T0003", "Get human vote (final authority)", "👤", PRIORITY_HIGH, "1"),
    "P06-T04": ("P0006-T0004", "Calculate consensus percentage", "📊", PRIORITY_MEDIUM, "1"),
    "P06-T05": ("P0006-T0005", "Apply decision rules", "📋", PRIORITY_HIGH, "2"),

    # Phase 7 subtasks
    "P07-T01": ("P0007-T0001", "Create Architecture Decision Records", "📄", PRIORITY_HIGH, "4"),
    "P07-T02": ("P0007-T0002", "Draw system architecture diagrams", "📐", PRIORITY_HIGH, "6"),
    "P07-T03": ("P0007-T0003", "Define component responsibilities", "🧩", PRIORITY_HIGH, "4"),
    "P07-T04": ("P0007-T0004", "Identify design patterns to apply", "🔧", PRIORITY_MEDIUM, "4"),
    "P07-T05": ("P0007-T0005", "Specify quality attributes", "⭐", PRIORITY_HIGH, "6"),

    # Phase 8 subtasks
    "P08-T01": ("P0008-T0001", "Create Work Breakdown Structure", "📝", PRIORITY_HIGH, "4"),
    "P08-T02": ("P0008-T0002", "Create dependency graph (Gantt)", "📊", PRIORITY_HIGH, "3"),
    "P08-T03": ("P0008-T0003", "Allocate resources (team, tools)", "👥", PRIORITY_HIGH, "3"),
    "P08-T04": ("P0008-T0004", "Document risk mitigation plan", "⚠️", PRIORITY_HIGH, "3"),
    "P08-T05": ("P0008-T0005", "Define success criteria & acceptance", "✅", PRIORITY_HIGH, "3"),

    # Phase 9 subtasks
    "P09-T01": ("P0009-T0001", "Establish test baseline", "📊", PRIORITY_HIGH, "4"),
    "P09-T02": ("P0009-T0002", "RED: Write failing tests first", "🔴", PRIORITY_HIGH, "8"),
    "P09-T03": ("P0009-T0003", "GREEN: Write code to pass tests", "🟢", PRIORITY_HIGH, "12"),
    "P09-T04": ("P0009-T0004", "REFACTOR: Improve code quality", "🔵", PRIORITY_MEDIUM, "8"),
    "P09-T05": ("P0009-T0005", "V-Model progression (TUT→FUT→SIT→UAT)", "📈", PRIORITY_HIGH, "6"),
    "P09-T06": ("P0009-T0006", "Verify >90% code coverage", "✅", PRIORITY_HIGH, "2"),

    # Phase 10 subtasks
    "P10-T01": ("P0010-T0001", "Create user training materials", "📚", PRIORITY_HIGH, "4"),
    "P10-T02": ("P0010-T0002", "Prepare demo video/walkthrough", "🎬", PRIORITY_MEDIUM, "4"),
    "P10-T03": ("P0010-T0003", "Set up feedback collection", "💬", PRIORITY_HIGH, "2"),
    "P10-T04": ("P0010-T0004", "Execute communication plan", "📢", PRIORITY_HIGH, "3"),
    "P10-T05": ("P0010-T0005", "Track adoption metrics", "📊", PRIORITY_HIGH, "3"),

    # Phase 11 subtasks
    "P11-T01": ("P0011-T0001", "Complete pre-deployment checklist", "📋", PRIORITY_HIGH, "2"),
    "P11-T02": ("P0011-T0002", "Run deployment automation", "⚙️", PRIORITY_HIGH, "4"),
    "P11-T03": ("P0011-T0003", "Execute health checks", "🏥", PRIORITY_HIGH, "2"),
    "P11-T04": ("P0011-T0004", "Verify monitoring and alerting", "📡", PRIORITY_HIGH, "3"),
    "P11-T05": ("P0011-T0005", "Run smoke tests in production", "🧪", PRIORITY_HIGH, "2"),
    "P11-T06": ("P0011-T0006", "Get UAT approval", "✔️", PRIORITY_HIGH, "3"),

    # Phase 12 subtasks
    "P12-T01": ("P0012-T0001", "Collect human feedback", "👤", PRIORITY_HIGH, "1"),
    "P12-T02": ("P0012-T0002", "Run agent SSC (Stop/Start/Continue)", "🤖", PRIORITY_HIGH, "2"),
    "P12-T03": ("P0012-T0003", "Update SE-Agent trajectory memory", "🧠", PRIORITY_HIGH, "1"),
    "P12-T04": ("P0012-T0004", "Add lessons to database (min 3)", "📚", PRIORITY_HIGH, "1"),
    "P12-T05": ("P0012-T0005", "Document proven patterns (min 4)", "📝", PRIORITY_HIGH, "1"),
    "P12-T06": ("P0012-T0006", "Assess organizational impact", "📊", PRIORITY_MEDIUM, "1"),
    "P12-T07": ("P0012-T0007", "Execute dissemination plan", "📣", PRIORITY_MEDIUM, "1"),
}

def generate_description(task_id: str, title: str) -> str:
    """Generate detailed description with AI agent instructions."""
    phase_num = task_id.split("-")[0]  # P0002
    phase_display = phase_num[-2:].lstrip("0") or "0"  # "2" from "P0002"

    return f"""# Task: {title}

## 🎯 OBJECTIVE
Execute this task following BACON-AI deterministic methodology as part of Phase {phase_display}.

## 🤖 AGENT SYSTEM PROMPT
```
You are a BACON-AI Task Execution Agent.
Task ID: {task_id}
Phase: {phase_num} (Phase {phase_display})

DETERMINISTIC EXECUTION SEQUENCE:
1. CHECK prerequisites - verify previous tasks completed
2. QUERY lessons learned for similar tasks
3. EXECUTE task steps in documented order
4. DOCUMENT all outputs with evidence
5. LOG lessons learned to bacon-memory
6. UPDATE task status to completed

CRITICAL RULES:
- Never skip steps or prerequisites
- Always check bacon-memory FIRST
- Document everything for future agents
- Use parallel agents where dependencies allow
```

## 🔧 REQUIRED MCP TOOLS
1. `mcp__mcp-bacon-memory__memory_query_proven_approaches` - Check existing solutions FIRST
2. `mcp__mcp-bacon-memory__memory_log_lesson_learned` - Log all findings
3. `WebSearch` - Research current best practices if needed
4. `mcp__ai-reasoning__*` - Deep analysis for complex decisions

## 📚 SKILLS TO REFERENCE
- `/lessons-learned` - Check organizational knowledge
- `/bacon-ai-deterministic-framework` - Follow phase methodology
- `/triz-innovation` - For contradiction resolution (Phase 3-4)

## 🔄 PARALLEL AGENT PROMPT
```
While executing primary task steps, spawn parallel agents to:
1. Pre-fetch documentation for next task
2. Prepare handoff summary for dependent tasks
3. Monitor for blocking issues
4. Update progress tracking in real-time
```

## 📝 LESSON LEARNED TEMPLATE
At task completion, execute:
```python
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="{task_id}: [TASK_SUMMARY]. Key insight: [KEY_INSIGHT]. Time taken: [DURATION]",
    severity="info",
    context="{task_id} {title}"
)
```

## ✅ SUCCESS CRITERIA
- [ ] Prerequisites verified complete
- [ ] Lessons learned queried BEFORE starting
- [ ] All task steps executed in order
- [ ] Outputs documented with evidence
- [ ] Lesson logged to bacon-memory
- [ ] Ready for dependent tasks
"""

def generate_checklist(task_id: str, title: str) -> List[Dict]:
    """Generate detailed checklist for task."""
    phase_num = task_id.split("-")[0]
    task_num = task_id.split("-")[1] if "-" in task_id else None

    # Base checklist items
    checklist = [
        {"text": "📥 INIT: Verify prerequisites complete", "checked": False},
        {"text": "🔍 Query bacon-memory for similar tasks/solutions", "checked": False},
        {"text": "📋 Review task requirements and constraints", "checked": False},
    ]

    # Add task-specific items based on title keywords
    if "Create" in title or "Draw" in title or "Write" in title:
        checklist.append({"text": "📝 Create initial draft/outline", "checked": False})
        checklist.append({"text": "📝 Complete full deliverable", "checked": False})
        checklist.append({"text": "🔍 Self-review for completeness", "checked": False})
    elif "Apply" in title or "Execute" in title or "Run" in title:
        checklist.append({"text": "⚙️ Prepare inputs and configuration", "checked": False})
        checklist.append({"text": "⚙️ Execute process/procedure", "checked": False})
        checklist.append({"text": "📊 Capture outputs and metrics", "checked": False})
    elif "Review" in title or "Verify" in title or "Check" in title:
        checklist.append({"text": "📋 Define review criteria", "checked": False})
        checklist.append({"text": "🔍 Execute review/verification steps", "checked": False})
        checklist.append({"text": "📝 Document findings and issues", "checked": False})
    elif "Identify" in title or "Collect" in title or "Gather" in title:
        checklist.append({"text": "📥 Collect from all sources", "checked": False})
        checklist.append({"text": "📊 Organize and categorize", "checked": False})
        checklist.append({"text": "🔍 Validate completeness", "checked": False})
    else:
        checklist.append({"text": f"📋 Execute step 1 of {title}", "checked": False})
        checklist.append({"text": f"📋 Execute step 2 of {title}", "checked": False})
        checklist.append({"text": f"📋 Execute step 3 of {title}", "checked": False})

    # Add standard completion items
    checklist.extend([
        {"text": "📝 Document all outputs with evidence", "checked": False},
        {"text": "📝 Prepare handoff notes for next task", "checked": False},
        {"text": "📝 Log lesson learned to bacon-memory", "checked": False},
        {"text": "✅ VERIFY: All success criteria met", "checked": False},
    ])

    return checklist


async def update_card(
    client: httpx.AsyncClient,
    card_id: str,
    new_title: str,
    icon: str,
    task_id: str,
    priority: str,
    hours: str,
    description: str,
    checklist: List[Dict]
) -> bool:
    """Update a card with all details."""

    # Get current card properties
    blocks_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks?type=card"
    response = await client.get(blocks_url, headers=get_headers())

    if response.status_code != 200:
        return False

    current_card = None
    for block in response.json():
        if block["id"] == card_id:
            current_card = block
            break

    if not current_card:
        return False

    # Update card properties
    current_props = current_card.get("fields", {}).get("properties", {})
    current_props[NUMBER_PROP_ID] = task_id
    current_props[PRIORITY_PROP_ID] = priority
    current_props[HOURS_PROP_ID] = hours

    patch_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks/{card_id}"
    patch_data = {
        "title": new_title,
        "updatedFields": {
            "icon": icon,
            "properties": current_props
        }
    }

    patch_response = await client.patch(patch_url, headers=get_headers(), json=patch_data)

    if patch_response.status_code != 200:
        print(f"  Failed to update card: {patch_response.status_code}")
        return False

    # Create content blocks
    await create_content_blocks(client, card_id, description, checklist)

    return True


async def create_content_blocks(
    client: httpx.AsyncClient,
    card_id: str,
    description: str,
    checklist: List[Dict]
) -> None:
    """Create content blocks for description and checklist."""

    blocks_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks"

    # Get existing content blocks for this card
    response = await client.get(blocks_url, headers=get_headers())

    if response.status_code == 200:
        # Delete existing text/checkbox blocks
        for block in response.json():
            if block.get("parentId") == card_id and block.get("type") in ["text", "checkbox"]:
                delete_url = f"{blocks_url}/{block['id']}"
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

    # Create checklist items
    for item in checklist:
        checkbox_block = {
            "type": "checkbox",
            "parentId": card_id,
            "boardId": BOARD_ID,
            "title": item["text"],
            "fields": {"value": item.get("checked", False)}
        }
        await client.post(blocks_url, headers=get_headers(), json=[checkbox_block])


async def main():
    print("=" * 70)
    print("BACON-AI Remaining Tasks Updater")
    print("Updating subtasks from P02-T01 format to P0002-T0001 format")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Get all cards
        url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks?type=card"
        response = await client.get(url, headers=get_headers())

        if response.status_code != 200:
            print(f"Failed to get cards: {response.status_code}")
            return

        cards = response.json()
        print(f"Found {len(cards)} total cards")

        # Build lookup by old prefix
        updated = 0
        not_found = 0

        for old_prefix, (new_task_id, title_suffix, icon, priority, hours) in TASK_MAPPING.items():
            # Find card with old prefix
            matching_card = None
            for card in cards:
                card_title = card.get("title", "")
                # Match "P02-T01 ──" at start of title
                if card_title.startswith(old_prefix + " "):
                    matching_card = card
                    break

            if matching_card:
                card_id = matching_card["id"]
                new_title = f"{new_task_id} ── {title_suffix}"
                description = generate_description(new_task_id, title_suffix)
                checklist = generate_checklist(new_task_id, title_suffix)

                success = await update_card(
                    client, card_id, new_title, icon,
                    new_task_id, priority, hours,
                    description, checklist
                )

                if success:
                    updated += 1
                    print(f"✅ {old_prefix} → {new_task_id}")
                else:
                    print(f"❌ Failed: {old_prefix}")
            else:
                not_found += 1
                print(f"⚠️  Not found: {old_prefix}")

        print()
        print("=" * 70)
        print(f"Complete: {updated} updated, {not_found} not found")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
