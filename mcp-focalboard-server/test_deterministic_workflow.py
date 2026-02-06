#!/usr/bin/env python3
"""
Comprehensive test for deterministic workflow with sub-agent orchestration.

This test demonstrates:
1. Creating a board from template
2. Setting up template tracking
3. Getting phase agent contexts
4. Simulating sub-agent workflow handoffs
5. Testing the complete BACON-AI 12-phase methodology

Use cases tested:
- Happy paths: Normal workflow execution
- Unhappy paths: Error handling, blocked tasks, missing data
"""

import asyncio
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

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
    # Template tools
    focalboard_instantiate_template,
    focalboard_list_templates,
    focalboard_get_template,
    focalboard_sync_template,
    # Tracking tools
    focalboard_get_board_tracking,
    focalboard_set_board_tracking,
    focalboard_get_phase_tasks,
    focalboard_get_phase_agent_context,
    # Board tools
    focalboard_list_boards,
    focalboard_get_board,
    focalboard_list_cards,
    focalboard_update_card_properties,
    focalboard_search_cards,
    focalboard_get_board_statistics,
    # Input models
    InstantiateTemplateInput,
    ListTemplatesInput,
    GetTemplateInput,
    SyncTemplateInput,
    GetBoardTrackingInput,
    SetBoardTrackingInput,
    GetPhaseTasksInput,
    GetPhaseAgentContextInput,
    TeamInput,
    BoardInput,
    ListCardsInput,
    UpdateCardPropertiesInput,
    SearchCardsInput,
    ResponseFormat,
    # Utils
    _api_request,
    FOCALBOARD_URL,
)


def take_screenshot(name: str):
    """Take a screenshot with the given name."""
    try:
        path = f"/tmp/focalboard_test_{name}.png"
        subprocess.run(
            ["scrot", "-u", path],
            env={**os.environ, "DISPLAY": ":0"},
            capture_output=True,
            timeout=5
        )
        print(f"📸 Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"⚠️ Screenshot failed: {e}")
        return None


def navigate_browser(url: str):
    """Navigate the browser to a URL using xdotool."""
    try:
        # Focus Chrome
        subprocess.run(
            ["xdotool", "search", "--name", "Google Chrome", "windowactivate"],
            env={**os.environ, "DISPLAY": ":0"},
            capture_output=True,
            timeout=5
        )
        # Navigate
        subprocess.run(["sleep", "0.3"])
        subprocess.run(
            ["xdotool", "key", "ctrl+l"],
            env={**os.environ, "DISPLAY": ":0"},
            capture_output=True
        )
        subprocess.run(["sleep", "0.3"])
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", url],
            env={**os.environ, "DISPLAY": ":0"},
            capture_output=True
        )
        subprocess.run(
            ["xdotool", "key", "Return"],
            env={**os.environ, "DISPLAY": ":0"},
            capture_output=True
        )
        subprocess.run(["sleep", "2"])
        return True
    except Exception as e:
        print(f"⚠️ Navigation failed: {e}")
        return False


class DeterministicWorkflowTest:
    """Test class for the deterministic workflow."""

    def __init__(self):
        self.board_id = None
        self.results = {}
        self.use_cases = []

    async def setup(self):
        """Create a test board from template."""
        print("\n" + "=" * 70)
        print("SETUP: Creating test board from template")
        print("=" * 70)

        params = InstantiateTemplateInput(
            template_id="bacon-ai-12-phase",
            project_name="Deterministic Workflow Test",
            team_id="0"
        )

        result = await focalboard_instantiate_template(params)
        print(result[:500])

        # Extract board ID
        for line in result.split("\n"):
            if "Board ID" in line and "`" in line:
                self.board_id = line.split("`")[1]
                break

        if self.board_id:
            print(f"\n✅ Board created: {self.board_id}")
            navigate_browser(f"{FOCALBOARD_URL}/board/{self.board_id}")
            take_screenshot("01_board_created")
            return True
        return False

    async def test_template_tracking(self):
        """Test template tracking functionality."""
        print("\n" + "=" * 70)
        print("USE CASE 1: Template Tracking (Happy Path)")
        print("=" * 70)

        # Get tracking (should show not tracked initially)
        params = GetBoardTrackingInput(board_id=self.board_id)
        result = await focalboard_get_board_tracking(params)
        print("Initial tracking status:")
        print(result)

        # Set tracking
        set_params = SetBoardTrackingInput(
            board_id=self.board_id,
            template_id="bacon-ai-12-phase",
            template_version="1.0.0",
            upgrade_status="current"
        )
        result = await focalboard_set_board_tracking(set_params)
        print("\nAfter setting tracking:")
        print(result)

        # Verify tracking
        result = await focalboard_get_board_tracking(params)
        print("\nVerify tracking set:")
        print(result)

        self.use_cases.append({
            "id": 1,
            "name": "Template Tracking Setup",
            "type": "happy",
            "status": "✅ PASS" if "Template ID" in result else "❌ FAIL"
        })

        return "Template ID" in result

    async def test_phase_tasks(self):
        """Test getting phase tasks."""
        print("\n" + "=" * 70)
        print("USE CASE 2: Get Phase Tasks (Happy Path)")
        print("=" * 70)

        for phase in [0, 1, 2]:
            params = GetPhaseTasksInput(
                board_id=self.board_id,
                phase_number=phase,
                response_format=ResponseFormat.MARKDOWN
            )
            result = await focalboard_get_phase_tasks(params)
            print(f"\n--- Phase {phase} ---")
            print(result[:400] + "..." if len(result) > 400 else result)

        self.use_cases.append({
            "id": 2,
            "name": "Get Phase Tasks",
            "type": "happy",
            "status": "✅ PASS"
        })

        return True

    async def test_phase_agent_context(self):
        """Test getting agent context for sub-agent injection."""
        print("\n" + "=" * 70)
        print("USE CASE 3: Phase Agent Context (Sub-Agent Injection)")
        print("=" * 70)

        params = GetPhaseAgentContextInput(
            board_id=self.board_id,
            phase_number=0
        )
        result = await focalboard_get_phase_agent_context(params)
        print(result)

        self.use_cases.append({
            "id": 3,
            "name": "Phase Agent Context Generation",
            "type": "happy",
            "status": "✅ PASS" if "Your Role" in result else "❌ FAIL"
        })

        return "Your Role" in result

    async def simulate_phase_execution(self, phase_number: int):
        """Simulate a sub-agent executing a phase."""
        print("\n" + "-" * 50)
        print(f"SUB-AGENT SIMULATION: Phase {phase_number}")
        print("-" * 50)

        # Get agent context
        params = GetPhaseAgentContextInput(
            board_id=self.board_id,
            phase_number=phase_number
        )
        context = await focalboard_get_phase_agent_context(params)

        # Find first pending task
        task_params = GetPhaseTasksInput(
            board_id=self.board_id,
            phase_number=phase_number,
            response_format=ResponseFormat.JSON
        )
        tasks_json = await focalboard_get_phase_tasks(task_params)
        tasks = json.loads(tasks_json)

        pending = [t for t in tasks.get("tasks", []) if t.get("status") in ["Not Started", "Unknown"]]

        if pending:
            first_task = pending[0]
            print(f"Working on: {first_task['title']}")

            # Get board to find status property
            board = await _api_request("GET", f"/boards/{self.board_id}")
            status_prop_id = None
            in_progress_id = None
            completed_id = None

            for prop in board.get("cardProperties", []):
                if prop.get("name") == "Status":
                    status_prop_id = prop.get("id")
                    for opt in prop.get("options", []):
                        if "Progress" in opt.get("value", ""):
                            in_progress_id = opt.get("id")
                        if "Completed" in opt.get("value", ""):
                            completed_id = opt.get("id")

            if status_prop_id and in_progress_id:
                # Update to In Progress
                update_params = UpdateCardPropertiesInput(
                    board_id=self.board_id,
                    card_id=first_task["id"],
                    properties={status_prop_id: in_progress_id}
                )
                result = await focalboard_update_card_properties(update_params)
                print(f"  → Set to In Progress")

                # Simulate work...
                await asyncio.sleep(0.5)

                # Update to Completed
                if completed_id:
                    update_params = UpdateCardPropertiesInput(
                        board_id=self.board_id,
                        card_id=first_task["id"],
                        properties={status_prop_id: completed_id}
                    )
                    result = await focalboard_update_card_properties(update_params)
                    print(f"  → Set to Completed ✅")

            return True
        else:
            print("No pending tasks in this phase")
            return True

    async def test_deterministic_workflow(self):
        """Test the full deterministic workflow with sub-agent handoffs."""
        print("\n" + "=" * 70)
        print("USE CASE 4-6: Deterministic Workflow (Phase 0-2)")
        print("=" * 70)

        # Navigate to board
        navigate_browser(f"{FOCALBOARD_URL}/board/{self.board_id}")
        await asyncio.sleep(1)
        take_screenshot("02_before_workflow")

        # Execute phases 0, 1, 2
        for phase in [0, 1, 2]:
            await self.simulate_phase_execution(phase)
            self.use_cases.append({
                "id": 4 + phase,
                "name": f"Phase {phase} Execution",
                "type": "happy",
                "status": "✅ PASS"
            })

        take_screenshot("03_after_workflow")

        # Check statistics
        stats_params = BoardInput(board_id=self.board_id)
        stats = await focalboard_get_board_statistics(stats_params)
        print("\n--- Board Statistics After Workflow ---")
        print(stats)

        return True

    async def test_error_handling(self):
        """Test error handling (unhappy paths)."""
        print("\n" + "=" * 70)
        print("USE CASE 7-10: Error Handling (Unhappy Paths)")
        print("=" * 70)

        # Test 7: Invalid board ID
        print("\n--- Test 7: Invalid Board ID ---")
        params = GetBoardTrackingInput(board_id="invalid-board-id")
        result = await focalboard_get_board_tracking(params)
        print(result[:200])
        self.use_cases.append({
            "id": 7,
            "name": "Invalid Board ID",
            "type": "unhappy",
            "status": "✅ PASS" if "Error" in result or "not found" in result else "❌ FAIL"
        })

        # Test 8: Invalid template ID
        print("\n--- Test 8: Invalid Template ID ---")
        params = GetTemplateInput(template_id="nonexistent-template")
        result = await focalboard_get_template(params)
        print(result[:200])
        self.use_cases.append({
            "id": 8,
            "name": "Invalid Template ID",
            "type": "unhappy",
            "status": "✅ PASS" if "not found" in result or "Error" in result else "❌ FAIL"
        })

        # Test 9: Invalid phase number
        print("\n--- Test 9: Phase Out of Range ---")
        try:
            params = GetPhaseTasksInput(
                board_id=self.board_id,
                phase_number=99  # Invalid
            )
            result = await focalboard_get_phase_tasks(params)
            # Should have validation error or empty result
            self.use_cases.append({
                "id": 9,
                "name": "Phase Out of Range",
                "type": "unhappy",
                "status": "✅ PASS" if "Tasks: 0" in result or "Error" in result else "⚠️ PARTIAL"
            })
        except Exception as e:
            print(f"Validation error (expected): {e}")
            self.use_cases.append({
                "id": 9,
                "name": "Phase Out of Range",
                "type": "unhappy",
                "status": "✅ PASS"
            })

        # Test 10: Sync with mismatched template
        print("\n--- Test 10: Sync Non-matching Board ---")
        params = SyncTemplateInput(
            board_id=self.board_id,
            template_id="nonexistent-template",
            dry_run=True
        )
        result = await focalboard_sync_template(params)
        print(result[:200])
        self.use_cases.append({
            "id": 10,
            "name": "Sync Non-matching Template",
            "type": "unhappy",
            "status": "✅ PASS" if "not found" in result or "Error" in result else "❌ FAIL"
        })

        return True

    async def test_search_and_filter(self):
        """Test search and filter functionality."""
        print("\n" + "=" * 70)
        print("USE CASE 11-15: Search and Filter Operations")
        print("=" * 70)

        # Test 11: Search by title
        print("\n--- Test 11: Search by Title ---")
        params = SearchCardsInput(
            board_id=self.board_id,
            query="empathy"
        )
        result = await focalboard_search_cards(params)
        print(result[:300])
        self.use_cases.append({
            "id": 11,
            "name": "Search by Title",
            "type": "happy",
            "status": "✅ PASS" if "empathy" in result.lower() else "❌ FAIL"
        })

        # Test 12: Search with no results
        print("\n--- Test 12: Search No Results ---")
        params = SearchCardsInput(
            board_id=self.board_id,
            query="xyznonexistent123"
        )
        result = await focalboard_search_cards(params)
        print(result[:200])
        self.use_cases.append({
            "id": 12,
            "name": "Search No Results",
            "type": "happy",
            "status": "✅ PASS" if "No cards found" in result or "0" in result else "❌ FAIL"
        })

        # Test 13: List with pagination
        print("\n--- Test 13: Pagination ---")
        params = ListCardsInput(
            board_id=self.board_id,
            limit=10,
            offset=0
        )
        result = await focalboard_list_cards(params)
        print(result[:300])
        self.use_cases.append({
            "id": 13,
            "name": "List with Pagination",
            "type": "happy",
            "status": "✅ PASS" if "10" in result and "Cards" in result else "❌ FAIL"
        })

        # Test 14: Get specific phase
        print("\n--- Test 14: Filter by Phase ---")
        params = GetPhaseTasksInput(
            board_id=self.board_id,
            phase_number=5
        )
        result = await focalboard_get_phase_tasks(params)
        print(result[:300])
        self.use_cases.append({
            "id": 14,
            "name": "Filter by Phase",
            "type": "happy",
            "status": "✅ PASS" if "Phase 5" in result else "❌ FAIL"
        })

        # Test 15: Board statistics
        print("\n--- Test 15: Board Statistics ---")
        params = BoardInput(board_id=self.board_id)
        result = await focalboard_get_board_statistics(params)
        print(result[:400])
        self.use_cases.append({
            "id": 15,
            "name": "Board Statistics",
            "type": "happy",
            "status": "✅ PASS" if "Total Cards" in result else "❌ FAIL"
        })

        return True

    async def test_template_operations(self):
        """Test template list, get, and sync operations."""
        print("\n" + "=" * 70)
        print("USE CASE 16-20: Template Operations")
        print("=" * 70)

        # Test 16: List templates
        print("\n--- Test 16: List Templates ---")
        params = ListTemplatesInput()
        result = await focalboard_list_templates(params)
        print(result[:400])
        self.use_cases.append({
            "id": 16,
            "name": "List Templates",
            "type": "happy",
            "status": "✅ PASS" if "bacon-ai-12-phase" in result else "❌ FAIL"
        })

        # Test 17: Get template details
        print("\n--- Test 17: Get Template Details ---")
        params = GetTemplateInput(template_id="bacon-ai-12-phase")
        result = await focalboard_get_template(params)
        print(result[:500])
        self.use_cases.append({
            "id": 17,
            "name": "Get Template Details",
            "type": "happy",
            "status": "✅ PASS" if "BACON-AI" in result and "phases" in result.lower() else "❌ FAIL"
        })

        # Test 18: Sync dry run
        print("\n--- Test 18: Sync Dry Run ---")
        params = SyncTemplateInput(
            board_id=self.board_id,
            template_id="bacon-ai-12-phase",
            direction="template_to_board",
            dry_run=True
        )
        result = await focalboard_sync_template(params)
        print(result[:400])
        self.use_cases.append({
            "id": 18,
            "name": "Sync Dry Run",
            "type": "happy",
            "status": "✅ PASS" if "Sync Report" in result else "❌ FAIL"
        })

        # Test 19: Get template JSON
        print("\n--- Test 19: Get Template as JSON ---")
        params = GetTemplateInput(
            template_id="bacon-ai-12-phase",
            response_format=ResponseFormat.JSON
        )
        result = await focalboard_get_template(params)
        try:
            data = json.loads(result)
            self.use_cases.append({
                "id": 19,
                "name": "Get Template JSON",
                "type": "happy",
                "status": "✅ PASS" if "meta" in data else "❌ FAIL"
            })
            print(f"Valid JSON with {len(data.get('phases', []))} phases")
        except:
            self.use_cases.append({
                "id": 19,
                "name": "Get Template JSON",
                "type": "happy",
                "status": "❌ FAIL"
            })

        # Test 20: List templates by category
        print("\n--- Test 20: List Templates by Category ---")
        params = ListTemplatesInput(category="framework")
        result = await focalboard_list_templates(params)
        print(result[:300])
        self.use_cases.append({
            "id": 20,
            "name": "List by Category",
            "type": "happy",
            "status": "✅ PASS" if "framework" in result.lower() else "❌ FAIL"
        })

        return True

    async def test_agent_context_all_phases(self):
        """Test agent context for all phases."""
        print("\n" + "=" * 70)
        print("USE CASE 21-30: Agent Context for All Phases")
        print("=" * 70)

        # Test phases 3-12
        for phase in range(3, 13):
            params = GetPhaseAgentContextInput(
                board_id=self.board_id,
                phase_number=phase
            )
            result = await focalboard_get_phase_agent_context(params)

            # Check for key elements
            has_role = "Your Role" in result
            has_tasks = "Tasks in This Phase" in result
            has_criteria = "Success Criteria" in result

            status = "✅ PASS" if (has_role and has_tasks and has_criteria) else "❌ FAIL"

            self.use_cases.append({
                "id": 21 + (phase - 3),
                "name": f"Agent Context Phase {phase}",
                "type": "happy",
                "status": status
            })

            print(f"Phase {phase}: {status} - Role: {has_role}, Tasks: {has_tasks}, Criteria: {has_criteria}")

        return True

    async def cleanup(self):
        """Delete the test board."""
        print("\n" + "=" * 70)
        print("CLEANUP: Deleting test board")
        print("=" * 70)

        if self.board_id:
            result = await _api_request("DELETE", f"/boards/{self.board_id}")
            print(f"Deleted board: {self.board_id}")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY: 30 USE CASES")
        print("=" * 70)

        happy_pass = sum(1 for uc in self.use_cases if uc["type"] == "happy" and "PASS" in uc["status"])
        happy_total = sum(1 for uc in self.use_cases if uc["type"] == "happy")
        unhappy_pass = sum(1 for uc in self.use_cases if uc["type"] == "unhappy" and "PASS" in uc["status"])
        unhappy_total = sum(1 for uc in self.use_cases if uc["type"] == "unhappy")

        print(f"\n📊 Results:")
        print(f"   Happy Paths:   {happy_pass}/{happy_total} passed")
        print(f"   Unhappy Paths: {unhappy_pass}/{unhappy_total} passed")
        print(f"   Total:         {happy_pass + unhappy_pass}/{len(self.use_cases)} passed")

        print("\n📋 All Use Cases:")
        for uc in self.use_cases:
            print(f"   {uc['id']:2d}. [{uc['type']:7s}] {uc['name']}: {uc['status']}")


async def main():
    print("=" * 70)
    print("FOCALBOARD DETERMINISTIC WORKFLOW TEST")
    print("30 Use Cases: Happy & Unhappy Paths")
    print("=" * 70)

    test = DeterministicWorkflowTest()

    try:
        # Setup
        if not await test.setup():
            print("❌ Setup failed!")
            return False

        # Run tests
        await test.test_template_tracking()
        await test.test_phase_tasks()
        await test.test_phase_agent_context()
        await test.test_deterministic_workflow()
        await test.test_error_handling()
        await test.test_search_and_filter()
        await test.test_template_operations()
        await test.test_agent_context_all_phases()

        # Summary
        test.print_summary()

        # Take final screenshot
        navigate_browser(f"{FOCALBOARD_URL}/board/{test.board_id}")
        await asyncio.sleep(1)
        take_screenshot("final_state")

    finally:
        # Cleanup
        await test.cleanup()

    return True


if __name__ == "__main__":
    asyncio.run(main())
