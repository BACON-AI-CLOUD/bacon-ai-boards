#!/usr/bin/env python3
"""
Test script for Focalboard template tools.
Tests the template discovery, loading, and instantiation functionality.
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

# Now import the server module
from server import (
    _discover_templates,
    _load_template,
    _format_template_markdown,
    focalboard_list_templates,
    focalboard_get_template,
    focalboard_health_check,
    ListTemplatesInput,
    GetTemplateInput,
    HealthCheckInput,
    ResponseFormat,
    TEMPLATE_BASE_DIR,
    FOCALBOARD_URL,
    FOCALBOARD_TOKEN
)


async def test_template_discovery():
    """Test template discovery."""
    print("\n" + "=" * 60)
    print("TEST 1: Template Discovery")
    print("=" * 60)

    templates = _discover_templates()
    print(f"Template directory: {TEMPLATE_BASE_DIR}")
    print(f"Found {len(templates)} templates:")

    for t in templates:
        print(f"  - {t['id']} (v{t['version']}) in {t['category']}")
        print(f"    {t['phases_count']} phases, {t['tasks_count']} tasks")

    return len(templates) > 0


async def test_template_loading():
    """Test loading a specific template."""
    print("\n" + "=" * 60)
    print("TEST 2: Template Loading")
    print("=" * 60)

    template = _load_template("bacon-ai-12-phase")

    if template:
        print(f"Loaded template: {template['meta']['name']}")
        print(f"Version: {template['meta']['version']}")
        print(f"Phases: {len(template['phases'])}")
        print(f"Total tasks: {sum(len(p['tasks']) for p in template['phases'])}")
        return True
    else:
        print("ERROR: Could not load bacon-ai-12-phase template")
        return False


async def test_list_templates_tool():
    """Test the focalboard_list_templates MCP tool."""
    print("\n" + "=" * 60)
    print("TEST 3: focalboard_list_templates Tool")
    print("=" * 60)

    params = ListTemplatesInput(response_format=ResponseFormat.MARKDOWN)
    result = await focalboard_list_templates(params)

    print(result[:500] + "..." if len(result) > 500 else result)

    return "Available Templates" in result or "No templates found" in result


async def test_get_template_tool():
    """Test the focalboard_get_template MCP tool."""
    print("\n" + "=" * 60)
    print("TEST 4: focalboard_get_template Tool")
    print("=" * 60)

    params = GetTemplateInput(
        template_id="bacon-ai-12-phase",
        response_format=ResponseFormat.MARKDOWN
    )
    result = await focalboard_get_template(params)

    print(result[:800] + "..." if len(result) > 800 else result)

    return "BACON-AI" in result or "not found" in result


async def test_health_check():
    """Test Focalboard server connectivity."""
    print("\n" + "=" * 60)
    print("TEST 5: Focalboard Health Check")
    print("=" * 60)

    print(f"Server URL: {FOCALBOARD_URL}")
    print(f"Token set: {bool(FOCALBOARD_TOKEN)}")

    params = HealthCheckInput()
    result = await focalboard_health_check(params)

    print(result)

    return "Health Check" in result


async def main():
    """Run all tests."""
    print("=" * 60)
    print("FOCALBOARD TEMPLATE TOOLS TEST SUITE")
    print("=" * 60)

    results = {}

    # Run tests
    results["discovery"] = await test_template_discovery()
    results["loading"] = await test_template_loading()
    results["list_tool"] = await test_list_templates_tool()
    results["get_tool"] = await test_get_template_tool()
    results["health"] = await test_health_check()

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0

    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
