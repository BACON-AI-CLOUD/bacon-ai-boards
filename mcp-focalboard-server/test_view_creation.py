#!/usr/bin/env python3
"""Test that board view is created correctly."""

import asyncio
import os
from pathlib import Path

# Load environment
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
    InstantiateTemplateInput,
    _api_request,
    FOCALBOARD_URL
)


async def main():
    print("=" * 60)
    print("TEST: Create Board with Default View")
    print("=" * 60)

    # Create a new board from template
    params = InstantiateTemplateInput(
        template_id="bacon-ai-12-phase",
        project_name="View Test Project",
        team_id="0"
    )

    result = await focalboard_instantiate_template(params)
    print(result)

    # Extract board ID
    board_id = None
    for line in result.split("\n"):
        if "Board ID" in line and "`" in line:
            board_id = line.split("`")[1]
            break

    if not board_id:
        print("\n❌ Could not extract board ID")
        return False

    # Verify view was created
    print("\n" + "=" * 60)
    print("Verifying view creation...")
    print("=" * 60)

    views = await _api_request("GET", f"/boards/{board_id}/blocks?type=view")

    if isinstance(views, list):
        print(f"✅ Found {len(views)} view(s)")
        for v in views:
            print(f"   - {v.get('title', 'Unnamed')} (type: {v.get('fields', {}).get('viewType', 'unknown')})")
    else:
        print(f"❌ Error getting views: {views}")
        return False

    print(f"\n✅ Board ready at: {FOCALBOARD_URL}/board/{board_id}")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
