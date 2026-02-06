#!/usr/bin/env python3
"""
Fix content blocks - properly link them to cards.

ISSUE: The original script set contentOrder with client-generated IDs,
but Focalboard server generates its own IDs. This script:
1. Finds all orphaned content blocks
2. Links them to the correct cards
3. Updates contentOrder with actual block IDs
"""

import asyncio
import httpx
from collections import defaultdict

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


async def main():
    print("=" * 70)
    print("Fix Content Blocks - Link to Cards")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Get all blocks
        blocks_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks"
        response = await client.get(blocks_url, headers=get_headers())

        if response.status_code != 200:
            print(f"Failed to get blocks: {response.status_code}")
            return

        blocks = response.json()

        # Separate cards and content blocks
        cards = {b["id"]: b for b in blocks if b.get("type") == "card"}
        content_blocks = [b for b in blocks if b.get("type") in ["text", "checkbox", "divider"]]

        print(f"Found {len(cards)} cards")
        print(f"Found {len(content_blocks)} content blocks")

        # Group content blocks by parentId
        blocks_by_parent = defaultdict(list)
        for block in content_blocks:
            parent_id = block.get("parentId")
            blocks_by_parent[parent_id].append(block)

        # Find cards that have content blocks
        cards_with_content = set(blocks_by_parent.keys()) & set(cards.keys())
        print(f"Cards with content blocks: {len(cards_with_content)}")

        # Find orphaned blocks (parentId not matching any card)
        orphan_parents = set(blocks_by_parent.keys()) - set(cards.keys())
        orphan_parents.discard(BOARD_ID)  # Board-level blocks are OK

        if orphan_parents:
            print(f"\n⚠️  Found {len(orphan_parents)} orphan parent IDs:")
            for parent_id in list(orphan_parents)[:5]:
                print(f"   - {parent_id}: {len(blocks_by_parent[parent_id])} blocks")

        # For each card, check and fix contentOrder
        fixed = 0
        for card_id, card in cards.items():
            title = card.get("title", "")
            if not title.startswith("P0"):
                continue

            current_order = card.get("fields", {}).get("contentOrder", [])
            actual_blocks = blocks_by_parent.get(card_id, [])

            if not actual_blocks:
                continue

            # Get actual block IDs that belong to this card
            actual_ids = [b["id"] for b in actual_blocks]

            # Check if contentOrder needs fixing
            missing = [bid for bid in current_order if bid not in actual_ids]
            extra = [bid for bid in actual_ids if bid not in current_order]

            if missing or extra:
                # Build proper contentOrder based on block types
                # Order: text (description), divider, text (header), checkboxes, divider, text (comment)
                text_blocks = sorted([b for b in actual_blocks if b["type"] == "text"],
                                     key=lambda x: x.get("createAt", 0))
                divider_blocks = sorted([b for b in actual_blocks if b["type"] == "divider"],
                                        key=lambda x: x.get("createAt", 0))
                checkbox_blocks = sorted([b for b in actual_blocks if b["type"] == "checkbox"],
                                         key=lambda x: x.get("createAt", 0))

                new_order = []
                # First text block (description)
                if text_blocks:
                    new_order.append(text_blocks[0]["id"])
                # First divider
                if divider_blocks:
                    new_order.append(divider_blocks[0]["id"])
                # Second text block (checklist header)
                if len(text_blocks) > 1:
                    new_order.append(text_blocks[1]["id"])
                # All checkboxes
                for cb in checkbox_blocks:
                    new_order.append(cb["id"])
                # Second divider
                if len(divider_blocks) > 1:
                    new_order.append(divider_blocks[1]["id"])
                # Third text block (comment)
                if len(text_blocks) > 2:
                    new_order.append(text_blocks[2]["id"])

                # Update contentOrder
                patch_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks/{card_id}"
                patch_data = {
                    "updatedFields": {
                        "contentOrder": new_order
                    }
                }

                patch_response = await client.patch(patch_url, headers=get_headers(), json=patch_data)

                if patch_response.status_code == 200:
                    fixed += 1
                    print(f"✅ Fixed {title[:40]}: {len(new_order)} blocks linked")
                else:
                    print(f"❌ Failed to fix {title[:40]}: {patch_response.status_code}")

        print()
        print("=" * 70)
        print(f"Fixed contentOrder on {fixed} cards")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
