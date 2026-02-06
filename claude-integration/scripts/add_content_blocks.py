#!/usr/bin/env python3
"""
Add content blocks (descriptions and checklists) to all BACON-AI tasks.
"""

import asyncio
import httpx
import json
import uuid
from typing import Dict, List

# Configuration
FOCALBOARD_URL = "http://localhost:8000"
AUTH_TOKEN = "k77tg84g87pd6tjk7rdho1kqs9h"
BOARD_ID = "bd5mw98s3cjftjnef77q8c4oone"

def get_headers():
    return {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

def generate_description(task_id: str, title: str) -> str:
    """Generate detailed description with AI agent instructions."""
    phase_num = task_id.split("-")[0]
    phase_display = phase_num[-2:].lstrip("0") or "0"

    # Check if it's a phase header or subtask
    if "-T" in task_id:
        return f"""# Task: {title}

## OBJECTIVE
Execute this task following BACON-AI deterministic methodology as part of Phase {phase_display}.

## AGENT SYSTEM PROMPT
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

## REQUIRED MCP TOOLS
1. mcp__mcp-bacon-memory__memory_query_proven_approaches - Check existing solutions FIRST
2. mcp__mcp-bacon-memory__memory_log_lesson_learned - Log all findings
3. WebSearch - Research current best practices if needed

## SKILLS TO REFERENCE
- /lessons-learned - Check organizational knowledge
- /bacon-ai-deterministic-framework - Follow phase methodology

## LESSON LEARNED TEMPLATE
Execute at task completion:
mcp__mcp-bacon-memory__memory_log_lesson_learned(
    content="{task_id}: [TASK_SUMMARY]. Key insight: [KEY_INSIGHT]",
    severity="info",
    context="{task_id}"
)

## SUCCESS CRITERIA
- Prerequisites verified complete
- Lessons learned queried BEFORE starting
- All task steps executed in order
- Outputs documented with evidence
- Lesson logged to bacon-memory"""
    else:
        return f"""# {title}

## PURPOSE
Phase {phase_display} of the BACON-AI 12-Phase Framework.

## PHASE LEAD AGENT PROMPT
You are the BACON-AI Phase {phase_display} Lead.
Ensure all subtasks complete before phase transition.

## PHASE COMPLETION
- All subtasks must show COMPLETED status
- Lessons learned logged
- Ready for next phase

## SELF-LEARNING
mcp__mcp-bacon-memory__memory_store_proven_approach(
    content="{phase_num} completed: [SUMMARY]",
    tags=["phase-{phase_display}", "bacon-ai"],
    verification_count=1
)"""


def generate_checklist(task_id: str, title: str) -> List[str]:
    """Generate checklist items for task."""
    if "-T" in task_id:
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
        else:
            checklist.extend([
                f"Execute step 1 of {title}",
                f"Execute step 2 of {title}",
                f"Execute step 3 of {title}",
            ])

        checklist.extend([
            "Document all outputs with evidence",
            "Prepare handoff notes for next task",
            "Log lesson learned to bacon-memory",
            "VERIFY: All success criteria met",
        ])
        return checklist
    else:
        # Phase header checklist
        return [
            "GATE: Confirm previous phase complete",
            "Load previous phase outputs",
            "Execute all subtasks",
            "Log phase lessons to bacon-memory",
            "GATE: All subtasks complete before next phase",
        ]


async def main():
    print("=" * 70)
    print("BACON-AI Content Block Creator")
    print("Adding descriptions and checklists to all P0xxx tasks")
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

        # Create content blocks for each card
        created = 0
        for card in task_cards:
            card_id = card["id"]
            title_parts = card["title"].split(" ── ")
            task_id = title_parts[0]
            task_title = title_parts[1] if len(title_parts) > 1 else card["title"]

            # Check if card already has content blocks
            existing_content = [b for b in blocks if b.get("parentId") == card_id and b.get("type") in ["text", "checkbox"]]
            if existing_content:
                # Skip if already has content
                continue

            # Generate content
            description = generate_description(task_id, task_title)
            checklist_items = generate_checklist(task_id, task_title)

            # Create description text block
            desc_block_id = str(uuid.uuid4()).replace("-", "")[:24] + "aaa"
            desc_block = {
                "id": desc_block_id,
                "type": "text",
                "parentId": card_id,
                "boardId": BOARD_ID,
                "title": description,
                "fields": {},
                "schema": 1
            }

            # Create blocks list
            new_blocks = [desc_block]

            # Create checklist header
            checklist_header_id = str(uuid.uuid4()).replace("-", "")[:24] + "bbb"
            checklist_header = {
                "id": checklist_header_id,
                "type": "text",
                "parentId": card_id,
                "boardId": BOARD_ID,
                "title": "## Subtasks Checklist",
                "fields": {},
                "schema": 1
            }
            new_blocks.append(checklist_header)

            # Create checkbox blocks for each checklist item
            content_order = [desc_block_id, checklist_header_id]
            for item in checklist_items:
                checkbox_id = str(uuid.uuid4()).replace("-", "")[:24] + "ccc"
                checkbox_block = {
                    "id": checkbox_id,
                    "type": "checkbox",
                    "parentId": card_id,
                    "boardId": BOARD_ID,
                    "title": item,
                    "fields": {"value": False},
                    "schema": 1
                }
                new_blocks.append(checkbox_block)
                content_order.append(checkbox_id)

            # Post all blocks at once
            post_response = await client.post(blocks_url, headers=get_headers(), json=new_blocks)

            if post_response.status_code in [200, 201]:
                # Update card's contentOrder
                patch_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks/{card_id}"

                # Merge with existing contentOrder
                existing_order = card.get("fields", {}).get("contentOrder", [])
                new_order = existing_order + content_order

                patch_data = {
                    "updatedFields": {
                        "contentOrder": new_order
                    }
                }

                patch_response = await client.patch(patch_url, headers=get_headers(), json=patch_data)

                if patch_response.status_code == 200:
                    created += 1
                    print(f"✅ {task_id}: Added {len(checklist_items)} checklist items")
                else:
                    print(f"⚠️  {task_id}: Blocks created but contentOrder failed")
            else:
                print(f"❌ {task_id}: Failed to create blocks - {post_response.status_code}")
                if post_response.text:
                    print(f"   Error: {post_response.text[:200]}")

        print()
        print("=" * 70)
        print(f"Complete: {created} cards updated with content blocks")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
