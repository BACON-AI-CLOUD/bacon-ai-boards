#!/usr/bin/env python3
"""
Export Focalboard Board as BACON-AI Template

Exports a Focalboard board to the BACON-AI template JSON format for:
- Template instantiation for new projects
- Self-annealing feedback tracking
- Version control and distribution

Usage:
    python export_template.py <board_id> [output_path]

Environment:
    FOCALBOARD_URL: Base URL (default: http://localhost:8000)
    FOCALBOARD_TOKEN: Authentication token (required)
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

import httpx

# Configuration
FOCALBOARD_URL = os.getenv("FOCALBOARD_URL", "http://localhost:8000")
FOCALBOARD_TOKEN = os.getenv("FOCALBOARD_TOKEN", "")


def get_headers() -> Dict[str, str]:
    """Get required headers for Focalboard API."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {FOCALBOARD_TOKEN}"
    }


async def api_request(method: str, endpoint: str) -> Dict | List:
    """Make an authenticated request to Focalboard API v2."""
    url = f"{FOCALBOARD_URL}/api/v2{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, headers=get_headers())
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code >= 400:
            raise Exception(f"API error ({response.status_code}): {response.text[:200]}")

        return response.json() if response.text else {}


def extract_phase_from_title(title: str) -> Optional[int]:
    """Extract phase number from card title.

    Supports formats:
    - 'P0000-T0001' -> phase 0 (4-digit phase code)
    - 'P0001-0000' -> phase 1 (phase header)
    - 'P0012-T0003' -> phase 12
    """
    if not title or len(title) < 5:
        return None

    import re

    # Pattern 1: P00XX-T#### or P00XX-#### (4-digit phase, e.g., P0001, P0012)
    match = re.search(r'P00(\d{2})[-]', title)
    if match:
        return int(match.group(1))

    # Pattern 2: Legacy P####-T0X## format
    match = re.search(r'P\d{4}-T(\d{2})\d{2}', title)
    if match:
        return int(match.group(1))

    return None


def extract_task_id(title: str) -> Optional[str]:
    """Extract task ID from card title.

    Supports formats:
    - 'P0000-T0001' -> 'T0001'
    - 'P0001-0000' -> None (phase header, not a task)
    """
    import re
    match = re.search(r'T\d{4}', title)
    return match.group(0) if match else None


async def export_board_as_template(
    board_id: str,
    template_id: str = "bacon-ai-12-phase",
    template_name: str = "BACON-AI 12-Phase Framework",
    author: str = "Colin Bacon"
) -> Dict[str, Any]:
    """
    Export a Focalboard board as a BACON-AI template.

    Args:
        board_id: Focalboard board ID to export
        template_id: Template identifier (kebab-case)
        template_name: Human-readable template name
        author: Template author

    Returns:
        Template dictionary conforming to template-v1.schema.json
    """
    print(f"Fetching board {board_id}...")

    # Fetch board details
    board = await api_request("GET", f"/boards/{board_id}")

    # Fetch all cards
    cards = await api_request("GET", f"/boards/{board_id}/cards")
    print(f"Found {len(cards)} cards")

    # Fetch all blocks (for content blocks)
    blocks = await api_request("GET", f"/boards/{board_id}/blocks")
    print(f"Found {len(blocks)} blocks")

    # Build content blocks index by parent card
    content_blocks_by_card: Dict[str, List[Dict]] = {}
    for block in blocks:
        if block.get("type") in ["text", "checkbox", "divider", "image"]:
            parent_id = block.get("parentId")
            if parent_id:
                if parent_id not in content_blocks_by_card:
                    content_blocks_by_card[parent_id] = []
                content_blocks_by_card[parent_id].append(block)

    # Build property options lookup
    property_options: Dict[str, Dict[str, str]] = {}  # prop_id -> {option_id -> option_value}
    property_names: Dict[str, str] = {}  # prop_id -> prop_name

    for prop in board.get("cardProperties", []):
        prop_id = prop.get("id")
        property_names[prop_id] = prop.get("name", "")
        if prop.get("options"):
            property_options[prop_id] = {
                opt["id"]: opt["value"]
                for opt in prop.get("options", [])
            }

    # Group cards by phase
    phases_dict: Dict[int, List[Dict]] = {}
    unphased_cards: List[Dict] = []

    for card in cards:
        title = card.get("title", "")
        phase_num = extract_phase_from_title(title)

        if phase_num is not None:
            if phase_num not in phases_dict:
                phases_dict[phase_num] = []
            phases_dict[phase_num].append(card)
        else:
            unphased_cards.append(card)

    # Phase metadata from BACON-AI framework
    phase_metadata = {
        0: {"name": "Verification Protocol", "icon": "🔍", "leader": "Research Specialist"},
        1: {"name": "Empathetic Problem Definition", "icon": "💭", "leader": "Elisabeth + Maisie"},
        2: {"name": "Multi-Dimensional Data Gathering", "icon": "📊", "leader": "Research Specialist"},
        3: {"name": "Systematic Analysis & Insights", "icon": "🔬", "leader": "George (Systems Architect)"},
        4: {"name": "Creative Solution Generation", "icon": "💡", "leader": "Finn (Innovation Engineer)"},
        5: {"name": "Systematic Solution Evaluation", "icon": "⚖️", "leader": "Perspective Analyst"},
        6: {"name": "Consensus & Solution Selection", "icon": "🗳️", "leader": "Elisabeth (Orchestrator)"},
        7: {"name": "Design Excellence (WRICEF)", "icon": "📐", "leader": "Giuseppe (Documentation)"},
        8: {"name": "Implementation Planning", "icon": "📋", "leader": "Elisabeth + Lily"},
        9: {"name": "Build → Test (TDD)", "icon": "🔨", "leader": "Lily (Quality Assurance)"},
        10: {"name": "Go-Live Prep & Change Management", "icon": "🚀", "leader": "Elisabeth + Connor"},
        11: {"name": "Production Deployment", "icon": "🌐", "leader": "Connor (DevOps)"},
        12: {"name": "Reflection & Learning (SSC)", "icon": "📝", "leader": "SE-Agent Observer"},
    }

    # Build phases array
    phases = []
    for phase_num in sorted(phases_dict.keys()):
        phase_cards = phases_dict[phase_num]
        meta = phase_metadata.get(phase_num, {"name": f"Phase {phase_num}", "icon": "📋", "leader": "Unknown"})

        tasks = []
        for card in sorted(phase_cards, key=lambda c: c.get("title", "")):
            card_id = card.get("id")
            title = card.get("title", "")
            task_id = extract_task_id(title) or f"T{phase_num:02d}{len(tasks)+1:02d}"

            # Get card properties with resolved values
            card_props = card.get("properties", {})
            resolved_props = {}
            for prop_id, prop_val in card_props.items():
                prop_name = property_names.get(prop_id, prop_id)
                if prop_id in property_options:
                    resolved_props[prop_name] = property_options[prop_id].get(prop_val, prop_val)
                else:
                    resolved_props[prop_name] = prop_val

            # Get content blocks for this card
            card_content_blocks = content_blocks_by_card.get(card_id, [])

            # Extract checklist items (checkbox blocks)
            checklist = []
            content_blocks = []

            for block in sorted(card_content_blocks, key=lambda b: b.get("createAt", 0)):
                block_type = block.get("type")
                block_title = block.get("title", "")

                if block_type == "checkbox":
                    checked = block.get("fields", {}).get("value", False)
                    checklist.append({
                        "title": block_title,
                        "checked": checked
                    })
                elif block_type == "text":
                    content_blocks.append({
                        "type": "text",
                        "content": block_title
                    })
                elif block_type == "divider":
                    content_blocks.append({
                        "type": "divider"
                    })

            # Determine status
            status = resolved_props.get("Status", "not-started").lower().replace(" ", "-")
            if status not in ["not-started", "in-progress", "blocked", "completed"]:
                status = "not-started"

            task = {
                "id": task_id,
                "title": title,
                "icon": card.get("icon", "📋"),
                "status": status,
                "phase": f"phase-{phase_num}",
            }

            if checklist:
                task["checklist"] = checklist

            if content_blocks:
                task["content_blocks"] = content_blocks

            # Add agent instructions if present
            for block in content_blocks:
                if block.get("type") == "text" and "## Agent Instructions" in block.get("content", ""):
                    task["agent_instructions"] = block["content"]
                    break

            tasks.append(task)

        phase = {
            "number": phase_num,
            "name": meta["name"],
            "icon": meta["icon"],
            "leader": meta["leader"],
            "tasks": tasks
        }
        phases.append(phase)

    # Build card properties for template
    card_properties = []
    for prop in board.get("cardProperties", []):
        prop_def = {
            "id": prop.get("id"),
            "name": prop.get("name"),
            "type": prop.get("type", "text")
        }

        if prop.get("options"):
            prop_def["options"] = [
                {
                    "id": opt.get("id"),
                    "value": opt.get("value"),
                    "color": opt.get("color", "propColorDefault")
                }
                for opt in prop.get("options", [])
            ]

        card_properties.append(prop_def)

    # Build template
    template = {
        "$schema": "https://bacon-ai.io/schemas/template-v1.schema.json",
        "meta": {
            "id": template_id,
            "name": template_name,
            "version": "1.0.0",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "updated": datetime.now().strftime("%Y-%m-%d"),
            "author": author,
            "description": "Complete 12-phase methodology for AI-assisted collaborative development with self-annealing feedback loops.",
            "tags": ["framework", "bacon-ai", "12-phase", "comprehensive", "self-annealing"],
            "complexity": "high",
            "estimated_duration": "2-4 weeks"
        },
        "version_history": [
            {
                "version": "1.0.0",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "changes": f"Initial export from Focalboard board {board_id}"
            }
        ],
        "board": {
            "title": "${PROJECT_NAME} - BACON-AI 12-Phase Board",
            "icon": board.get("icon", "🥓"),
            "description": board.get("description", "BACON-AI 12-Phase Framework for collaborative AI development"),
            "type": board.get("type", "P"),
            "cardProperties": card_properties
        },
        "phases": phases,
        "feedback": {
            "pending_proposals": [],
            "approved_proposals": [],
            "rejected_proposals": []
        },
        "instances": {
            "active": [
                {
                    "board_id": board_id,
                    "project_name": "Original Template Source",
                    "created": datetime.now().isoformat(),
                    "template_version": "1.0.0",
                    "current_version": "1.0.0",
                    "upgrade_status": "current"
                }
            ],
            "archived": []
        }
    }

    # Add unphased cards as a special section if any exist
    if unphased_cards:
        unphased_tasks = []
        for card in unphased_cards:
            unphased_tasks.append({
                "id": extract_task_id(card.get("title", "")) or f"TXXXX",
                "title": card.get("title", ""),
                "icon": card.get("icon", "📋"),
                "status": "not-started"
            })

        template["unphased_cards"] = unphased_tasks

    return template


async def main():
    if len(sys.argv) < 2:
        print("Usage: python export_template.py <board_id> [output_path]")
        print("\nEnvironment variables:")
        print("  FOCALBOARD_URL: Base URL (default: http://localhost:8000)")
        print("  FOCALBOARD_TOKEN: Authentication token (required)")
        sys.exit(1)

    if not FOCALBOARD_TOKEN:
        print("Error: FOCALBOARD_TOKEN environment variable not set")
        sys.exit(1)

    board_id = sys.argv[1]

    # Default output path
    default_output = Path.home() / ".bacon-ai" / "templates" / "framework" / "bacon-ai-12-phase" / "template.json"
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else default_output

    print(f"Exporting board: {board_id}")
    print(f"Output path: {output_path}")
    print(f"Focalboard URL: {FOCALBOARD_URL}")
    print()

    try:
        template = await export_board_as_template(board_id)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write template
        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)

        print()
        print(f"Template exported successfully!")
        print(f"  Phases: {len(template['phases'])}")
        print(f"  Total tasks: {sum(len(p['tasks']) for p in template['phases'])}")
        print(f"  Output: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
