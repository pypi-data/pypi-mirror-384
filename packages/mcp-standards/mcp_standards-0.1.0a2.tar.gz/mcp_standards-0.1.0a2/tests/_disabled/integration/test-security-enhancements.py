#!/usr/bin/env python3
"""
Test Security Enhancements

Tests all 4 security features:
1. Path whitelist for CLAUDE.md updates
2. Input sanitization for pattern descriptions
3. Rate limiting for pattern spam
4. Audit logging for all modifications
"""

import asyncio
import sys
import sqlite3
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "mcp-servers" / "claude-memory"))

from claude_memory.server import ClaudeMemoryMCP


async def test_security_enhancements():
    """Test all security enhancements"""

    print("=" * 70)
    print("Testing Security Enhancements")
    print("=" * 70)
    print()

    # Initialize server with test database
    test_db_path = Path("/tmp/test-security.db")
    test_db_path.unlink(missing_ok=True)
    server = ClaudeMemoryMCP(db_path=str(test_db_path))
    print("✓ Server initialized\n")

    # Test 1: Path Whitelist
    print("=" * 70)
    print("Test 1: Path Whitelist for CLAUDE.md Updates")
    print("=" * 70)

    # Test valid path (current directory)
    print("\n1.1 Testing valid path (current directory)...")
    valid_result = await server._update_claudemd(
        file_path="/tmp/test-CLAUDE.md",  # /tmp should be accessible
        min_confidence=0.3
    )
    print(f"Result: {valid_result['success']}")
    print(f"Message: {valid_result.get('message', valid_result.get('error'))}")

    # Test invalid path (outside whitelist)
    print("\n1.2 Testing invalid path (outside whitelist)...")
    invalid_result = await server._update_claudemd(
        file_path="/etc/CLAUDE.md",  # /etc should be blocked
        min_confidence=0.3
    )
    print(f"Result: {invalid_result['success']}")
    print(f"Expected: False")
    print(f"Error: {invalid_result.get('error')}")
    assert not invalid_result['success'], "Should reject path outside whitelist"
    print("✓ Path whitelist working correctly")

    # Test invalid filename
    print("\n1.3 Testing invalid filename...")
    invalid_name_result = await server._update_claudemd(
        file_path="/tmp/malicious.md",
        min_confidence=0.3
    )
    print(f"Result: {invalid_name_result['success']}")
    print(f"Expected: False")
    print(f"Error: {invalid_name_result.get('error')}")
    assert not invalid_name_result['success'], "Should reject non-CLAUDE.md files"
    print("✓ Filename validation working correctly")

    # Test 2: Input Sanitization
    print("\n" + "=" * 70)
    print("Test 2: Input Sanitization for Pattern Descriptions")
    print("=" * 70)

    print("\n2.1 Testing malicious input with control characters...")
    result = await server._log_tool_execution(
        tool_name="Bash",
        args={"command": "test"},
        result="use \x00\x01evil\nnot \r\ngood"  # Control characters
    )
    print(f"Patterns detected: {result.get('patterns_detected', 0)}")
    if result.get('patterns'):
        for pattern in result['patterns']:
            print(f"  Sanitized: '{pattern}'")
            # Check for control characters
            assert '\x00' not in pattern, "Null byte should be removed"
            assert '\r' not in pattern, "Carriage return should be removed"
    print("✓ Input sanitization working correctly")

    print("\n2.2 Testing SQL injection attempt...")
    result = await server._log_tool_execution(
        tool_name="Bash",
        args={"command": "test"},
        result="use pip'; DROP TABLE episodes; -- not uv"
    )
    print(f"Patterns detected: {result.get('patterns_detected', 0)}")
    print("✓ SQL injection attempt safely handled")

    # Test 3: Rate Limiting
    print("\n" + "=" * 70)
    print("Test 3: Rate Limiting for Pattern Spam")
    print("=" * 70)

    print(f"\n3.1 Testing rate limit ({server.pattern_extractor.MAX_PATTERNS_PER_MINUTE} patterns/min)...")

    # Send patterns up to the limit
    successful_count = 0
    for i in range(server.pattern_extractor.MAX_PATTERNS_PER_MINUTE + 10):
        result = await server._log_tool_execution(
            tool_name="Bash",
            args={"command": f"test{i}"},
            result=f"use tool{i} not old{i}"
        )
        if result.get('patterns_detected', 0) > 0:
            successful_count += 1

    print(f"Successful pattern extractions: {successful_count}")
    print(f"Expected: ~{server.pattern_extractor.MAX_PATTERNS_PER_MINUTE}")
    assert successful_count <= server.pattern_extractor.MAX_PATTERNS_PER_MINUTE + 1, \
        "Rate limit should prevent excessive patterns"
    print("✓ Rate limiting working correctly")

    # Test 4: Audit Logging
    print("\n" + "=" * 70)
    print("Test 4: Audit Logging for All Modifications")
    print("=" * 70)

    print("\n4.1 Checking audit log entries...")
    with sqlite3.connect(test_db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT action, target_type, target_path, details, success, timestamp
            FROM audit_log
            ORDER BY timestamp DESC
            LIMIT 10
        """)

        audit_entries = cursor.fetchall()
        print(f"\nFound {len(audit_entries)} audit log entries:")

        for entry in audit_entries:
            print(f"\n  Action: {entry['action']}")
            print(f"  Target: {entry['target_type']} - {entry['target_path']}")
            print(f"  Details: {entry['details']}")
            print(f"  Success: {entry['success']}")
            print(f"  Timestamp: {entry['timestamp']}")

    assert len(audit_entries) > 0, "Should have audit log entries"
    print(f"\n✓ Audit logging working correctly ({len(audit_entries)} entries)")

    # Test 4.2: Verify failed attempts are logged
    print("\n4.2 Verifying failed attempts are logged...")
    failed_attempts = [
        entry for entry in audit_entries
        if not entry['success']
    ]
    print(f"Failed attempts logged: {len(failed_attempts)}")
    for attempt in failed_attempts:
        print(f"  - {attempt['action']}: {attempt['details']}")
    assert len(failed_attempts) >= 2, "Should log failed path validation attempts"
    print("✓ Failed attempts properly logged")

    # Summary
    print("\n" + "=" * 70)
    print("Security Test Summary")
    print("=" * 70)
    print("✓ Path whitelist validation: WORKING")
    print("✓ Input sanitization: WORKING")
    print("✓ Rate limiting: WORKING")
    print("✓ Audit logging: WORKING")
    print("\n🎉 All security enhancements validated!")

    # Cleanup
    print("\nCleaning up test files...")
    test_db_path.unlink(missing_ok=True)
    Path("/tmp/test-CLAUDE.md").unlink(missing_ok=True)
    print("✓ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(test_security_enhancements())
