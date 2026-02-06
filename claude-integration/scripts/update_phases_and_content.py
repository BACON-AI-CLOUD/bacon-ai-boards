#!/usr/bin/env python3
"""
Update BACON-AI tasks:
1. Rename phase headers from P0002 to P0002-0000 format
2. Add content blocks (descriptions and checklists) to all tasks
"""

import asyncio
import httpx
import time
import random
import string
from typing import Dict, List

# Configuration
FOCALBOARD_URL = "http://localhost:8000"
AUTH_TOKEN = "k77tg84g87pd6tjk7rdho1kqs9h"
BOARD_ID = "bd5mw98s3cjftjnef77q8c4oone"
NUMBER_PROP_ID = "a5p9bpedehti9yph1uuehqighue"

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

def generate_description(task_id: str, title: str) -> str:
    """Generate detailed description with AI agent instructions."""
    # Extract phase number from task_id
    if "-0000" in task_id:
        # Phase header
        phase_num = task_id.split("-")[0][-2:].lstrip("0") or "0"
        return f"""# {title}

## PURPOSE
Phase {phase_num} of the BACON-AI 12-Phase Framework.

## PHASE LEAD AGENT PROMPT
You are the BACON-AI Phase {phase_num} Lead.
Ensure all subtasks complete before phase transition.

## PHASE COMPLETION CRITERIA
- All subtasks must show COMPLETED status
- Lessons learned logged for phase
- Documentation updated
- Ready for next phase

## REQUIRED MCP TOOLS
1. mcp__mcp-bacon-memory__memory_query_proven_approaches
2. mcp__mcp-bacon-memory__memory_store_proven_approach
3. mcp__mcp-bacon-memory__memory_log_lesson_learned

## SELF-LEARNING CHECKPOINT
At phase completion:
mcp__mcp-bacon-memory__memory_store_proven_approach(
    content="{task_id} Phase {phase_num} completed: [SUMMARY]",
    tags=["phase-{phase_num}", "bacon-ai"],
    verification_count=1
)"""
    else:
        # Subtask
        phase_num = task_id.split("-")[0][-2:].lstrip("0") or "0"
        task_num = task_id.split("-")[1][-4:].lstrip("0") or "0"

        return f"""# Task: {title}

## OBJECTIVE
Execute this task following BACON-AI deterministic methodology as part of Phase {phase_num}.

## AGENT SYSTEM PROMPT
You are a BACON-AI Task Execution Agent.
Task ID: {task_id}
Phase: {phase_num}
Task: {task_num}

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

## REQUIRED MCP TOOLS
1. mcp__mcp-bacon-memory__memory_query_proven_approaches
2. mcp__mcp-bacon-memory__memory_log_lesson_learned
3. WebSearch (for current best practices if needed)
4. mcp__ai-reasoning__* (for complex decisions)

## SKILLS TO REFERENCE
- /lessons-learned - Check organizational knowledge
- /bacon-ai-deterministic-framework - Follow phase methodology
- /triz-innovation - For contradiction resolution

## PARALLEL AGENT PROMPT
While executing primary task steps, spawn parallel agents to:
1. Pre-fetch documentation for next task
2. Prepare handoff summary for dependent tasks
3. Monitor for blocking issues

## LESSON LEARNED TEMPLATE
At task completion:
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="{task_id}: [TASK_SUMMARY]. Insight: [KEY_INSIGHT]",
    severity="info",
    context="{task_id}"
)

## SUCCESS CRITERIA
- Prerequisites verified complete
- Lessons learned queried BEFORE starting
- All task steps executed in order
- Outputs documented with evidence
- Lesson logged to bacon-memory"""


def generate_checklist(task_id: str, title: str) -> List[str]:
    """Generate checklist items for task."""
    if "-0000" in task_id:
        # Phase header checklist
        phase_num = task_id.split("-")[0][-2:].lstrip("0") or "0"
        return [
            f"GATE: Confirm Phase {int(phase_num)-1} complete (if not Phase 0)",
            "Load previous phase outputs",
            "Brief phase team on objectives",
            "Execute all subtasks in dependency order",
            "Monitor for blockers and escalate",
            "Validate all subtask outputs",
            "Log phase lessons to bacon-memory",
            f"GATE: All subtasks complete before Phase {int(phase_num)+1}",
        ]
    else:
        # Subtask checklist
        checklist = [
            "INIT: Verify prerequisites complete",
            "Query bacon-memory for similar tasks/solutions",
            "Review task requirements and constraints",
        ]

        # Add task-specific items
        if "Create" in title or "Draw" in title or "Write" in title:
            checklist.extend([
                "Create initial draft/outline",
                "Complete full deliverable",
                "Self-review for completeness",
            ])
        elif "Apply" in title or "Execute" in title or "Run" in title:
            checklist.extend([
                "Prepare inputs and configuration",
                "Execute process/procedure",
                "Capture outputs and metrics",
            ])
        elif "Review" in title or "Verify" in title or "Check" in title:
            checklist.extend([
                "Define review criteria",
                "Execute review/verification steps",
                "Document findings and issues",
            ])
        elif "Collect" in title or "Gather" in title or "Identify" in title:
            checklist.extend([
                "Identify all sources",
                "Collect/gather data systematically",
                "Validate completeness",
            ])
        else:
            checklist.extend([
                f"Execute step 1: {title[:30]}...",
                f"Execute step 2: Validate results",
                f"Execute step 3: Document findings",
            ])

        checklist.extend([
            "Document all outputs with evidence",
            "Prepare handoff notes for next task",
            "Log lesson learned to bacon-memory",
            "VERIFY: All success criteria met",
        ])
        return checklist


async def main():
    print("=" * 70)
    print("BACON-AI Task Updater (Phase Headers + Content Blocks)")
    print("=" * 70)

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
        content_added = 0

        for card in task_cards:
            card_id = card["id"]
            old_title = card["title"]
            title_parts = old_title.split(" ── ")
            old_task_id = title_parts[0]
            task_name = title_parts[1] if len(title_parts) > 1 else ""

            # Determine new task ID
            if "-T" in old_task_id:
                # Already a subtask, keep format
                new_task_id = old_task_id
            elif old_task_id.startswith("P") and len(old_task_id) == 5:
                # Phase header like P0002, convert to P0002-0000
                new_task_id = f"{old_task_id}-0000"
            else:
                new_task_id = old_task_id

            # Build new title
            if task_name:
                new_title = f"{new_task_id} ── {task_name}"
            else:
                new_title = f"{new_task_id} ── {old_title}"

            # Check if update needed
            needs_title_update = new_title != old_title

            if needs_title_update:
                # Update card title and properties
                current_props = card.get("fields", {}).get("properties", {})
                current_props[NUMBER_PROP_ID] = new_task_id

                patch_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks/{card_id}"
                patch_data = {
                    "title": new_title,
                    "updatedFields": {
                        "properties": current_props
                    }
                }

                patch_response = await client.patch(patch_url, headers=get_headers(), json=patch_data)

                if patch_response.status_code == 200:
                    updated += 1
                    print(f"✅ Renamed: {old_task_id} → {new_task_id}")

            # Check if card already has content blocks
            existing_content = [b for b in blocks if b.get("parentId") == card_id and b.get("type") in ["text", "checkbox"]]
            if existing_content:
                continue

            # Generate and add content blocks
            task_title_for_content = task_name if task_name else old_title.replace(old_task_id, "").strip(" ──")
            description = generate_description(new_task_id, task_title_for_content)
            checklist_items = generate_checklist(new_task_id, task_title_for_content)

            now = int(time.time() * 1000)

            # Create blocks
            new_blocks = []
            content_order = []

            # Description text block
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

            # Checklist header
            header_id = generate_block_id()
            new_blocks.append({
                "id": header_id,
                "type": "text",
                "parentId": card_id,
                "boardId": BOARD_ID,
                "title": "## Subtasks Checklist",
                "fields": {},
                "schema": 1,
                "createAt": now,
                "updateAt": now,
            })
            content_order.append(header_id)

            # Checkbox items
            for item in checklist_items:
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

            # Post blocks
            post_response = await client.post(blocks_url, headers=get_headers(), json=new_blocks)

            if post_response.status_code in [200, 201]:
                # Update card's contentOrder
                existing_order = card.get("fields", {}).get("contentOrder", [])
                new_order = existing_order + content_order

                patch_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks/{card_id}"
                patch_data = {
                    "updatedFields": {
                        "contentOrder": new_order
                    }
                }

                await client.patch(patch_url, headers=get_headers(), json=patch_data)
                content_added += 1
                print(f"   + Added {len(checklist_items)} checklist items to {new_task_id}")
            else:
                print(f"   ❌ Failed to add content to {new_task_id}: {post_response.status_code}")
                if post_response.text:
                    print(f"      Error: {post_response.text[:100]}")

        print()
        print("=" * 70)
        print(f"Complete: {updated} renamed, {content_added} with content blocks")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
