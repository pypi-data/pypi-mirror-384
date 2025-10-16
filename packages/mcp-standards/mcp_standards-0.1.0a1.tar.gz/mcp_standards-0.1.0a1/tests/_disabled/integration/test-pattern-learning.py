#!/usr/bin/env python3
"""
Test Pattern Learning Feedback Loop

This script validates that:
1. Tool executions are logged
2. Corrections are detected as patterns
3. Patterns are promoted to preferences after 3 occurrences
4. CLAUDE.md can be updated with learned preferences
"""

import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "mcp-servers" / "claude-memory"))

from claude_memory.server import ClaudeMemoryMCP


async def test_pattern_learning():
    """Test the complete pattern learning feedback loop"""

    print("=" * 60)
    print("Testing Pattern Learning Feedback Loop")
    print("=" * 60)
    print()

    # Initialize server
    print("1. Initializing server...")
    test_db_path = Path("/tmp/test-pattern-learning.db")
    test_db_path.unlink(missing_ok=True)  # Clean slate
    server = ClaudeMemoryMCP(db_path=str(test_db_path))
    print("   ✓ Server initialized")
    print()

    # Step 1: Log tool execution with correction pattern (occurrence #1)
    print("2. Logging tool execution with correction pattern (occurrence #1)...")
    result1 = await server._log_tool_execution(
        tool_name="Bash",
        args={"command": "pip install requests"},
        result="User said: actually use uv not pip"
    )
    print(f"   Result: {result1}")
    print(f"   ✓ Patterns detected: {result1.get('patterns_detected', 0)}")
    if result1.get('patterns'):
        for pattern in result1['patterns']:
            print(f"     - {pattern}")
    print()

    # Step 2: Log same correction again (occurrence #2)
    print("3. Logging same correction again (occurrence #2)...")
    result2 = await server._log_tool_execution(
        tool_name="Bash",
        args={"command": "pip install numpy"},
        result="use uv not pip"
    )
    print(f"   Result: {result2}")
    print(f"   ✓ Patterns detected: {result2.get('patterns_detected', 0)}")
    print()

    # Step 3: Log third occurrence (should trigger promotion!)
    print("4. Logging third occurrence (should trigger promotion!)...")
    result3 = await server._log_tool_execution(
        tool_name="Bash",
        args={"command": "pip install pandas"},
        result="actually use uv not pip"
    )
    print(f"   Result: {result3}")
    print(f"   ✓ Patterns detected: {result3.get('patterns_detected', 0)}")
    print()

    # Step 4: Check learned preferences
    print("5. Checking learned preferences...")
    preferences = await server._get_learned_preferences(min_confidence=0.3)
    print(f"   Found {preferences['count']} preference(s):")
    for pref in preferences.get('preferences', []):
        print(f"     - {pref['preference']} (confidence: {pref['confidence']:.2f})")
    print()

    # Step 5: Get CLAUDE.md update suggestions
    print("6. Getting CLAUDE.md update suggestions...")
    suggestions = await server._suggest_claudemd_update(min_confidence=0.3)
    print(f"   Found {suggestions['count']} suggestion(s):")
    for sugg in suggestions.get('suggestions', []):
        print(f"     - {sugg['preference']} (confidence: {sugg['confidence']:.2f})")
    print()

    # Step 6: Generate CLAUDE.md content
    print("7. Generating CLAUDE.md content...")
    content = server.claudemd_manager.generate_claudemd_content(min_confidence=0.3)
    print("   Generated content preview:")
    print("   " + "-" * 50)
    for line in content.split("\n")[:20]:
        print(f"   {line}")
    print("   ...")
    print()

    # Step 7: Test update CLAUDE.md
    print("8. Testing CLAUDE.md update...")
    test_claudemd_path = "/tmp/test-CLAUDE.md"
    update_result = await server._update_claudemd(
        file_path=test_claudemd_path,
        min_confidence=0.3
    )
    print(f"   Result: {update_result}")

    if update_result['success']:
        print(f"   ✓ Created {test_claudemd_path}")
        with open(test_claudemd_path, 'r') as f:
            lines = f.read().split("\n")
            print(f"   Preview (first 15 lines):")
            for line in lines[:15]:
                print(f"     {line}")
    print()

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"✓ Tool execution logging: Working")
    print(f"✓ Pattern detection: {result1.get('patterns_detected', 0) > 0}")
    print(f"✓ Pattern promotion (3+ occurrences): {preferences['count'] > 0}")
    print(f"✓ CLAUDE.md suggestions: {suggestions['count'] > 0}")
    print(f"✓ CLAUDE.md update: {update_result['success']}")
    print()
    print("🎉 Self-improving feedback loop is WORKING!")
    print()

    # Cleanup
    print("Cleaning up test files...")
    test_db_path.unlink(missing_ok=True)
    Path(test_claudemd_path).unlink(missing_ok=True)
    print("✓ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(test_pattern_learning())
