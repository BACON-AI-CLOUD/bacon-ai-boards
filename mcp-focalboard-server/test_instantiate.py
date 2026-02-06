#!/usr/bin/env python3
"""
Test instantiating a template as a new Focalboard board.
"""

import asyncio
import os
import sys
from pathlib import Path

# Load environment variables from .env file
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

from server import (
    focalboard_instantiate_template,
    focalboard_list_boards,
    focalboard_list_cards,
    focalboard_sync_template,
    InstantiateTemplateInput,
    SyncTemplateInput,
    TeamInput,
    ListCardsInput,
    ResponseFormat,
    FOCALBOARD_URL
)


async def test_instantiate_template():
    """Test creating a board from a template."""
    print("\n" + "=" * 60)
    print("TEST: Instantiate Template")
    print("=" * 60)

    params = InstantiateTemplateInput(
        template_id="bacon-ai-12-phase",
        project_name="Test Project - Template Instantiation",
        team_id="0"
    )

    result = await focalboard_instantiate_template(params)
    print(result)

    # Extract board ID from result
    board_id = None
    for line in result.split("\n"):
        if "Board ID" in line and "`" in line:
            board_id = line.split("`")[1]
            break

    return board_id


async def test_list_boards():
    """List all boards to verify creation."""
    print("\n" + "=" * 60)
    print("TEST: List Boards")
    print("=" * 60)

    params = TeamInput(team_id="0", response_format=ResponseFormat.MARKDOWN)
    result = await focalboard_list_boards(params)
    print(result[:1000] + "..." if len(result) > 1000 else result)

    return "Template Instantiation" in result


async def test_list_cards(board_id: str):
    """List cards on the new board."""
    print("\n" + "=" * 60)
    print(f"TEST: List Cards on Board {board_id}")
    print("=" * 60)

    params = ListCardsInput(
        board_id=board_id,
        limit=20,
        response_format=ResponseFormat.MARKDOWN
    )
    result = await focalboard_list_cards(params)
    print(result[:1500] + "..." if len(result) > 1500 else result)

    return "Cards" in result


async def test_sync_template(board_id: str):
    """Test syncing the board with its template."""
    print("\n" + "=" * 60)
    print(f"TEST: Sync Template (dry run)")
    print("=" * 60)

    params = SyncTemplateInput(
        board_id=board_id,
        template_id="bacon-ai-12-phase",
        direction="template_to_board",
        dry_run=True
    )
    result = await focalboard_sync_template(params)
    print(result)

    return "Sync Report" in result


async def main():
    """Run all tests."""
    print("=" * 60)
    print("TEMPLATE INSTANTIATION TEST")
    print(f"Server: {FOCALBOARD_URL}")
    print("=" * 60)

    # Test instantiation
    board_id = await test_instantiate_template()

    if not board_id:
        print("\n❌ FAILED: Could not create board from template")
        return False

    print(f"\n✅ Created board: {board_id}")

    # Test listing boards
    await test_list_boards()

    # Test listing cards
    await test_list_cards(board_id)

    # Test sync
    await test_sync_template(board_id)

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print(f"\n✅ Board created successfully!")
    print(f"View at: {FOCALBOARD_URL}/board/{board_id}")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
