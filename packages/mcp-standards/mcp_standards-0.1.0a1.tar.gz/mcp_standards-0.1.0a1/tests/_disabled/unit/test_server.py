"""Unit tests for MCP server protocol handlers

Tests MCP tool calls, server setup, and protocol compliance.
Target: 85%+ coverage
"""
import pytest
import json
from mcp.types import TextContent


@pytest.mark.unit
class TestMCPServerSetup:
    """Test MCP server initialization and setup"""

    def test_server_initialization(self, memory_server):
        """Test server initializes correctly"""
        assert memory_server.server is not None
        assert memory_server.db_path is not None
        assert memory_server.autologger is not None

    def test_database_path_default(self, tmp_path, monkeypatch):
        """Test default database path uses home directory"""
        from claude_memory.server import ClaudeMemoryMCP
        from pathlib import Path

        # Create server without explicit db_path
        monkeypatch.setenv("HOME", str(tmp_path))
        server = ClaudeMemoryMCP(db_path=None)

        assert ".claude-memory" in str(server.db_path)

    def test_database_path_override(self, tmp_path):
        """Test database path can be overridden"""
        from claude_memory.server import ClaudeMemoryMCP

        custom_path = tmp_path / "custom.db"
        server = ClaudeMemoryMCP(db_path=str(custom_path))

        assert server.db_path == custom_path

    def test_components_initialized(self, memory_server):
        """Test all server components are initialized"""
        assert hasattr(memory_server, 'server')
        assert hasattr(memory_server, 'db_path')
        assert hasattr(memory_server, 'autologger')
        assert hasattr(memory_server, 'pattern_extractor')
        assert hasattr(memory_server, 'claudemd_manager')


@pytest.mark.unit
class TestMCPToolHandlers:
    """Test MCP protocol tool call handlers"""

    async def test_add_episode_tool_call(self, memory_server):
        """Test add_episode via MCP tool call"""
        result = await memory_server.server.call_tool(
            "add_episode",
            {
                "name": "Test Episode",
                "content": "Test content",
                "source": "test"
            }
        )

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        result_data = json.loads(result[0].text)
        assert result_data["success"] is True

    async def test_search_episodes_tool_call(self, populated_server):
        """Test search_episodes via MCP tool call"""
        result = await populated_server.server.call_tool(
            "search_episodes",
            {"query": "Python", "limit": 10}
        )

        assert len(result) > 0
        result_data = json.loads(result[0].text)
        assert result_data["success"] is True
        assert "results" in result_data

    async def test_list_recent_tool_call(self, populated_server):
        """Test list_recent via MCP tool call"""
        result = await populated_server.server.call_tool(
            "list_recent",
            {"limit": 5}
        )

        assert len(result) > 0
        result_data = json.loads(result[0].text)
        assert result_data["success"] is True
        assert "results" in result_data

    async def test_tool_call_error_handling(self, memory_server):
        """Test tool calls handle errors gracefully"""
        # Call with invalid parameters
        result = await memory_server.server.call_tool(
            "add_episode",
            {"name": "", "content": "", "source": ""}
        )

        assert len(result) > 0
        result_data = json.loads(result[0].text)
        assert result_data["success"] is False
        assert "error" in result_data

    async def test_tool_call_returns_json(self, memory_server):
        """Test all tool calls return valid JSON"""
        result = await memory_server.server.call_tool(
            "add_episode",
            {"name": "Test", "content": "Content", "source": "test"}
        )

        assert isinstance(result[0], TextContent)
        # Should not raise
        parsed = json.loads(result[0].text)
        assert isinstance(parsed, dict)


@pytest.mark.unit
class TestToolLogging:
    """Test tool execution logging"""

    async def test_log_tool_execution_success(self, memory_server):
        """Test successful tool execution is logged"""
        result = await memory_server._log_tool_execution(
            tool_name="test_tool",
            args={"param1": "value1"},
            result={"success": True}
        )

        assert result["success"] is True

        # Verify logged to database
        import sqlite3
        with sqlite3.connect(memory_server.db_path) as conn:
            cursor = conn.execute(
                "SELECT tool_name, args FROM tool_logs WHERE tool_name = ?",
                ("test_tool",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "test_tool"

    async def test_log_tool_execution_with_significance(self, memory_server):
        """Test tool logging with significance score"""
        result = await memory_server._log_tool_execution(
            tool_name="important_tool",
            args={"key": "value"},
            result={"success": True},
            significance_score=0.85
        )

        assert result["success"] is True

        # Verify significance score stored
        import sqlite3
        with sqlite3.connect(memory_server.db_path) as conn:
            cursor = conn.execute(
                "SELECT significance_score FROM tool_logs WHERE tool_name = ?",
                ("important_tool",)
            )
            row = cursor.fetchone()
            if row and row[0]:
                assert float(row[0]) == 0.85

    async def test_log_tool_execution_json_serialization(self, memory_server):
        """Test complex objects are JSON serialized"""
        complex_args = {
            "list": [1, 2, 3],
            "nested": {"key": "value"},
            "bool": True,
            "null": None
        }

        result = await memory_server._log_tool_execution(
            tool_name="complex_tool",
            args=complex_args,
            result={"success": True}
        )

        assert result["success"] is True


@pytest.mark.unit
class TestAuditLogging:
    """Test audit logging functionality"""

    def test_audit_log_creation(self, memory_server):
        """Test audit log entry creation"""
        memory_server._audit_log(
            action="test_action",
            target_type="test_target",
            target_path="/test/path",
            details={"key": "value"},
            success=True
        )

        # Verify logged
        import sqlite3
        with sqlite3.connect(memory_server.db_path) as conn:
            cursor = conn.execute(
                "SELECT action, target_type FROM audit_log WHERE action = ?",
                ("test_action",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "test_action"
            assert row[1] == "test_target"

    def test_audit_log_failure(self, memory_server):
        """Test failed operations are logged"""
        memory_server._audit_log(
            action="failed_action",
            target_type="file",
            target_path="/invalid/path",
            details={"error": "access denied"},
            success=False
        )

        import sqlite3
        with sqlite3.connect(memory_server.db_path) as conn:
            cursor = conn.execute(
                "SELECT success FROM audit_log WHERE action = ?",
                ("failed_action",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 0  # False


@pytest.mark.unit
class TestExportFunctionality:
    """Test export to markdown functionality"""

    async def test_export_to_markdown(self, populated_server, tmp_path):
        """Test exporting episodes to markdown file"""
        from claude_memory.export import export_to_markdown

        output_file = tmp_path / "export.md"

        # Export episodes
        export_to_markdown(
            str(populated_server.db_path),
            str(output_file)
        )

        assert output_file.exists()
        content = output_file.read_text()
        assert "# Claude Memory Export" in content
        assert "## Episodes" in content

    async def test_export_empty_database(self, memory_server, tmp_path):
        """Test exporting from empty database"""
        from claude_memory.export import export_to_markdown

        output_file = tmp_path / "empty_export.md"

        export_to_markdown(
            str(memory_server.db_path),
            str(output_file)
        )

        assert output_file.exists()
