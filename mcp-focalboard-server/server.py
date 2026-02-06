#!/usr/bin/env python3
"""
MCP Server for Focalboard
=========================

A Model Context Protocol server for interacting with Focalboard project management.
Provides tools for managing boards, cards, content blocks, and tasks via the Focalboard REST API v2.

Configuration:
    Set environment variables:
    - FOCALBOARD_URL: Base URL (default: http://localhost:8000)
    - FOCALBOARD_TOKEN: Authentication token (required)

Usage:
    python server.py

Lessons Learned (from BACON-AI integration):
    1. CSRF Protection: Always include 'X-Requested-With: XMLHttpRequest' header
    2. Cards API vs Blocks API:
       - GET/POST /cards - Works for reading and creating cards
       - PATCH /cards/{id} - Does NOT persist properties reliably
       - PATCH /boards/{board_id}/blocks/{card_id} - CORRECT way to update card properties
    3. Content Blocks: Cards can have child blocks (text, checkbox, divider, image)
       - Must include createAt/updateAt timestamps
       - Must update card's contentOrder field for blocks to appear
    4. Date Properties: Use millisecond timestamps as strings
    5. Select Properties: Use option ID (not value) as property value
"""

import os
import sys
import json
import time
import random
import string
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pathlib import Path

import httpx
from pydantic import BaseModel, Field, ConfigDict, field_validator
from mcp.server.fastmcp import FastMCP

# Template directory configuration
TEMPLATE_BASE_DIR = Path.home() / ".bacon-ai" / "templates"

# ============================================================================
# Configuration
# ============================================================================

FOCALBOARD_URL = os.getenv("FOCALBOARD_URL", "http://localhost:8000")
FOCALBOARD_TOKEN = os.getenv("FOCALBOARD_TOKEN", "")
CHARACTER_LIMIT = 25000  # Maximum response size in characters
DEFAULT_LIMIT = 50  # Default pagination limit

# Initialize the MCP server
mcp = FastMCP("focalboard_mcp")


# ============================================================================
# Enums and Input Models
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class TeamInput(BaseModel):
    """Input for team-based operations."""
    model_config = ConfigDict(str_strip_whitespace=True)

    team_id: str = Field(
        default="0",
        description="Team ID. Use '0' for personal boards (default)."
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class BoardInput(BaseModel):
    """Input for board operations."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID (e.g., 'bd5mw98s3cjftjnef77q8c4oone')",
        min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class ListCardsInput(BaseModel):
    """Input for listing cards with pagination."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID",
        min_length=1
    )
    limit: int = Field(
        default=50,
        description="Maximum number of cards to return (1-200)",
        ge=1,
        le=200
    )
    offset: int = Field(
        default=0,
        description="Number of cards to skip for pagination",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class CardInput(BaseModel):
    """Input for single card operations."""
    model_config = ConfigDict(str_strip_whitespace=True)

    card_id: str = Field(
        ...,
        description="The card ID",
        min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class CardWithBoardInput(BaseModel):
    """Input for card operations that require board context."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID",
        min_length=1
    )
    card_id: str = Field(
        ...,
        description="The card ID",
        min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class CreateCardInput(BaseModel):
    """Input for creating a new card."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID where the card will be created",
        min_length=1
    )
    title: str = Field(
        ...,
        description="Card title (e.g., 'P0001-T0001 ── Create empathy map')",
        min_length=1,
        max_length=500
    )
    icon: str = Field(
        default="📋",
        description="Card icon (emoji), e.g., '🎯', '✅', '🔧'"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Card properties as {property_id: value}. Use focalboard_get_board to discover property IDs."
    )
    disable_notify: bool = Field(
        default=True,
        description="Disable notifications (recommended for bulk operations)"
    )


class UpdateCardPropertiesInput(BaseModel):
    """Input for updating card properties using the blocks API (recommended method)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID",
        min_length=1
    )
    card_id: str = Field(
        ...,
        description="The card ID to update",
        min_length=1
    )
    title: Optional[str] = Field(
        default=None,
        description="New card title (optional)"
    )
    icon: Optional[str] = Field(
        default=None,
        description="New card icon emoji (optional)"
    )
    properties: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Properties to update as {property_id: value}. For dates, use millisecond timestamp as string."
    )


class AddContentBlockInput(BaseModel):
    """Input for adding content blocks (text, checkbox, divider) to a card."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID",
        min_length=1
    )
    card_id: str = Field(
        ...,
        description="The card ID to add content to",
        min_length=1
    )
    block_type: str = Field(
        ...,
        description="Block type: 'text', 'checkbox', or 'divider'",
        pattern="^(text|checkbox|divider)$"
    )
    content: str = Field(
        default="",
        description="Block content (text content or checkbox label)"
    )
    checked: bool = Field(
        default=False,
        description="For checkbox blocks: whether it's checked (default False)"
    )


class BulkAddChecklistInput(BaseModel):
    """Input for adding multiple checklist items at once."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID",
        min_length=1
    )
    card_id: str = Field(
        ...,
        description="The card ID to add checklist to",
        min_length=1
    )
    items: List[str] = Field(
        ...,
        description="List of checklist item labels",
        min_length=1,
        max_length=50
    )
    header: Optional[str] = Field(
        default=None,
        description="Optional header text to add before checklist items"
    )


class DeleteCardInput(BaseModel):
    """Input for deleting a card."""
    model_config = ConfigDict(str_strip_whitespace=True)

    card_id: str = Field(
        ...,
        description="The card ID to delete",
        min_length=1
    )


class BulkCreateCardsInput(BaseModel):
    """Input for bulk card creation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID where cards will be created",
        min_length=1
    )
    cards: List[Dict[str, Any]] = Field(
        ...,
        description="Array of card objects with 'title', optional 'icon', and optional 'properties'",
        min_length=1,
        max_length=100
    )

    @field_validator('cards')
    @classmethod
    def validate_cards(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for i, card in enumerate(v):
            if 'title' not in card or not card['title']:
                raise ValueError(f"Card {i} missing required 'title' field")
        return v


class SearchCardsInput(BaseModel):
    """Input for searching cards."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID to search in",
        min_length=1
    )
    query: str = Field(
        ...,
        description="Search query (case-insensitive match on title)",
        min_length=1
    )
    limit: int = Field(
        default=50,
        description="Maximum results to return",
        ge=1,
        le=200
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class SetDueDateInput(BaseModel):
    """Input for setting a card's due date."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID",
        min_length=1
    )
    card_id: str = Field(
        ...,
        description="The card ID",
        min_length=1
    )
    due_date: str = Field(
        ...,
        description="Due date in YYYY-MM-DD format (e.g., '2026-02-15')"
    )
    due_date_property_id: str = Field(
        ...,
        description="The property ID for the due date field (get from focalboard_get_board)"
    )


class CreateBoardInput(BaseModel):
    """Input for creating a new board."""
    model_config = ConfigDict(str_strip_whitespace=True)

    team_id: str = Field(
        default="0",
        description="Team ID. Use '0' for personal boards."
    )
    title: str = Field(
        ...,
        description="Board title",
        min_length=1,
        max_length=200
    )
    description: str = Field(
        default="",
        description="Board description"
    )
    icon: str = Field(
        default="📋",
        description="Board icon emoji"
    )
    board_type: str = Field(
        default="P",
        description="Board type: 'P' for project board"
    )


class DuplicateBoardInput(BaseModel):
    """Input for duplicating a board."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID to duplicate",
        min_length=1
    )


class BoardMemberInput(BaseModel):
    """Input for board member operations."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID",
        min_length=1
    )
    user_id: str = Field(
        ...,
        description="The user ID to add/update/remove",
        min_length=1
    )
    role: str = Field(
        default="editor",
        description="Role: 'admin', 'editor', 'commenter', or 'viewer'"
    )


class ExportBoardInput(BaseModel):
    """Input for exporting a board archive."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID to export",
        min_length=1
    )


class UpdateCheckboxInput(BaseModel):
    """Input for updating a checkbox block's checked state."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID",
        min_length=1
    )
    block_id: str = Field(
        ...,
        description="The checkbox block ID",
        min_length=1
    )
    checked: bool = Field(
        ...,
        description="New checked state (True or False)"
    )


class HealthCheckInput(BaseModel):
    """Input for health check (no parameters required)."""
    model_config = ConfigDict(str_strip_whitespace=True)


class ListTemplatesInput(BaseModel):
    """Input for listing available templates."""
    model_config = ConfigDict(str_strip_whitespace=True)

    category: Optional[str] = Field(
        default=None,
        description="Filter by category (e.g., 'framework', 'sprint', 'project')"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class GetTemplateInput(BaseModel):
    """Input for getting template details."""
    model_config = ConfigDict(str_strip_whitespace=True)

    template_id: str = Field(
        ...,
        description="Template ID (e.g., 'bacon-ai-12-phase')",
        min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class InstantiateTemplateInput(BaseModel):
    """Input for creating a new board from a template."""
    model_config = ConfigDict(str_strip_whitespace=True)

    template_id: str = Field(
        ...,
        description="Template ID to instantiate",
        min_length=1
    )
    project_name: str = Field(
        ...,
        description="Project name for the new board",
        min_length=1,
        max_length=200
    )
    team_id: str = Field(
        default="0",
        description="Team ID. Use '0' for personal boards."
    )
    variables: Optional[Dict[str, str]] = Field(
        default=None,
        description="Variables to substitute in template (e.g., {'PROJECT_NAME': 'My Project'})"
    )


class SyncTemplateInput(BaseModel):
    """Input for syncing a board with its template."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID to sync",
        min_length=1
    )
    template_id: str = Field(
        ...,
        description="The template ID to sync with",
        min_length=1
    )
    direction: str = Field(
        default="template_to_board",
        description="Sync direction: 'template_to_board' or 'board_to_template'"
    )
    dry_run: bool = Field(
        default=True,
        description="If True, only show what would change without applying"
    )


class GetBoardTrackingInput(BaseModel):
    """Input for getting board template tracking info."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID to get tracking info for",
        min_length=1
    )


class SetBoardTrackingInput(BaseModel):
    """Input for setting board template tracking properties."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID to update",
        min_length=1
    )
    template_id: str = Field(
        ...,
        description="Template ID this board was created from",
        min_length=1
    )
    template_version: str = Field(
        ...,
        description="Template version (e.g., '1.0.0')",
        pattern=r"^\d+\.\d+\.\d+$"
    )
    upgrade_status: str = Field(
        default="current",
        description="Upgrade status: 'current', 'available', or 'skipped'"
    )


class GetPhaseTasksInput(BaseModel):
    """Input for getting tasks for a specific phase."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID",
        min_length=1
    )
    phase_number: int = Field(
        ...,
        description="Phase number (0-12)",
        ge=0,
        le=12
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class GetPhaseAgentContextInput(BaseModel):
    """Input for getting agent context for a phase."""
    model_config = ConfigDict(str_strip_whitespace=True)

    board_id: str = Field(
        ...,
        description="The board ID",
        min_length=1
    )
    phase_number: int = Field(
        ...,
        description="Phase number (0-12)",
        ge=0,
        le=12
    )


# ============================================================================
# Shared Utilities
# ============================================================================

def _get_headers() -> Dict[str, str]:
    """Get required headers for Focalboard API."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",  # CRITICAL: Required for CSRF protection
        "Authorization": f"Bearer {FOCALBOARD_TOKEN}"
    }


def _generate_block_id() -> str:
    """Generate a valid Focalboard block ID (27 alphanumeric characters)."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(27))


async def _api_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None
) -> Dict | List | str:
    """Make an authenticated request to Focalboard API v2."""
    url = f"{FOCALBOARD_URL}/api/v2{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=_get_headers(), params=params)
            elif method == "POST":
                response = await client.post(url, headers=_get_headers(), json=data, params=params)
            elif method == "PATCH":
                response = await client.patch(url, headers=_get_headers(), json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=_get_headers())
            else:
                return {"error": f"Unsupported HTTP method: {method}"}

            if response.status_code >= 400:
                return _handle_http_error(response)

            if response.text:
                return response.json()
            return {"success": True}

        except httpx.TimeoutException:
            return {"error": "Request timed out. The Focalboard server may be slow or unavailable. Try again."}
        except httpx.ConnectError:
            return {"error": f"Could not connect to Focalboard at {FOCALBOARD_URL}. Ensure the server is running."}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}


def _handle_http_error(response: httpx.Response) -> Dict[str, str]:
    """Convert HTTP errors to actionable error messages."""
    status = response.status_code

    if status == 401:
        return {"error": "Authentication failed. Check that FOCALBOARD_TOKEN is valid and not expired."}
    elif status == 403:
        return {"error": "Permission denied. The token may not have access to this resource."}
    elif status == 404:
        return {"error": "Resource not found. Verify the board_id or card_id is correct."}
    elif status == 429:
        return {"error": "Rate limit exceeded. Wait a moment before making more requests."}
    else:
        return {"error": f"API error (HTTP {status}): {response.text[:200]}"}


def _truncate_response(result: str, item_count: int) -> str:
    """Truncate response if it exceeds CHARACTER_LIMIT."""
    if len(result) <= CHARACTER_LIMIT:
        return result

    truncated = result[:CHARACTER_LIMIT - 200]
    truncated += f"\n\n---\n**Response truncated** from {len(result)} to {CHARACTER_LIMIT} characters.\n"
    truncated += f"Use 'offset' parameter or 'query' filter to see more.\n"
    return truncated


def _format_timestamp(ts: Optional[int]) -> str:
    """Format millisecond timestamp to human-readable date."""
    if not ts:
        return "Not set"
    try:
        dt = datetime.fromtimestamp(ts / 1000)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return str(ts)


def _format_board_markdown(board: Dict) -> str:
    """Format board details as markdown."""
    lines = [
        f"# {board.get('title', 'Untitled Board')}",
        "",
        f"**ID**: `{board.get('id', 'N/A')}`",
        f"**Type**: {board.get('type', 'N/A')}",
        f"**Created**: {_format_timestamp(board.get('createAt'))}",
        f"**Updated**: {_format_timestamp(board.get('updateAt'))}",
        ""
    ]

    card_props = board.get("cardProperties", [])
    if card_props:
        lines.append("## Card Properties")
        lines.append("")
        for prop in card_props:
            prop_name = prop.get("name", "Unknown")
            prop_id = prop.get("id", "")
            prop_type = prop.get("type", "text")
            lines.append(f"### {prop_name}")
            lines.append(f"- **ID**: `{prop_id}`")
            lines.append(f"- **Type**: {prop_type}")

            options = prop.get("options", [])
            if options:
                lines.append("- **Options**:")
                for opt in options[:10]:
                    lines.append(f"  - `{opt.get('id')}` = {opt.get('value')}")
                if len(options) > 10:
                    lines.append(f"  - ... and {len(options) - 10} more")
            lines.append("")

    return "\n".join(lines)


def _format_card_markdown(card: Dict, brief: bool = False) -> str:
    """Format card details as markdown."""
    title = card.get("title", "Untitled")
    icon = card.get("icon", "📋")
    card_id = card.get("id", "N/A")

    if brief:
        return f"- {icon} **{title}** (`{card_id}`)"

    lines = [
        f"## {icon} {title}",
        f"**ID**: `{card_id}`",
        f"**Created**: {_format_timestamp(card.get('createAt'))}",
        f"**Updated**: {_format_timestamp(card.get('updateAt'))}",
    ]

    props = card.get("properties", {})
    if props:
        lines.append("")
        lines.append("**Properties**:")
        for k, v in list(props.items())[:10]:
            lines.append(f"- `{k}`: {v}")

    return "\n".join(lines)


# ============================================================================
# Template Utilities
# ============================================================================

def _discover_templates(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Discover available templates from the template directory."""
    templates = []

    if not TEMPLATE_BASE_DIR.exists():
        return templates

    # Scan all subdirectories for template.json files
    for category_dir in TEMPLATE_BASE_DIR.iterdir():
        if not category_dir.is_dir():
            continue

        if category and category_dir.name != category:
            continue

        for template_dir in category_dir.iterdir():
            if not template_dir.is_dir():
                continue

            template_file = template_dir / "template.json"
            if template_file.exists():
                try:
                    with open(template_file, 'r') as f:
                        template = json.load(f)

                    meta = template.get("meta", {})
                    templates.append({
                        "id": meta.get("id", template_dir.name),
                        "name": meta.get("name", template_dir.name),
                        "version": meta.get("version", "0.0.0"),
                        "category": category_dir.name,
                        "description": meta.get("description", ""),
                        "author": meta.get("author", "Unknown"),
                        "complexity": meta.get("complexity", "medium"),
                        "tags": meta.get("tags", []),
                        "path": str(template_file),
                        "phases_count": len(template.get("phases", [])),
                        "tasks_count": sum(len(p.get("tasks", [])) for p in template.get("phases", []))
                    })
                except (json.JSONDecodeError, IOError) as e:
                    # Skip invalid templates
                    continue

    return templates


def _load_template(template_id: str) -> Optional[Dict[str, Any]]:
    """Load a template by ID."""
    templates = _discover_templates()

    for t in templates:
        if t["id"] == template_id:
            try:
                with open(t["path"], 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None

    return None


def _save_template(template: Dict[str, Any], template_id: str, category: str = "framework") -> bool:
    """Save a template to disk."""
    template_dir = TEMPLATE_BASE_DIR / category / template_id
    template_dir.mkdir(parents=True, exist_ok=True)

    template_file = template_dir / "template.json"
    try:
        with open(template_file, 'w') as f:
            json.dump(template, f, indent=2)
        return True
    except IOError:
        return False


def _substitute_variables(text: str, variables: Dict[str, str]) -> str:
    """Substitute variables like ${PROJECT_NAME} in text."""
    if not variables:
        return text

    result = text
    for key, value in variables.items():
        result = result.replace(f"${{{key}}}", value)

    return result


def _format_template_markdown(template: Dict[str, Any], brief: bool = False) -> str:
    """Format template details as markdown."""
    meta = template.get("meta", {})
    phases = template.get("phases", [])

    if brief:
        return f"- **{meta.get('name', 'Unknown')}** (v{meta.get('version', '0.0.0')}) - {meta.get('description', '')[:50]}..."

    lines = [
        f"# {meta.get('name', 'Unknown Template')}",
        "",
        f"**ID**: `{meta.get('id', 'unknown')}`",
        f"**Version**: {meta.get('version', '0.0.0')}",
        f"**Author**: {meta.get('author', 'Unknown')}",
        f"**Complexity**: {meta.get('complexity', 'medium')}",
        f"**Created**: {meta.get('created', 'N/A')}",
        f"**Updated**: {meta.get('updated', 'N/A')}",
        "",
        f"**Description**: {meta.get('description', 'No description')}",
        "",
        f"**Tags**: {', '.join(meta.get('tags', []))}",
        "",
        "## Phases",
        ""
    ]

    for phase in phases:
        phase_num = phase.get("number", 0)
        phase_name = phase.get("name", "Unknown")
        phase_icon = phase.get("icon", "📋")
        tasks = phase.get("tasks", [])
        lines.append(f"### {phase_icon} Phase {phase_num}: {phase_name}")
        lines.append(f"- **Tasks**: {len(tasks)}")
        lines.append(f"- **Leader**: {phase.get('leader', 'N/A')}")
        lines.append("")

    total_tasks = sum(len(p.get("tasks", [])) for p in phases)
    lines.append("---")
    lines.append(f"**Total**: {len(phases)} phases, {total_tasks} tasks")

    return "\n".join(lines)


# ============================================================================
# Tool Implementations
# ============================================================================

@mcp.tool(
    name="focalboard_list_boards",
    annotations={
        "title": "List Focalboard Boards",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_list_boards(params: TeamInput) -> str:
    """
    List all boards for a team in Focalboard.

    This tool retrieves all boards accessible to the authenticated user
    within the specified team. Use team_id='0' for personal boards.

    Args:
        params: TeamInput containing:
            - team_id (str): Team ID, default '0' for personal boards
            - response_format: 'markdown' or 'json'

    Returns:
        str: List of boards with their IDs, titles, and types.

    Examples:
        - List personal boards: team_id="0"
        - List team boards: team_id="your-team-id"

    Next Steps:
        - Use focalboard_get_board with a board_id to see card properties
        - Use focalboard_list_cards to see cards on a board
    """
    result = await _api_request("GET", f"/teams/{params.team_id}/boards")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    if not isinstance(result, list):
        return "Error: Unexpected response format from API"

    boards = result

    if params.response_format == ResponseFormat.JSON:
        return json.dumps({"count": len(boards), "boards": boards}, indent=2)

    if not boards:
        return "No boards found for this team. Create a board in Focalboard first."

    lines = [
        "# Focalboard Boards",
        "",
        f"Found **{len(boards)}** boards:",
        ""
    ]

    for board in boards:
        title = board.get("title", "Untitled")
        board_id = board.get("id", "N/A")
        board_type = board.get("type", "board")
        lines.append(f"- **{title}** (`{board_id}`) - {board_type}")

    lines.append("")
    lines.append("---")
    lines.append("Use `focalboard_get_board` with a board_id to see card properties.")

    return "\n".join(lines)


@mcp.tool(
    name="focalboard_get_board",
    annotations={
        "title": "Get Board Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_get_board(params: BoardInput) -> str:
    """
    Get detailed information about a Focalboard board including property definitions.

    This tool retrieves board details including card property definitions,
    which are essential for creating cards with the correct property IDs.

    IMPORTANT: Use this tool FIRST to discover property IDs before creating/updating cards.

    Args:
        params: BoardInput containing:
            - board_id (str): The board ID to retrieve
            - response_format: 'markdown' or 'json'

    Returns:
        str: Board details including:
            - Title and metadata
            - Card property definitions with IDs and option values

    Property Types:
        - select: Use option ID as value (not the display text)
        - date: Use millisecond timestamp as string
        - number: Use string representation of number
        - text: Use plain string

    Next Steps:
        - Use the property IDs shown to create cards with focalboard_create_card
        - Use option IDs for select/multiSelect property values
    """
    result = await _api_request("GET", f"/boards/{params.board_id}")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(result, indent=2)

    return _format_board_markdown(result)


@mcp.tool(
    name="focalboard_list_cards",
    annotations={
        "title": "List Cards on Board",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_list_cards(params: ListCardsInput) -> str:
    """
    List cards on a Focalboard board with pagination.

    Args:
        params: ListCardsInput containing:
            - board_id (str): The board ID
            - limit (int): Max cards to return (1-200, default 50)
            - offset (int): Cards to skip for pagination
            - response_format: 'markdown' or 'json'

    Returns:
        str: List of cards with pagination info.

    Examples:
        - First 50 cards: board_id="...", limit=50
        - Next page: board_id="...", limit=50, offset=50
    """
    result = await _api_request("GET", f"/boards/{params.board_id}/cards")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    if not isinstance(result, list):
        return "Error: Unexpected response format from API"

    all_cards = result
    total = len(all_cards)

    cards = all_cards[params.offset:params.offset + params.limit]
    has_more = total > params.offset + len(cards)

    if params.response_format == ResponseFormat.JSON:
        response = {
            "total": total,
            "count": len(cards),
            "offset": params.offset,
            "has_more": has_more,
            "next_offset": params.offset + len(cards) if has_more else None,
            "cards": cards
        }
        result_str = json.dumps(response, indent=2)
        return _truncate_response(result_str, len(cards))

    if not cards:
        if params.offset > 0:
            return f"No more cards after offset {params.offset}. Total cards: {total}"
        return "No cards found on this board."

    lines = [
        "# Cards",
        "",
        f"Showing **{len(cards)}** of **{total}** cards (offset: {params.offset})",
        ""
    ]

    for card in cards:
        lines.append(_format_card_markdown(card, brief=True))

    if has_more:
        lines.append("")
        lines.append(f"---")
        lines.append(f"More cards available. Use offset={params.offset + len(cards)} to see next page.")

    result_str = "\n".join(lines)
    return _truncate_response(result_str, len(cards))


@mcp.tool(
    name="focalboard_get_card",
    annotations={
        "title": "Get Card Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_get_card(params: CardInput) -> str:
    """
    Get detailed information about a specific card.

    Args:
        params: CardInput containing:
            - card_id (str): The card ID to retrieve
            - response_format: 'markdown' or 'json'

    Returns:
        str: Card details including title, icon, properties, and timestamps.
    """
    result = await _api_request("GET", f"/cards/{params.card_id}")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(result, indent=2)

    return _format_card_markdown(result)


@mcp.tool(
    name="focalboard_get_card_content",
    annotations={
        "title": "Get Card Content Blocks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_get_card_content(params: CardWithBoardInput) -> str:
    """
    Get content blocks (text, checkboxes, dividers) for a specific card.

    Content blocks are child elements of a card that provide:
    - Text blocks: Descriptions, instructions, notes
    - Checkbox blocks: Checklists, subtasks
    - Divider blocks: Visual separators

    Args:
        params: CardWithBoardInput containing:
            - board_id (str): The board ID
            - card_id (str): The card ID
            - response_format: 'markdown' or 'json'

    Returns:
        str: List of content blocks with their types and content.
    """
    result = await _api_request("GET", f"/boards/{params.board_id}/blocks")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    if not isinstance(result, list):
        return "Error: Unexpected response format from API"

    # Filter to content blocks for this card
    content_blocks = [
        b for b in result
        if b.get("parentId") == params.card_id and b.get("type") in ["text", "checkbox", "divider", "image"]
    ]

    if params.response_format == ResponseFormat.JSON:
        return json.dumps({"count": len(content_blocks), "blocks": content_blocks}, indent=2)

    if not content_blocks:
        return f"No content blocks found for card `{params.card_id}`."

    lines = [
        "# Card Content Blocks",
        "",
        f"Found **{len(content_blocks)}** blocks:",
        ""
    ]

    for block in content_blocks:
        block_type = block.get("type", "unknown")
        title = block.get("title", "")
        block_id = block.get("id", "")

        if block_type == "checkbox":
            checked = block.get("fields", {}).get("value", False)
            checkbox = "[x]" if checked else "[ ]"
            lines.append(f"- {checkbox} {title} (`{block_id}`)")
        elif block_type == "divider":
            lines.append(f"- --- (divider) (`{block_id}`)")
        elif block_type == "text":
            preview = title[:80] + "..." if len(title) > 80 else title
            lines.append(f"- **Text**: {preview} (`{block_id}`)")
        else:
            lines.append(f"- **{block_type}**: {title[:50]} (`{block_id}`)")

    return "\n".join(lines)


@mcp.tool(
    name="focalboard_create_card",
    annotations={
        "title": "Create Card",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def focalboard_create_card(params: CreateCardInput) -> str:
    """
    Create a new card on a Focalboard board.

    Before creating cards, use focalboard_get_board to discover
    available property IDs and option values.

    Args:
        params: CreateCardInput containing:
            - board_id (str): Board where the card will be created
            - title (str): Card title
            - icon (str): Emoji icon (default '📋')
            - properties (dict): Property values as {property_id: value}
            - disable_notify (bool): Skip notifications (default True)

    Returns:
        str: Created card details including the new card ID.

    Property Value Formats:
        - Select: Use the option ID string (e.g., "ayz81h9f3dwp...")
        - MultiSelect: Use array of option IDs
        - Text: Use string value
        - Number: Use string value (e.g., "8")
        - Date: Use millisecond timestamp as string

    Examples:
        Create a task:
        - title: "P0001-T0001 ── Create empathy map"
        - icon: "💭"
        - properties: {"status-prop-id": "not-started-option-id"}
    """
    query_params = {"disable_notify": "true"} if params.disable_notify else None

    data = {
        "title": params.title,
        "icon": params.icon,
        "properties": params.properties
    }

    result = await _api_request(
        "POST",
        f"/boards/{params.board_id}/cards",
        data=data,
        params=query_params
    )

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    card_id = result.get("id", "unknown")
    return f"Card created successfully!\n\n**Title**: {params.title}\n**ID**: `{card_id}`"


@mcp.tool(
    name="focalboard_update_card_properties",
    annotations={
        "title": "Update Card Properties (Recommended)",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_update_card_properties(params: UpdateCardPropertiesInput) -> str:
    """
    Update a card's title, icon, and/or properties using the blocks API.

    IMPORTANT: This is the RECOMMENDED method for updating card properties.
    The /cards/{id} PATCH endpoint does NOT reliably persist properties.
    This tool uses /boards/{board_id}/blocks/{card_id} which works correctly.

    Args:
        params: UpdateCardPropertiesInput containing:
            - board_id (str): The board ID
            - card_id (str): Card to update
            - title (str, optional): New title
            - icon (str, optional): New icon emoji
            - properties (dict, optional): Properties to update

    Returns:
        str: Confirmation of update.

    Property Value Formats:
        - Select: Use the option ID string
        - Date: Use millisecond timestamp as string (e.g., "1738368000000")
        - Number: Use string value (e.g., "8")

    Examples:
        - Update status: properties={"status-id": "completed-option-id"}
        - Set due date: properties={"due-date-id": "1738368000000"}
    """
    # First get current card to preserve existing properties
    get_url = f"/boards/{params.board_id}/blocks?type=card"
    cards_result = await _api_request("GET", get_url)

    if isinstance(cards_result, dict) and "error" in cards_result:
        return f"Error getting card: {cards_result['error']}"

    current_card = None
    for card in cards_result:
        if card.get("id") == params.card_id:
            current_card = card
            break

    if not current_card:
        return f"Error: Card `{params.card_id}` not found on board `{params.board_id}`"

    # Build update data
    update_data = {"updatedFields": {}}

    if params.properties is not None:
        # Merge with existing properties
        current_props = current_card.get("fields", {}).get("properties", {})
        current_props.update(params.properties)
        update_data["updatedFields"]["properties"] = current_props

    if params.icon is not None:
        update_data["updatedFields"]["icon"] = params.icon

    if params.title is not None:
        update_data["title"] = params.title

    if not update_data.get("updatedFields") and not update_data.get("title"):
        return "Error: No updates provided. Specify title, icon, or properties to update."

    # Update using blocks API
    result = await _api_request(
        "PATCH",
        f"/boards/{params.board_id}/blocks/{params.card_id}",
        data=update_data
    )

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    return f"Card `{params.card_id}` updated successfully!"


@mcp.tool(
    name="focalboard_add_content_block",
    annotations={
        "title": "Add Content Block to Card",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def focalboard_add_content_block(params: AddContentBlockInput) -> str:
    """
    Add a content block (text, checkbox, or divider) to a card.

    Content blocks appear in the card's detail view and are useful for:
    - Text: Descriptions, instructions, documentation
    - Checkbox: Checklists, subtasks, verification steps
    - Divider: Visual separation between sections

    Args:
        params: AddContentBlockInput containing:
            - board_id (str): The board ID
            - card_id (str): The card ID to add content to
            - block_type (str): 'text', 'checkbox', or 'divider'
            - content (str): Block content (text or checkbox label)
            - checked (bool): For checkboxes, whether checked (default False)

    Returns:
        str: Confirmation with new block ID.

    Examples:
        - Add description: block_type="text", content="## Description\\n..."
        - Add task: block_type="checkbox", content="Verify prerequisites"
        - Add separator: block_type="divider"
    """
    now = int(time.time() * 1000)
    block_id = _generate_block_id()

    block_data = {
        "id": block_id,
        "type": params.block_type,
        "parentId": params.card_id,
        "boardId": params.board_id,
        "title": params.content,
        "fields": {"value": params.checked} if params.block_type == "checkbox" else {},
        "schema": 1,
        "createAt": now,
        "updateAt": now,
    }

    # Create the block
    result = await _api_request(
        "POST",
        f"/boards/{params.board_id}/blocks",
        data=[block_data]
    )

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    # Update card's contentOrder
    cards_result = await _api_request("GET", f"/boards/{params.board_id}/blocks?type=card")
    if isinstance(cards_result, list):
        for card in cards_result:
            if card.get("id") == params.card_id:
                current_order = card.get("fields", {}).get("contentOrder", [])
                current_order.append(block_id)
                await _api_request(
                    "PATCH",
                    f"/boards/{params.board_id}/blocks/{params.card_id}",
                    data={"updatedFields": {"contentOrder": current_order}}
                )
                break

    return f"Content block added!\n\n**Type**: {params.block_type}\n**ID**: `{block_id}`"


@mcp.tool(
    name="focalboard_add_checklist",
    annotations={
        "title": "Add Checklist to Card",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def focalboard_add_checklist(params: BulkAddChecklistInput) -> str:
    """
    Add multiple checklist items to a card at once.

    This is more efficient than adding items one by one. Optionally
    includes a header text block before the checklist items.

    Args:
        params: BulkAddChecklistInput containing:
            - board_id (str): The board ID
            - card_id (str): The card ID
            - items (list[str]): List of checklist item labels
            - header (str, optional): Header text to add before items

    Returns:
        str: Summary of items added.

    Examples:
        Add subtasks with header:
        - header: "## Subtasks Checklist"
        - items: ["Verify prerequisites", "Execute task", "Document results"]
    """
    now = int(time.time() * 1000)
    new_blocks = []
    content_order = []

    # Add header if provided
    if params.header:
        header_id = _generate_block_id()
        new_blocks.append({
            "id": header_id,
            "type": "text",
            "parentId": params.card_id,
            "boardId": params.board_id,
            "title": params.header,
            "fields": {},
            "schema": 1,
            "createAt": now,
            "updateAt": now,
        })
        content_order.append(header_id)

    # Add checkbox items
    for item in params.items:
        checkbox_id = _generate_block_id()
        new_blocks.append({
            "id": checkbox_id,
            "type": "checkbox",
            "parentId": params.card_id,
            "boardId": params.board_id,
            "title": item,
            "fields": {"value": False},
            "schema": 1,
            "createAt": now,
            "updateAt": now,
        })
        content_order.append(checkbox_id)

    # Create all blocks
    result = await _api_request(
        "POST",
        f"/boards/{params.board_id}/blocks",
        data=new_blocks
    )

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    # Update card's contentOrder
    cards_result = await _api_request("GET", f"/boards/{params.board_id}/blocks?type=card")
    if isinstance(cards_result, list):
        for card in cards_result:
            if card.get("id") == params.card_id:
                current_order = card.get("fields", {}).get("contentOrder", [])
                current_order.extend(content_order)
                await _api_request(
                    "PATCH",
                    f"/boards/{params.board_id}/blocks/{params.card_id}",
                    data={"updatedFields": {"contentOrder": current_order}}
                )
                break

    return f"Checklist added!\n\n**Items**: {len(params.items)}\n**Header**: {'Yes' if params.header else 'No'}"


@mcp.tool(
    name="focalboard_set_due_date",
    annotations={
        "title": "Set Card Due Date",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_set_due_date(params: SetDueDateInput) -> str:
    """
    Set or update a card's due date.

    Converts a human-readable date (YYYY-MM-DD) to the millisecond timestamp
    format required by Focalboard.

    Args:
        params: SetDueDateInput containing:
            - board_id (str): The board ID
            - card_id (str): The card ID
            - due_date (str): Due date in YYYY-MM-DD format
            - due_date_property_id (str): The property ID for due date

    Returns:
        str: Confirmation of date set.

    How to find due_date_property_id:
        1. Use focalboard_get_board to list properties
        2. Find the property with type="date" named "Due Date"
        3. Use that property's ID

    Examples:
        - due_date: "2026-02-15"
        - due_date_property_id: "a3zsw7xs8sxy7atj8b6totp3mby"
    """
    try:
        dt = datetime.strptime(params.due_date, "%Y-%m-%d")
        timestamp_ms = str(int(dt.timestamp() * 1000))
    except ValueError:
        return f"Error: Invalid date format '{params.due_date}'. Use YYYY-MM-DD format."

    # Update using the properties update tool
    update_params = UpdateCardPropertiesInput(
        board_id=params.board_id,
        card_id=params.card_id,
        properties={params.due_date_property_id: timestamp_ms}
    )

    return await focalboard_update_card_properties(update_params)


@mcp.tool(
    name="focalboard_delete_card",
    annotations={
        "title": "Delete Card",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_delete_card(params: DeleteCardInput) -> str:
    """
    Delete a card from Focalboard.

    WARNING: This action is destructive and cannot be undone.

    Args:
        params: DeleteCardInput containing:
            - card_id (str): Card to delete

    Returns:
        str: Confirmation or error message.
    """
    result = await _api_request("DELETE", f"/blocks/{params.card_id}")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    return f"Card `{params.card_id}` deleted successfully."


@mcp.tool(
    name="focalboard_bulk_create_cards",
    annotations={
        "title": "Bulk Create Cards",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def focalboard_bulk_create_cards(params: BulkCreateCardsInput) -> str:
    """
    Create multiple cards efficiently in a single operation.

    More efficient than calling focalboard_create_card multiple times.
    Notifications are disabled automatically.

    Args:
        params: BulkCreateCardsInput containing:
            - board_id (str): Target board
            - cards (list): Array of card objects with:
                - title (str, required): Card title
                - icon (str, optional): Emoji icon
                - properties (dict, optional): Card properties

    Returns:
        str: Summary of created cards and any errors.

    Examples:
        cards: [
            {"title": "Task 1", "icon": "✅"},
            {"title": "Task 2", "icon": "🔧", "properties": {...}}
        ]
    """
    results = {"created": 0, "failed": 0, "errors": [], "ids": []}

    for i, card in enumerate(params.cards):
        data = {
            "title": card["title"],
            "icon": card.get("icon", "📋"),
            "properties": card.get("properties", {})
        }

        result = await _api_request(
            "POST",
            f"/boards/{params.board_id}/cards",
            data=data,
            params={"disable_notify": "true"}
        )

        if isinstance(result, dict) and "error" in result:
            results["failed"] += 1
            results["errors"].append(f"Card {i+1} ('{card['title']}'): {result['error']}")
        else:
            results["created"] += 1
            results["ids"].append(result.get("id", "unknown"))

    lines = [
        "# Bulk Create Results",
        "",
        f"**Created**: {results['created']} cards",
        f"**Failed**: {results['failed']} cards"
    ]

    if results["errors"]:
        lines.append("")
        lines.append("## Errors:")
        for err in results["errors"][:10]:
            lines.append(f"- {err}")
        if len(results["errors"]) > 10:
            lines.append(f"- ... and {len(results['errors']) - 10} more errors")

    return "\n".join(lines)


@mcp.tool(
    name="focalboard_search_cards",
    annotations={
        "title": "Search Cards",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_search_cards(params: SearchCardsInput) -> str:
    """
    Search for cards by title on a board.

    Performs case-insensitive substring matching on card titles.

    Args:
        params: SearchCardsInput containing:
            - board_id (str): Board to search
            - query (str): Search text (matches anywhere in title)
            - limit (int): Max results (default 50)
            - response_format: 'markdown' or 'json'

    Returns:
        str: Matching cards or message if none found.

    Examples:
        - Find phase 1 tasks: query="P0001"
        - Find verification tasks: query="Verify"
    """
    result = await _api_request("GET", f"/boards/{params.board_id}/cards")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    if not isinstance(result, list):
        return "Error: Unexpected response format from API"

    query_lower = params.query.lower()
    matching = [
        card for card in result
        if query_lower in card.get("title", "").lower()
    ][:params.limit]

    if params.response_format == ResponseFormat.JSON:
        return json.dumps({
            "query": params.query,
            "count": len(matching),
            "cards": matching
        }, indent=2)

    if not matching:
        return f"No cards found matching '{params.query}' on this board."

    lines = [
        f"# Search Results: '{params.query}'",
        "",
        f"Found **{len(matching)}** matching cards:",
        ""
    ]

    for card in matching:
        lines.append(_format_card_markdown(card, brief=True))

    return "\n".join(lines)


@mcp.tool(
    name="focalboard_get_board_statistics",
    annotations={
        "title": "Get Board Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_get_board_statistics(params: BoardInput) -> str:
    """
    Get statistics about cards on a board.

    Provides counts grouped by select properties like status and priority.
    Useful for project overview and progress tracking.

    Args:
        params: BoardInput containing:
            - board_id (str): The board to analyze
            - response_format: 'markdown' or 'json'

    Returns:
        str: Statistics including total cards and counts by property values.

    Examples:
        - Track project progress by status
        - See distribution of priority levels
    """
    board = await _api_request("GET", f"/boards/{params.board_id}")
    if isinstance(board, dict) and "error" in board:
        return f"Error: {board['error']}"

    cards = await _api_request("GET", f"/boards/{params.board_id}/cards")
    if isinstance(cards, dict) and "error" in cards:
        return f"Error: {cards['error']}"

    if not isinstance(cards, list):
        return "Error: Unexpected response format"

    stats = {
        "total_cards": len(cards),
        "by_property": {}
    }

    card_properties = board.get("cardProperties", [])
    for prop in card_properties:
        if prop.get("type") == "select":
            prop_id = prop["id"]
            prop_name = prop["name"]
            options = {opt["id"]: opt["value"] for opt in prop.get("options", [])}

            counts = {}
            for card in cards:
                val = card.get("properties", {}).get(prop_id, "")
                val_name = options.get(val, "Unset")
                counts[val_name] = counts.get(val_name, 0) + 1

            stats["by_property"][prop_name] = counts

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(stats, indent=2)

    lines = [
        "# Board Statistics",
        "",
        f"**Total Cards**: {stats['total_cards']}",
        ""
    ]

    for prop_name, counts in stats["by_property"].items():
        lines.append(f"## {prop_name}")
        for val, count in sorted(counts.items(), key=lambda x: -x[1]):
            pct = (count / stats["total_cards"] * 100) if stats["total_cards"] > 0 else 0
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            lines.append(f"- **{val}**: {count} ({pct:.0f}%) {bar}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool(
    name="focalboard_create_board",
    annotations={
        "title": "Create Board",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def focalboard_create_board(params: CreateBoardInput) -> str:
    """
    Create a new Focalboard board.

    Args:
        params: CreateBoardInput containing:
            - team_id (str): Team ID, '0' for personal boards
            - title (str): Board title
            - description (str): Board description
            - icon (str): Board icon emoji
            - board_type (str): 'P' for project board

    Returns:
        str: Created board details including ID.
    """
    data = {
        "teamId": params.team_id,
        "type": params.board_type,
        "title": params.title,
        "description": params.description,
        "icon": params.icon,
        "showDescription": bool(params.description),
        "cardProperties": []
    }

    result = await _api_request("POST", "/boards", data=data)

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    board_id = result.get("id", "unknown")
    return f"Board created successfully!\n\n**Title**: {params.title}\n**ID**: `{board_id}`\n**Icon**: {params.icon}"


@mcp.tool(
    name="focalboard_duplicate_board",
    annotations={
        "title": "Duplicate Board",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def focalboard_duplicate_board(params: DuplicateBoardInput) -> str:
    """
    Duplicate an existing board with all its cards and content.

    Args:
        params: DuplicateBoardInput containing:
            - board_id (str): The board ID to duplicate

    Returns:
        str: New board details.
    """
    result = await _api_request("POST", f"/boards/{params.board_id}/duplicate")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    boards = result.get("boards", [])
    if boards:
        new_board = boards[0]
        return f"Board duplicated!\n\n**New Board ID**: `{new_board.get('id')}`\n**Title**: {new_board.get('title')}"

    return "Board duplicated successfully!"


@mcp.tool(
    name="focalboard_list_board_members",
    annotations={
        "title": "List Board Members",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_list_board_members(params: BoardInput) -> str:
    """
    List all members of a board.

    Args:
        params: BoardInput containing:
            - board_id (str): The board ID
            - response_format: 'markdown' or 'json'

    Returns:
        str: List of board members with their roles.
    """
    result = await _api_request("GET", f"/boards/{params.board_id}/members")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    if params.response_format == ResponseFormat.JSON:
        return json.dumps({"count": len(result), "members": result}, indent=2)

    if not result:
        return "No members found for this board."

    lines = [
        "# Board Members",
        "",
        f"Found **{len(result)}** members:",
        ""
    ]

    for member in result:
        user_id = member.get("userId", "N/A")
        roles = member.get("roles", "")
        is_admin = member.get("schemeAdmin", False)
        lines.append(f"- **{user_id}** - {roles} {'(Admin)' if is_admin else ''}")

    return "\n".join(lines)


@mcp.tool(
    name="focalboard_add_board_member",
    annotations={
        "title": "Add Board Member",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_add_board_member(params: BoardMemberInput) -> str:
    """
    Add a user as a member of a board.

    Args:
        params: BoardMemberInput containing:
            - board_id (str): The board ID
            - user_id (str): The user ID to add
            - role (str): 'admin', 'editor', 'commenter', or 'viewer'

    Returns:
        str: Confirmation message.
    """
    data = {
        "boardId": params.board_id,
        "userId": params.user_id,
        "roles": params.role,
        "schemeAdmin": params.role == "admin",
        "schemeEditor": params.role in ["admin", "editor"],
        "schemeCommenter": params.role in ["admin", "editor", "commenter"],
        "schemeViewer": True
    }

    result = await _api_request("POST", f"/boards/{params.board_id}/members", data=data)

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    return f"User `{params.user_id}` added to board as **{params.role}**."


@mcp.tool(
    name="focalboard_remove_board_member",
    annotations={
        "title": "Remove Board Member",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_remove_board_member(params: BoardMemberInput) -> str:
    """
    Remove a user from a board.

    Args:
        params: BoardMemberInput containing:
            - board_id (str): The board ID
            - user_id (str): The user ID to remove

    Returns:
        str: Confirmation message.
    """
    result = await _api_request("DELETE", f"/boards/{params.board_id}/members/{params.user_id}")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    return f"User `{params.user_id}` removed from board."


@mcp.tool(
    name="focalboard_update_checkbox",
    annotations={
        "title": "Update Checkbox State",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_update_checkbox(params: UpdateCheckboxInput) -> str:
    """
    Update the checked state of a checkbox block.

    Useful for marking checklist items as complete or incomplete.

    Args:
        params: UpdateCheckboxInput containing:
            - board_id (str): The board ID
            - block_id (str): The checkbox block ID
            - checked (bool): New checked state

    Returns:
        str: Confirmation message.

    Examples:
        - Mark complete: checked=True
        - Mark incomplete: checked=False
    """
    data = {
        "updatedFields": {
            "value": params.checked
        }
    }

    result = await _api_request(
        "PATCH",
        f"/boards/{params.board_id}/blocks/{params.block_id}",
        data=data
    )

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    status = "checked ✓" if params.checked else "unchecked"
    return f"Checkbox `{params.block_id}` marked as **{status}**."


@mcp.tool(
    name="focalboard_health_check",
    annotations={
        "title": "Server Health Check",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_health_check(params: HealthCheckInput) -> str:
    """
    Check if the Focalboard server is healthy and responding.

    Returns server status and basic information.

    Args:
        params: HealthCheckInput (no parameters required)

    Returns:
        str: Server health status.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Check /hello endpoint (no auth required)
            hello_response = await client.get(f"{FOCALBOARD_URL}/api/v2/hello")

            # Check /ping endpoint
            ping_response = await client.get(f"{FOCALBOARD_URL}/api/v2/ping")
            ping_data = ping_response.json() if ping_response.status_code == 200 else {}

            # Check authenticated access
            auth_response = await client.get(
                f"{FOCALBOARD_URL}/api/v2/users/me",
                headers=_get_headers()
            )
            auth_ok = auth_response.status_code == 200

            lines = [
                "# Focalboard Health Check",
                "",
                f"**Server URL**: {FOCALBOARD_URL}",
                f"**Hello Endpoint**: {'✅ OK' if hello_response.status_code == 200 else '❌ Failed'}",
                f"**Ping Endpoint**: {'✅ OK' if ping_response.status_code == 200 else '❌ Failed'}",
                f"**Authentication**: {'✅ Valid' if auth_ok else '❌ Invalid or expired'}",
            ]

            if ping_data:
                lines.append("")
                lines.append("**Server Info**:")
                for key, value in list(ping_data.items())[:10]:
                    lines.append(f"- {key}: {value}")

            return "\n".join(lines)

        except httpx.ConnectError:
            return f"❌ **Connection Failed**\n\nCould not connect to Focalboard at {FOCALBOARD_URL}.\nEnsure the server is running."
        except Exception as e:
            return f"❌ **Health Check Error**\n\n{str(e)}"


@mcp.tool(
    name="focalboard_get_server_statistics",
    annotations={
        "title": "Get Server Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_get_server_statistics(params: HealthCheckInput) -> str:
    """
    Get server-wide statistics from Focalboard.

    Returns overall usage statistics including board and card counts.

    Args:
        params: HealthCheckInput (no parameters required)

    Returns:
        str: Server statistics.
    """
    result = await _api_request("GET", "/statistics")

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    lines = [
        "# Focalboard Server Statistics",
        ""
    ]

    for key, value in result.items():
        lines.append(f"- **{key}**: {value}")

    return "\n".join(lines)


# ============================================================================
# Template Tools
# ============================================================================

@mcp.tool(
    name="focalboard_list_templates",
    annotations={
        "title": "List Available Templates",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def focalboard_list_templates(params: ListTemplatesInput) -> str:
    """
    List available BACON-AI templates that can be instantiated.

    Templates are stored in ~/.bacon-ai/templates/ and include:
    - Framework templates (e.g., BACON-AI 12-phase methodology)
    - Sprint templates
    - Project templates

    Args:
        params: ListTemplatesInput containing:
            - category (str, optional): Filter by category
            - response_format: 'markdown' or 'json'

    Returns:
        str: List of templates with metadata.

    Next Steps:
        - Use focalboard_get_template to see template details
        - Use focalboard_instantiate_template to create a board from template
    """
    templates = _discover_templates(params.category)

    if params.response_format == ResponseFormat.JSON:
        return json.dumps({
            "count": len(templates),
            "templates": templates,
            "template_dir": str(TEMPLATE_BASE_DIR)
        }, indent=2)

    if not templates:
        return f"No templates found in `{TEMPLATE_BASE_DIR}`.\n\nRun the export script to create templates from existing boards."

    lines = [
        "# Available Templates",
        "",
        f"Found **{len(templates)}** templates in `{TEMPLATE_BASE_DIR}`:",
        ""
    ]

    # Group by category
    by_category: Dict[str, List[Dict]] = {}
    for t in templates:
        cat = t.get("category", "other")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(t)

    for cat, cat_templates in sorted(by_category.items()):
        lines.append(f"## {cat.title()}")
        lines.append("")
        for t in cat_templates:
            lines.append(f"- **{t['name']}** (`{t['id']}`) v{t['version']}")
            lines.append(f"  - {t['description'][:60]}..." if len(t.get('description', '')) > 60 else f"  - {t.get('description', 'No description')}")
            lines.append(f"  - {t['phases_count']} phases, {t['tasks_count']} tasks")
            lines.append("")

    lines.append("---")
    lines.append("Use `focalboard_get_template` with a template_id to see details.")

    return "\n".join(lines)


@mcp.tool(
    name="focalboard_get_template",
    annotations={
        "title": "Get Template Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def focalboard_get_template(params: GetTemplateInput) -> str:
    """
    Get detailed information about a specific template.

    Shows all phases, tasks, checklist items, and configuration details.
    Use this to understand what will be created when instantiating a template.

    Args:
        params: GetTemplateInput containing:
            - template_id (str): The template ID
            - response_format: 'markdown' or 'json'

    Returns:
        str: Complete template details including:
            - Metadata (name, version, author, tags)
            - All phases with tasks
            - Card property definitions
            - Instance tracking info

    Next Steps:
        - Use focalboard_instantiate_template to create a board from this template
    """
    template = _load_template(params.template_id)

    if not template:
        return f"Error: Template `{params.template_id}` not found.\n\nUse `focalboard_list_templates` to see available templates."

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(template, indent=2)

    return _format_template_markdown(template)


@mcp.tool(
    name="focalboard_instantiate_template",
    annotations={
        "title": "Create Board from Template",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def focalboard_instantiate_template(params: InstantiateTemplateInput) -> str:
    """
    Create a new Focalboard board from a template.

    This creates a complete board with:
    - All card properties defined in the template
    - All cards (tasks) organized by phase
    - All checklists and content blocks
    - Template tracking metadata

    Args:
        params: InstantiateTemplateInput containing:
            - template_id (str): Template to instantiate
            - project_name (str): Name for the new project
            - team_id (str): Team ID, '0' for personal boards
            - variables (dict, optional): Variables like {'PROJECT_NAME': 'My Project'}

    Returns:
        str: Details of created board including board ID.

    Variables:
        - ${PROJECT_NAME}: Replaced with project_name
        - ${CURRENT_DATE}: Replaced with current date
        - Custom variables can be passed in the variables parameter

    Examples:
        - Create a new BACON-AI project board:
          template_id="bacon-ai-12-phase", project_name="My AI Project"
    """
    template = _load_template(params.template_id)

    if not template:
        return f"Error: Template `{params.template_id}` not found."

    # Build variables for substitution
    variables = params.variables or {}
    variables.setdefault("PROJECT_NAME", params.project_name)
    variables.setdefault("CURRENT_DATE", datetime.now().strftime("%Y-%m-%d"))

    meta = template.get("meta", {})
    board_config = template.get("board", {})
    phases = template.get("phases", [])

    # Step 1: Create the board
    board_title = _substitute_variables(board_config.get("title", "${PROJECT_NAME} Board"), variables)

    board_data = {
        "teamId": params.team_id,
        "type": board_config.get("type", "P"),
        "title": board_title,
        "description": _substitute_variables(board_config.get("description", ""), variables),
        "icon": board_config.get("icon", "🥓"),
        "showDescription": True,
        "cardProperties": board_config.get("cardProperties", [])
    }

    board_result = await _api_request("POST", "/boards", data=board_data)

    if isinstance(board_result, dict) and "error" in board_result:
        return f"Error creating board: {board_result['error']}"

    board_id = board_result.get("id", "unknown")

    # Build property ID mapping for status, phase, etc.
    property_map: Dict[str, str] = {}
    option_map: Dict[str, Dict[str, str]] = {}  # prop_name -> {option_value -> option_id}

    for prop in board_config.get("cardProperties", []):
        prop_name = prop.get("name", "")
        prop_id = prop.get("id", "")
        property_map[prop_name] = prop_id

        if prop.get("options"):
            option_map[prop_name] = {
                opt.get("value", ""): opt.get("id", "")
                for opt in prop.get("options", [])
            }

    # Step 2: Create cards for each phase
    cards_created = 0
    errors = []

    for phase in phases:
        phase_num = phase.get("number", 0)
        tasks = phase.get("tasks", [])

        for task in tasks:
            task_title = _substitute_variables(task.get("title", "Untitled Task"), variables)

            # Build properties
            card_properties = {}

            # Set status property if available
            status = task.get("status", "not-started")
            if "Status" in property_map and "Status" in option_map:
                status_option_id = option_map["Status"].get(status.replace("-", " ").title(), "")
                if status_option_id:
                    card_properties[property_map["Status"]] = status_option_id

            # Set phase property if available
            if "Phase" in property_map and "Phase" in option_map:
                phase_name = f"Phase {phase_num}"
                phase_option_id = option_map["Phase"].get(phase_name, "")
                if phase_option_id:
                    card_properties[property_map["Phase"]] = phase_option_id

            card_data = {
                "title": task_title,
                "icon": task.get("icon", "📋"),
                "properties": card_properties
            }

            card_result = await _api_request(
                "POST",
                f"/boards/{board_id}/cards",
                data=card_data,
                params={"disable_notify": "true"}
            )

            if isinstance(card_result, dict) and "error" in card_result:
                errors.append(f"Task '{task_title}': {card_result['error']}")
                continue

            card_id = card_result.get("id", "")
            cards_created += 1

            # Add checklists if defined
            checklist = task.get("checklist", [])
            if checklist and card_id:
                now = int(time.time() * 1000)
                new_blocks = []
                content_order = []

                for item in checklist:
                    checkbox_id = _generate_block_id()
                    item_title = item if isinstance(item, str) else item.get("title", "")
                    item_checked = False if isinstance(item, str) else item.get("checked", False)

                    new_blocks.append({
                        "id": checkbox_id,
                        "type": "checkbox",
                        "parentId": card_id,
                        "boardId": board_id,
                        "title": _substitute_variables(item_title, variables),
                        "fields": {"value": item_checked},
                        "schema": 1,
                        "createAt": now,
                        "updateAt": now,
                    })
                    content_order.append(checkbox_id)

                # Create blocks
                if new_blocks:
                    await _api_request("POST", f"/boards/{board_id}/blocks", data=new_blocks)

                    # Update content order
                    await _api_request(
                        "PATCH",
                        f"/boards/{board_id}/blocks/{card_id}",
                        data={"updatedFields": {"contentOrder": content_order}}
                    )

            # Add content blocks if defined
            content_blocks = task.get("content_blocks", [])
            if content_blocks and card_id:
                now = int(time.time() * 1000)
                new_blocks = []
                content_order_additions = []

                for block in content_blocks:
                    block_id = _generate_block_id()
                    block_type = block.get("type", "text")

                    if block_type == "divider":
                        new_blocks.append({
                            "id": block_id,
                            "type": "divider",
                            "parentId": card_id,
                            "boardId": board_id,
                            "title": "",
                            "fields": {},
                            "schema": 1,
                            "createAt": now,
                            "updateAt": now,
                        })
                    else:
                        new_blocks.append({
                            "id": block_id,
                            "type": "text",
                            "parentId": card_id,
                            "boardId": board_id,
                            "title": _substitute_variables(block.get("content", ""), variables),
                            "fields": {},
                            "schema": 1,
                            "createAt": now,
                            "updateAt": now,
                        })

                    content_order_additions.append(block_id)

                if new_blocks:
                    await _api_request("POST", f"/boards/{board_id}/blocks", data=new_blocks)

                    # Get current content order and append
                    cards_result = await _api_request("GET", f"/boards/{board_id}/blocks?type=card")
                    if isinstance(cards_result, list):
                        for card in cards_result:
                            if card.get("id") == card_id:
                                current_order = card.get("fields", {}).get("contentOrder", [])
                                current_order.extend(content_order_additions)
                                await _api_request(
                                    "PATCH",
                                    f"/boards/{board_id}/blocks/{card_id}",
                                    data={"updatedFields": {"contentOrder": current_order}}
                                )
                                break

    # Step 3: Create a default table view for the board
    now = int(time.time() * 1000)
    view_id = _generate_block_id()

    # Get the Status property ID for visible columns
    status_prop_id = property_map.get("Status", "")

    view_data = [{
        "id": view_id,
        "parentId": board_id,
        "boardId": board_id,
        "schema": 1,
        "type": "view",
        "title": "Task Overview",
        "fields": {
            "viewType": "table",
            "cardOrder": [],
            "collapsedOptionIds": [],
            "columnCalculations": {},
            "columnWidths": {},
            "defaultTemplateId": "",
            "filter": {"filters": [], "operation": "and"},
            "groupById": "",
            "hiddenOptionIds": [],
            "kanbanCalculations": {},
            "sortOptions": [],
            "visibleOptionIds": [],
            "visiblePropertyIds": [status_prop_id] if status_prop_id else []
        },
        "createAt": now,
        "updateAt": now,
    }]

    view_result = await _api_request("POST", f"/boards/{board_id}/blocks", data=view_data)
    view_created = not (isinstance(view_result, dict) and "error" in view_result)

    # Step 4: Update template instance tracking
    template_instances = template.get("instances", {"active": [], "archived": []})
    template_instances["active"].append({
        "board_id": board_id,
        "project_name": params.project_name,
        "created": datetime.now().isoformat(),
        "template_version": meta.get("version", "1.0.0"),
        "current_version": meta.get("version", "1.0.0"),
        "upgrade_status": "current"
    })
    template["instances"] = template_instances

    # Find the category and save
    templates = _discover_templates()
    template_info = next((t for t in templates if t["id"] == params.template_id), None)
    if template_info:
        _save_template(template, params.template_id, template_info.get("category", "framework"))

    # Build result
    lines = [
        "# Board Created from Template",
        "",
        f"**Template**: {meta.get('name', 'Unknown')} v{meta.get('version', '0.0.0')}",
        f"**Project**: {params.project_name}",
        "",
        "## Board Details",
        f"- **Board ID**: `{board_id}`",
        f"- **Title**: {board_title}",
        f"- **Cards Created**: {cards_created}",
        f"- **Default View**: {'✅ Created' if view_created else '❌ Failed'}",
    ]

    if errors:
        lines.append("")
        lines.append(f"## Errors ({len(errors)})")
        for err in errors[:5]:
            lines.append(f"- {err}")
        if len(errors) > 5:
            lines.append(f"- ... and {len(errors) - 5} more errors")

    lines.append("")
    lines.append("---")
    lines.append(f"View in Focalboard: {FOCALBOARD_URL}/board/{board_id}")

    return "\n".join(lines)


@mcp.tool(
    name="focalboard_sync_template",
    annotations={
        "title": "Sync Board with Template",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_sync_template(params: SyncTemplateInput) -> str:
    """
    Compare and optionally sync changes between a board and its template.

    This tool supports the self-annealing feedback loop by:
    - Detecting differences between board and template
    - Proposing changes for template updates (board_to_template)
    - Applying template updates to boards (template_to_board)

    Args:
        params: SyncTemplateInput containing:
            - board_id (str): The board ID to sync
            - template_id (str): The template ID to sync with
            - direction (str): 'template_to_board' or 'board_to_template'
            - dry_run (bool): If True, only show changes without applying

    Returns:
        str: Sync report showing detected differences and actions taken.

    Directions:
        - template_to_board: Apply template changes to board (update board)
        - board_to_template: Propose board changes as template feedback

    Examples:
        - Check for template updates: dry_run=True, direction="template_to_board"
        - Propose board changes: direction="board_to_template"
    """
    template = _load_template(params.template_id)

    if not template:
        return f"Error: Template `{params.template_id}` not found."

    # Get board and cards
    board = await _api_request("GET", f"/boards/{params.board_id}")
    if isinstance(board, dict) and "error" in board:
        return f"Error: {board['error']}"

    cards = await _api_request("GET", f"/boards/{params.board_id}/cards")
    if isinstance(cards, dict) and "error" in cards:
        return f"Error: {cards['error']}"

    if not isinstance(cards, list):
        cards = []

    # Build comparison
    template_tasks = []
    for phase in template.get("phases", []):
        for task in phase.get("tasks", []):
            template_tasks.append({
                "id": task.get("id"),
                "title": task.get("title"),
                "phase": phase.get("number"),
                "icon": task.get("icon"),
                "checklist_count": len(task.get("checklist", []))
            })

    board_cards = [
        {
            "id": c.get("id"),
            "title": c.get("title"),
            "icon": c.get("icon")
        }
        for c in cards
    ]

    # Find differences
    template_titles = {t["title"] for t in template_tasks}
    board_titles = {c["title"] for c in board_cards}

    missing_from_board = template_titles - board_titles
    extra_in_board = board_titles - template_titles

    lines = [
        "# Template Sync Report",
        "",
        f"**Template**: {template.get('meta', {}).get('name', 'Unknown')} v{template.get('meta', {}).get('version', '0.0.0')}",
        f"**Board**: `{params.board_id}`",
        f"**Direction**: {params.direction}",
        f"**Dry Run**: {'Yes' if params.dry_run else 'No'}",
        "",
        "## Differences Detected",
        ""
    ]

    if not missing_from_board and not extra_in_board:
        lines.append("✅ **No differences found!** Board is in sync with template.")
    else:
        if missing_from_board:
            lines.append(f"### Missing from Board ({len(missing_from_board)} tasks)")
            for title in sorted(missing_from_board)[:10]:
                lines.append(f"- ❌ {title}")
            if len(missing_from_board) > 10:
                lines.append(f"- ... and {len(missing_from_board) - 10} more")
            lines.append("")

        if extra_in_board:
            lines.append(f"### Extra in Board ({len(extra_in_board)} cards)")
            for title in sorted(extra_in_board)[:10]:
                lines.append(f"- ➕ {title}")
            if len(extra_in_board) > 10:
                lines.append(f"- ... and {len(extra_in_board) - 10} more")
            lines.append("")

    # Actions based on direction
    if params.direction == "template_to_board" and missing_from_board:
        if params.dry_run:
            lines.append("## Planned Actions (Dry Run)")
            lines.append(f"Would create {len(missing_from_board)} cards from template.")
        else:
            lines.append("## Actions Taken")
            created = 0
            for task in template_tasks:
                if task["title"] in missing_from_board:
                    card_data = {
                        "title": task["title"],
                        "icon": task.get("icon", "📋"),
                        "properties": {}
                    }
                    result = await _api_request(
                        "POST",
                        f"/boards/{params.board_id}/cards",
                        data=card_data,
                        params={"disable_notify": "true"}
                    )
                    if not (isinstance(result, dict) and "error" in result):
                        created += 1

            lines.append(f"✅ Created {created} cards from template.")

    elif params.direction == "board_to_template" and extra_in_board:
        if params.dry_run:
            lines.append("## Feedback Proposals (Dry Run)")
            lines.append(f"Would propose {len(extra_in_board)} new tasks for template.")
        else:
            lines.append("## Feedback Proposals Created")
            # Add to pending proposals
            feedback = template.get("feedback", {"pending_proposals": [], "approved_proposals": [], "rejected_proposals": []})

            for title in extra_in_board:
                proposal_id = f"FP-{datetime.now().strftime('%Y-%m-%d')}-{_generate_block_id()[:6]}"
                feedback["pending_proposals"].append({
                    "id": proposal_id,
                    "created": datetime.now().isoformat(),
                    "type": "add_task",
                    "target": {"phase": 0},  # Needs manual assignment
                    "change": {"title": title},
                    "rationale": f"Task discovered in board {params.board_id}",
                    "source_instances": [{"id": params.board_id, "project": "Unknown"}],
                    "votes": {"approve": [], "reject": []},
                    "status": "pending"
                })
                lines.append(f"- Proposal `{proposal_id}`: Add '{title}'")

            template["feedback"] = feedback

            # Save updated template
            templates = _discover_templates()
            template_info = next((t for t in templates if t["id"] == params.template_id), None)
            if template_info:
                _save_template(template, params.template_id, template_info.get("category", "framework"))

            lines.append("")
            lines.append(f"✅ Created {len(extra_in_board)} feedback proposals.")

    lines.append("")
    lines.append("---")
    lines.append(f"**Summary**: Template has {len(template_tasks)} tasks, Board has {len(board_cards)} cards")

    return "\n".join(lines)


# ============================================================================
# Template Tracking Tools
# ============================================================================

# Template tracking property IDs (constants for board properties)
TRACKING_PROP_TEMPLATE_ID = "bacon-template-id"
TRACKING_PROP_TEMPLATE_VERSION = "bacon-template-version"
TRACKING_PROP_UPGRADE_STATUS = "bacon-upgrade-status"


@mcp.tool(
    name="focalboard_get_board_tracking",
    annotations={
        "title": "Get Board Template Tracking",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_get_board_tracking(params: GetBoardTrackingInput) -> str:
    """
    Get template tracking information for a board.

    Returns the template ID, version, and upgrade status if the board
    was created from a template.

    Args:
        params: GetBoardTrackingInput containing:
            - board_id (str): The board ID

    Returns:
        str: Template tracking info or indication that board is not tracked.
    """
    board = await _api_request("GET", f"/boards/{params.board_id}")

    if isinstance(board, dict) and "error" in board:
        return f"Error: {board['error']}"

    properties = board.get("properties") or {}

    template_id = properties.get(TRACKING_PROP_TEMPLATE_ID, "")
    template_version = properties.get(TRACKING_PROP_TEMPLATE_VERSION, "")
    upgrade_status = properties.get(TRACKING_PROP_UPGRADE_STATUS, "")

    if not template_id:
        return f"Board `{params.board_id}` is not tracked by a template.\n\nUse `focalboard_set_board_tracking` to link it to a template."

    lines = [
        "# Board Template Tracking",
        "",
        f"**Board ID**: `{params.board_id}`",
        f"**Board Title**: {board.get('title', 'Unknown')}",
        "",
        "## Template Information",
        f"- **Template ID**: `{template_id}`",
        f"- **Template Version**: {template_version}",
        f"- **Upgrade Status**: {upgrade_status}",
    ]

    # Check if upgrade is available
    template = _load_template(template_id)
    if template:
        current_version = template.get("meta", {}).get("version", "0.0.0")
        if current_version != template_version:
            lines.append("")
            lines.append(f"⚠️ **Upgrade Available**: Template is now at v{current_version}")
            lines.append("Use `focalboard_sync_template` to check differences.")

    return "\n".join(lines)


@mcp.tool(
    name="focalboard_set_board_tracking",
    annotations={
        "title": "Set Board Template Tracking",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_set_board_tracking(params: SetBoardTrackingInput) -> str:
    """
    Set template tracking properties on a board.

    Links a board to a template for tracking versions and upgrades.

    Args:
        params: SetBoardTrackingInput containing:
            - board_id (str): The board ID
            - template_id (str): Template ID
            - template_version (str): Template version (e.g., '1.0.0')
            - upgrade_status (str): 'current', 'available', or 'skipped'

    Returns:
        str: Confirmation of tracking properties set.
    """
    # Update board properties
    update_data = {
        "updatedProperties": {
            TRACKING_PROP_TEMPLATE_ID: params.template_id,
            TRACKING_PROP_TEMPLATE_VERSION: params.template_version,
            TRACKING_PROP_UPGRADE_STATUS: params.upgrade_status
        }
    }

    result = await _api_request("PATCH", f"/boards/{params.board_id}", data=update_data)

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    return f"""# Template Tracking Set

**Board ID**: `{params.board_id}`

## Tracking Properties
- **Template ID**: `{params.template_id}`
- **Template Version**: {params.template_version}
- **Upgrade Status**: {params.upgrade_status}

Use `focalboard_sync_template` to sync changes with the template."""


@mcp.tool(
    name="focalboard_get_phase_tasks",
    annotations={
        "title": "Get Phase Tasks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_get_phase_tasks(params: GetPhaseTasksInput) -> str:
    """
    Get all tasks for a specific BACON-AI phase.

    Filters cards by phase number based on task ID pattern (P00XX-TXXXX).

    Args:
        params: GetPhaseTasksInput containing:
            - board_id (str): The board ID
            - phase_number (int): Phase number (0-12)
            - response_format: 'markdown' or 'json'

    Returns:
        str: List of tasks for the specified phase with their status.
    """
    cards = await _api_request("GET", f"/boards/{params.board_id}/cards")

    if isinstance(cards, dict) and "error" in cards:
        return f"Error: {cards['error']}"

    if not isinstance(cards, list):
        return "Error: No cards found"

    # Filter cards by phase pattern
    import re
    phase_pattern = f"P00{params.phase_number:02d}"
    phase_cards = [
        c for c in cards
        if c.get("title", "").startswith(phase_pattern)
    ]

    # Get board for property resolution
    board = await _api_request("GET", f"/boards/{params.board_id}")
    status_options = {}
    if isinstance(board, dict):
        for prop in board.get("cardProperties", []):
            if prop.get("name") == "Status":
                status_options = {
                    opt["id"]: opt["value"]
                    for opt in prop.get("options", [])
                }
                status_prop_id = prop.get("id", "")
                break

    # Phase metadata
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

    meta = phase_metadata.get(params.phase_number, {"name": f"Phase {params.phase_number}", "icon": "📋", "leader": "Unknown"})

    if params.response_format == ResponseFormat.JSON:
        return json.dumps({
            "phase": params.phase_number,
            "name": meta["name"],
            "leader": meta["leader"],
            "tasks": [
                {
                    "id": c.get("id"),
                    "title": c.get("title"),
                    "icon": c.get("icon"),
                    "status": status_options.get(c.get("properties", {}).get(status_prop_id, ""), "Unknown")
                }
                for c in phase_cards
            ]
        }, indent=2)

    # Count by status
    status_counts = {}
    for c in phase_cards:
        status = status_options.get(c.get("properties", {}).get(status_prop_id, ""), "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    lines = [
        f"# {meta['icon']} Phase {params.phase_number}: {meta['name']}",
        "",
        f"**Leader**: {meta['leader']}",
        f"**Tasks**: {len(phase_cards)}",
        "",
        "## Status Summary",
    ]

    for status, count in sorted(status_counts.items()):
        pct = (count / len(phase_cards) * 100) if phase_cards else 0
        lines.append(f"- **{status}**: {count} ({pct:.0f}%)")

    lines.append("")
    lines.append("## Tasks")
    lines.append("")

    for card in sorted(phase_cards, key=lambda c: c.get("title", "")):
        title = card.get("title", "Untitled")
        icon = card.get("icon", "📋")
        status = status_options.get(card.get("properties", {}).get(status_prop_id, ""), "Unknown")
        card_id = card.get("id", "")

        status_icon = {"Not Started": "⬜", "In Progress": "🔵", "Completed": "✅", "Blocked": "🔴"}.get(status, "⬜")
        lines.append(f"- {status_icon} {icon} **{title}** (`{card_id}`)")

    return "\n".join(lines)


@mcp.tool(
    name="focalboard_get_phase_agent_context",
    annotations={
        "title": "Get Phase Agent Context",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def focalboard_get_phase_agent_context(params: GetPhaseAgentContextInput) -> str:
    """
    Get complete context for an AI agent to work on a specific phase.

    Returns the phase role, responsibilities, tasks, and agent instructions
    in a format suitable for sub-agent injection.

    This is designed for deterministic workflow orchestration where a main
    agent spawns specialized sub-agents for each phase.

    Args:
        params: GetPhaseAgentContextInput containing:
            - board_id (str): The board ID
            - phase_number (int): Phase number (0-12)

    Returns:
        str: Complete agent context including role, tasks, and instructions.

    Usage in orchestration:
        1. Main agent calls this to get phase context
        2. Spawns sub-agent with the returned context as system prompt
        3. Sub-agent completes phase tasks
        4. Returns control to main agent for next phase
    """
    # Get phase tasks
    cards = await _api_request("GET", f"/boards/{params.board_id}/cards")

    if isinstance(cards, dict) and "error" in cards:
        return f"Error: {cards['error']}"

    if not isinstance(cards, list):
        cards = []

    # Filter by phase
    phase_pattern = f"P00{params.phase_number:02d}"
    phase_cards = [c for c in cards if c.get("title", "").startswith(phase_pattern)]

    # Get board for property definitions
    board = await _api_request("GET", f"/boards/{params.board_id}")
    status_options = {}
    status_prop_id = ""
    if isinstance(board, dict):
        for prop in board.get("cardProperties", []):
            if prop.get("name") == "Status":
                status_options = {opt["id"]: opt["value"] for opt in prop.get("options", [])}
                status_prop_id = prop.get("id", "")

    # Phase definitions with detailed context
    phase_definitions = {
        0: {
            "name": "Verification Protocol",
            "icon": "🔍",
            "leader": "Research Specialist",
            "role_description": """You are a Research Specialist responsible for the Verification Protocol phase.
Your primary goal is to ensure we're not solving an already-solved problem and to gather existing knowledge.

KEY RESPONSIBILITIES:
- Query the lessons learned database for similar problems
- Search for existing solutions and best practices
- Consult external AI models for alternative perspectives
- Document current state and assumptions
- Validate that the problem hasn't already been solved

CRITICAL: This phase MUST complete before any implementation begins.
Do NOT skip this phase - it prevents wasted effort on solved problems.""",
            "success_criteria": [
                "Lessons learned database queried",
                "Web search for best practices completed",
                "External AI models consulted",
                "Current state documented",
                "Problem novelty validated"
            ]
        },
        1: {
            "name": "Empathetic Problem Definition",
            "icon": "💭",
            "leader": "Elisabeth (Orchestrator) + Maisie (Human Experience)",
            "role_description": """You are leading the Empathetic Problem Definition phase using Design Thinking principles.
Your goal is to deeply understand the problem from the user's perspective.

KEY RESPONSIBILITIES:
- Create an empathy map (Think, Feel, Say, Do)
- Define the problem using 5W+1H framework (Who, What, When, Where, Why, How)
- Apply Six Thinking Hats review for comprehensive analysis
- Document success criteria and constraints
- Get stakeholder approval on problem definition

CRITICAL: Do NOT propose solutions yet - focus only on understanding the problem.""",
            "success_criteria": [
                "Empathy map created",
                "5W+1H framework completed",
                "Six Thinking Hats applied",
                "Success criteria documented",
                "Stakeholder approval obtained"
            ]
        },
        2: {
            "name": "Multi-Dimensional Data Gathering",
            "icon": "📊",
            "leader": "Research Specialist",
            "role_description": """You are a Research Specialist responsible for comprehensive data gathering.
Your goal is to collect all relevant information using Systems Thinking principles.

KEY RESPONSIBILITIES:
- Create a context map of system boundaries
- Conduct thorough stakeholder analysis
- Collect data from all relevant sources
- Identify data gaps and plan mitigation
- Organize findings for analysis phase

APPROACH: Use multiple perspectives and data sources to ensure completeness.""",
            "success_criteria": [
                "Context map created",
                "Stakeholder analysis complete",
                "Data collected from all sources",
                "Data gaps identified",
                "Findings organized"
            ]
        },
        3: {
            "name": "Systematic Analysis & Insights",
            "icon": "🔬",
            "leader": "George (Systems Architect)",
            "role_description": """You are George, the Systems Architect, leading the analysis phase.
Your goal is to derive actionable insights from gathered data using Systems Thinking.

KEY RESPONSIBILITIES:
- Identify patterns and trends in data
- Map causal relationships and feedback loops
- Identify root causes (use 5 Whys technique)
- Document key insights and implications
- Prepare recommendations for solution generation

FOCUS: Look for systemic issues, not just symptoms.""",
            "success_criteria": [
                "Patterns identified",
                "Causal relationships mapped",
                "Root causes identified",
                "Insights documented",
                "Recommendations prepared"
            ]
        },
        4: {
            "name": "Creative Solution Generation",
            "icon": "💡",
            "leader": "Finn (Innovation Engineer)",
            "role_description": """You are Finn, the Innovation Engineer, leading creative solution generation.
Your goal is to generate multiple solution options using TRIZ and creative techniques.

KEY RESPONSIBILITIES:
- Apply TRIZ 40 inventive principles
- Generate at least 3 distinct solution approaches
- Consider unconventional and innovative options
- Document pros and cons of each approach
- Prepare solutions for evaluation phase

MINDSET: Think outside the box - the best solution may be non-obvious.""",
            "success_criteria": [
                "TRIZ principles applied",
                "3+ solutions generated",
                "Innovative options considered",
                "Pros/cons documented",
                "Solutions ready for evaluation"
            ]
        },
        5: {
            "name": "Systematic Solution Evaluation",
            "icon": "⚖️",
            "leader": "Perspective Analyst",
            "role_description": """You are the Perspective Analyst, leading systematic solution evaluation.
Your goal is to objectively evaluate all proposed solutions using multiple criteria.

KEY RESPONSIBILITIES:
- Define evaluation criteria (cost, time, risk, value)
- Score each solution against criteria
- Apply Six Thinking Hats for balanced review
- Identify risks and mitigations for each
- Rank solutions with justification

OBJECTIVITY: Evaluate based on criteria, not preference.""",
            "success_criteria": [
                "Evaluation criteria defined",
                "Solutions scored",
                "Six Hats review completed",
                "Risks identified",
                "Solutions ranked"
            ]
        },
        6: {
            "name": "Consensus & Solution Selection",
            "icon": "🗳️",
            "leader": "Elisabeth (Orchestrator)",
            "role_description": """You are Elisabeth, the Orchestrator, leading consensus building and solution selection.
Your goal is to facilitate team consensus on the chosen solution.

KEY RESPONSIBILITIES:
- Present evaluation results to stakeholders
- Facilitate discussion on trade-offs
- Address concerns and objections
- Build consensus on selected solution
- Document decision rationale

FACILITATION: Ensure all voices are heard before finalizing.""",
            "success_criteria": [
                "Results presented",
                "Trade-offs discussed",
                "Concerns addressed",
                "Consensus achieved",
                "Decision documented"
            ]
        },
        7: {
            "name": "Design Excellence (WRICEF)",
            "icon": "📐",
            "leader": "Giuseppe (Documentation Manager)",
            "role_description": """You are Giuseppe, the Documentation Manager, leading design specification.
Your goal is to create comprehensive design documents using WRICEF framework.

WRICEF Components:
- Workflows: Process flows and sequences
- Reports: Output and reporting requirements
- Interfaces: Integration points and APIs
- Conversions: Data migration needs
- Enhancements: Customizations required
- Forms: User interface specifications

KEY RESPONSIBILITIES:
- Create detailed technical specifications
- Document all WRICEF components
- Define acceptance criteria
- Plan for testing requirements

DETAIL: Be specific enough that implementation is unambiguous.""",
            "success_criteria": [
                "Workflows documented",
                "Interfaces specified",
                "Acceptance criteria defined",
                "Test requirements planned",
                "Design reviewed"
            ]
        },
        8: {
            "name": "Implementation Planning",
            "icon": "📋",
            "leader": "Elisabeth (Orchestrator) + Lily (QA)",
            "role_description": """You are leading Implementation Planning with Elisabeth and Lily.
Your goal is to create a detailed implementation plan with quality gates.

KEY RESPONSIBILITIES:
- Break down work into implementable tasks
- Define dependencies and sequence
- Estimate effort and timeline
- Plan quality checkpoints
- Assign resources and responsibilities

PLANNING: Account for testing, review, and iteration time.""",
            "success_criteria": [
                "Tasks broken down",
                "Dependencies mapped",
                "Timeline estimated",
                "Quality gates defined",
                "Resources assigned"
            ]
        },
        9: {
            "name": "Build → Test (TDD)",
            "icon": "🔨",
            "leader": "Lily (Quality Assurance)",
            "role_description": """You are Lily, the Quality Assurance lead, overseeing Test-Driven Development.
Your goal is to ensure high-quality implementation through TDD practices.

KEY RESPONSIBILITIES:
- Write tests BEFORE implementation
- Implement code to pass tests
- Refactor while maintaining test coverage
- Conduct code reviews
- Track and fix defects

TDD CYCLE: Red (fail) → Green (pass) → Refactor

QUALITY: No code merges without passing tests and review.""",
            "success_criteria": [
                "Tests written first",
                "All tests passing",
                "Code reviewed",
                "Coverage adequate",
                "Defects resolved"
            ]
        },
        10: {
            "name": "Go-Live Prep & Change Management",
            "icon": "🚀",
            "leader": "Elisabeth (Orchestrator) + Connor (DevOps)",
            "role_description": """You are leading Go-Live Preparation with Elisabeth and Connor.
Your goal is to prepare for production deployment with change management.

KEY RESPONSIBILITIES:
- Create deployment runbook
- Plan rollback procedures
- Prepare user communication
- Train support team
- Conduct final UAT

READINESS: Don't go live until all gates are green.""",
            "success_criteria": [
                "Runbook created",
                "Rollback planned",
                "Users notified",
                "Support trained",
                "UAT approved"
            ]
        },
        11: {
            "name": "Production Deployment",
            "icon": "🌐",
            "leader": "Connor (DevOps)",
            "role_description": """You are Connor, the DevOps lead, executing production deployment.
Your goal is to deploy safely and monitor for issues.

KEY RESPONSIBILITIES:
- Execute deployment runbook
- Monitor system health
- Verify functionality in production
- Address immediate issues
- Communicate deployment status

CAUTION: Have rollback ready at all times during deployment.""",
            "success_criteria": [
                "Deployment executed",
                "Health monitored",
                "Functionality verified",
                "Issues addressed",
                "Status communicated"
            ]
        },
        12: {
            "name": "Reflection & Learning (SSC)",
            "icon": "📝",
            "leader": "SE-Agent Observer",
            "role_description": """You are the SE-Agent Observer, leading reflection and organizational learning.
SSC = Stop, Start, Continue retrospective.

KEY RESPONSIBILITIES:
- Conduct SSC retrospective
- Document lessons learned
- Update proven approaches database
- Propose template improvements
- Celebrate successes

LEARNING: What we learn here improves ALL future projects.""",
            "success_criteria": [
                "Retrospective completed",
                "Lessons documented",
                "Database updated",
                "Improvements proposed",
                "Team recognized"
            ]
        },
    }

    phase_def = phase_definitions.get(params.phase_number, {
        "name": f"Phase {params.phase_number}",
        "icon": "📋",
        "leader": "Unknown",
        "role_description": "No specific role description available.",
        "success_criteria": []
    })

    # Build task list with status
    task_lines = []
    pending_tasks = []
    for card in sorted(phase_cards, key=lambda c: c.get("title", "")):
        title = card.get("title", "Untitled")
        status = status_options.get(card.get("properties", {}).get(status_prop_id, ""), "Unknown")
        card_id = card.get("id", "")

        if status in ["Not Started", "In Progress"]:
            pending_tasks.append({"title": title, "id": card_id, "status": status})

        status_mark = "✅" if status == "Completed" else "⬜" if status == "Not Started" else "🔵" if status == "In Progress" else "🔴"
        task_lines.append(f"  - [{status_mark}] {title}")

    # Build agent context
    context = f"""# BACON-AI Phase {params.phase_number} Agent Context

## Your Role
{phase_def['role_description']}

## Phase Information
- **Phase**: {params.phase_number} - {phase_def['name']} {phase_def['icon']}
- **Leader**: {phase_def['leader']}
- **Board ID**: `{params.board_id}`

## Success Criteria
{chr(10).join(f'- [ ] {c}' for c in phase_def.get('success_criteria', []))}

## Tasks in This Phase
{chr(10).join(task_lines)}

## Pending Tasks (Your Focus)
{chr(10).join(f"- **{t['title']}** (`{t['id']}`) - {t['status']}" for t in pending_tasks) or "All tasks completed!"}

## Instructions for Sub-Agent
1. Review your role description carefully
2. Work through pending tasks sequentially
3. Update task status as you progress (use focalboard_update_card_properties)
4. Mark tasks as 'Completed' when done
5. Document any blockers or issues
6. When all tasks complete, return control to orchestrator

## API Tools Available
- `focalboard_update_card_properties` - Update task status
- `focalboard_add_content_block` - Add notes to tasks
- `focalboard_update_checkbox` - Mark checklist items complete
- `focalboard_search_cards` - Find related tasks

## Handoff Protocol
When this phase is complete, report:
1. Summary of completed tasks
2. Any issues encountered
3. Recommendations for next phase
4. Updated status of all tasks
"""

    return context


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    if not FOCALBOARD_TOKEN:
        print("Warning: FOCALBOARD_TOKEN not set. API calls will fail.", file=sys.stderr)
        print(f"Set it with: export FOCALBOARD_TOKEN='your-token'", file=sys.stderr)

    print(f"Starting Focalboard MCP Server...", file=sys.stderr)
    print(f"  URL: {FOCALBOARD_URL}", file=sys.stderr)
    print(f"  Token: {'Set' if FOCALBOARD_TOKEN else 'NOT SET'}", file=sys.stderr)
    print(f"  Template Dir: {TEMPLATE_BASE_DIR}", file=sys.stderr)
    print(f"  Tools: 30 tools available", file=sys.stderr)

    mcp.run()
