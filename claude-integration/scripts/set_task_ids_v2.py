#!/usr/bin/env python3
"""
Set unique task IDs for all BACON-AI Focalboard cards using blocks API.
"""

import asyncio
import httpx
import json
import re

# Configuration
FOCALBOARD_URL = "http://localhost:8000"
AUTH_TOKEN = "k77tg84g87pd6tjk7rdho1kqs9h"
BOARD_ID = "bd5mw98s3cjftjnef77q8c4oone"
NUMBER_PROP_ID = "a5p9bpedehti9yph1uuehqighue"

# Task ID mapping
TASK_IDS = {
    "P00": 0, "P00-T01": 1, "P00-T02": 2, "P00-T03": 3, "P00-T04": 4, "P00-T05": 5,
    "P01": 100, "P01-T01": 101, "P01-T02": 102, "P01-T03": 103, "P01-T04": 104, "P01-T05": 105,
    "P02": 200, "P02-T01": 201, "P02-T02": 202, "P02-T03": 203, "P02-T04": 204, "P02-T05": 205,
    "P03": 300, "P03-T01": 301, "P03-T02": 302, "P03-T03": 303, "P03-T04": 304, "P03-T05": 305,
    "P04": 400, "P04-T01": 401, "P04-T02": 402, "P04-T03": 403, "P04-T04": 404, "P04-T05": 405,
    "P05": 500, "P05-T01": 501, "P05-T02": 502, "P05-T03": 503, "P05-T04": 504, "P05-T05": 505,
    "P06": 600, "P06-T01": 601, "P06-T02": 602, "P06-T03": 603, "P06-T04": 604, "P06-T05": 605,
    "P07": 700, "P07-T01": 701, "P07-T02": 702, "P07-T03": 703, "P07-T04": 704, "P07-T05": 705,
    "P08": 800, "P08-T01": 801, "P08-T02": 802, "P08-T03": 803, "P08-T04": 804, "P08-T05": 805,
    "P09": 900, "P09-T01": 901, "P09-T02": 902, "P09-T03": 903, "P09-T04": 904, "P09-T05": 905, "P09-T06": 906,
    "P10": 1000, "P10-T01": 1001, "P10-T02": 1002, "P10-T03": 1003, "P10-T04": 1004, "P10-T05": 1005,
    "P11": 1100, "P11-T01": 1101, "P11-T02": 1102, "P11-T03": 1103, "P11-T04": 1104, "P11-T05": 1105, "P11-T06": 1106,
    "P12": 1200, "P12-T01": 1201, "P12-T02": 1202, "P12-T03": 1203, "P12-T04": 1204, "P12-T05": 1205, "P12-T06": 1206, "P12-T07": 1207,
}

def get_headers():
    return {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

def extract_task_key(title):
    """Extract task key like P00-T01 or P00 from title."""
    match = re.match(r'^(P\d+-T\d+|P\d+)', title)
    return match.group(1) if match else None

async def main():
    print("=" * 60)
    print("BACON-AI Task ID Assignment (v2)")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get all cards using blocks API
        url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks?type=card"
        response = await client.get(url, headers=get_headers())

        if response.status_code != 200:
            print(f"Failed to get blocks: {response.status_code}")
            return

        blocks = response.json()
        print(f"Found {len(blocks)} card blocks")

        updated = 0
        skipped = 0

        for block in blocks:
            title = block.get("title", "")
            task_key = extract_task_key(title)

            if task_key and task_key in TASK_IDS:
                task_id = TASK_IDS[task_key]
                card_id = block["id"]

                # Get current properties
                current_props = block.get("fields", {}).get("properties", {})

                # Add/update the Number property
                current_props[NUMBER_PROP_ID] = str(task_id)

                # Update using blocks PATCH endpoint
                patch_url = f"{FOCALBOARD_URL}/api/v2/boards/{BOARD_ID}/blocks/{card_id}"
                patch_data = {
                    "updatedFields": {
                        "properties": current_props
                    }
                }

                patch_response = await client.patch(patch_url, headers=get_headers(), json=patch_data)

                if patch_response.status_code == 200:
                    print(f"✅ {task_key} -> ID {task_id}")
                    updated += 1
                else:
                    print(f"❌ {task_key}: {patch_response.status_code} - {patch_response.text[:100]}")
            else:
                skipped += 1

        print()
        print("=" * 60)
        print(f"Complete: {updated} updated, {skipped} skipped")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
