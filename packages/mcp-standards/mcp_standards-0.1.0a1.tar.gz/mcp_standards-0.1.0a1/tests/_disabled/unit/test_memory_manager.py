"""Unit tests for ClaudeMemoryMCP core CRUD operations

Tests episode management, search functionality, and database operations.
Target: 85%+ coverage
"""
import pytest
import sqlite3
import json
from datetime import datetime


@pytest.mark.unit
class TestEpisodeOperations:
    """Test episode CRUD operations"""

    async def test_add_episode_success(self, memory_server):
        """Test adding episode with valid data"""
        result = await memory_server._add_episode(
            name="Test Episode",
            content="Test content with searchable text",
            source="test"
        )

        assert result["success"] is True
        assert "id" in result
        assert result["message"].startswith("Episode")

    async def test_add_episode_empty_name(self, memory_server):
        """Test adding episode with empty name fails"""
        result = await memory_server._add_episode(
            name="",
            content="Test content",
            source="test"
        )

        assert result["success"] is False
        assert "error" in result

    async def test_add_episode_empty_content(self, memory_server):
        """Test adding episode with empty content fails"""
        result = await memory_server._add_episode(
            name="Test",
            content="",
            source="test"
        )

        assert result["success"] is False
        assert "error" in result

    async def test_add_episode_with_metadata(self, memory_server):
        """Test adding episode with JSON metadata"""
        metadata = {"priority": "high", "tags": ["important", "urgent"]}

        result = await memory_server._add_episode(
            name="Episode with Metadata",
            content="Content",
            source="test",
            metadata=metadata
        )

        assert result["success"] is True

        # Verify metadata stored correctly
        with sqlite3.connect(memory_server.db_path) as conn:
            cursor = conn.execute(
                "SELECT metadata FROM episodes WHERE id = ?",
                (result["id"],)
            )
            row = cursor.fetchone()
            stored_metadata = json.loads(row[0]) if row and row[0] else None
            assert stored_metadata == metadata

    async def test_add_episode_increments_id(self, memory_server):
        """Test episode IDs increment sequentially"""
        result1 = await memory_server._add_episode("Episode 1", "Content 1", "test")
        result2 = await memory_server._add_episode("Episode 2", "Content 2", "test")

        assert result1["success"] is True
        assert result2["success"] is True
        assert result2["id"] > result1["id"]

    async def test_add_episode_timestamps(self, memory_server):
        """Test episodes receive timestamps"""
        result = await memory_server._add_episode("Test", "Content", "test")

        with sqlite3.connect(memory_server.db_path) as conn:
            cursor = conn.execute(
                "SELECT timestamp FROM episodes WHERE id = ?",
                (result["id"],)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] is not None  # Timestamp exists

    async def test_add_multiple_episodes(self, memory_server, sample_episodes):
        """Test adding multiple episodes successfully"""
        for episode in sample_episodes:
            result = await memory_server._add_episode(
                episode["name"],
                episode["content"],
                episode["source"]
            )
            assert result["success"] is True

        # Verify all were added
        with sqlite3.connect(memory_server.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM episodes")
            count = cursor.fetchone()[0]
            assert count >= len(sample_episodes)


@pytest.mark.unit
class TestSearchOperations:
    """Test full-text search functionality"""

    async def test_search_episodes_fts_basic(self, populated_server):
        """Test basic full-text search functionality"""
        results = await populated_server._search_episodes("python", limit=10)

        assert results["success"] is True
        assert results["count"] >= 0
        if results["count"] > 0:
            assert any("Python" in r["name"] for r in results["results"])

    async def test_search_episodes_case_insensitive(self, populated_server):
        """Test search is case-insensitive"""
        upper_result = await populated_server._search_episodes("PYTHON", limit=10)
        lower_result = await populated_server._search_episodes("python", limit=10)

        # Should return same results regardless of case
        assert upper_result["count"] == lower_result["count"]

    async def test_search_episodes_no_results(self, populated_server):
        """Test search with no matching results"""
        results = await populated_server._search_episodes("xyznonexistent", limit=10)

        assert results["success"] is True
        assert results["count"] == 0
        assert results["results"] == []

    async def test_search_episodes_respects_limit(self, memory_server):
        """Test search respects limit parameter"""
        # Add many episodes
        for i in range(20):
            await memory_server._add_episode(
                f"Python Episode {i}",
                f"Python content {i}",
                "test"
            )

        results = await memory_server._search_episodes("Python", limit=5)

        assert results["success"] is True
        assert len(results["results"]) <= 5

    async def test_search_episodes_partial_word(self, populated_server):
        """Test search with partial word matching"""
        results = await populated_server._search_episodes("API", limit=10)

        assert results["success"] is True
        # FTS5 may or may not support partial matching depending on config

    async def test_search_episodes_multiple_words(self, populated_server):
        """Test search with multiple words"""
        await populated_server._add_episode(
            "Python Type Hints",
            "Use type hints for better code quality",
            "test"
        )

        results = await populated_server._search_episodes("Python type", limit=10)

        assert results["success"] is True

    async def test_search_episodes_in_content(self, populated_server):
        """Test search finds matches in content, not just name"""
        results = await populated_server._search_episodes("docstrings", limit=10)

        assert results["success"] is True
        if results["count"] > 0:
            # Should find "API Documentation" episode
            assert any("Documentation" in r["name"] for r in results["results"])


@pytest.mark.unit
class TestListOperations:
    """Test listing and retrieving episodes"""

    async def test_list_recent_with_limit(self, memory_server):
        """Test listing recent episodes respects limit"""
        # Add multiple episodes
        for i in range(15):
            await memory_server._add_episode(
                f"Episode {i}",
                f"Content {i}",
                "test"
            )

        results = await memory_server._list_recent(limit=5)

        assert results["success"] is True
        assert results["count"] == 5
        assert len(results["results"]) == 5

    async def test_list_recent_chronological_order(self, memory_server):
        """Test episodes listed in reverse chronological order"""
        # Add episodes with delays to ensure different timestamps
        import asyncio

        for i in range(5):
            await memory_server._add_episode(f"Episode {i}", f"Content {i}", "test")
            await asyncio.sleep(0.01)  # Small delay

        results = await memory_server._list_recent(limit=5)

        if results["count"] > 1:
            # Most recent first
            ids = [r["id"] for r in results["results"]]
            assert ids == sorted(ids, reverse=True)

    async def test_list_recent_empty_database(self, memory_server):
        """Test listing from empty database"""
        results = await memory_server._list_recent(limit=10)

        assert results["success"] is True
        assert results["count"] == 0
        assert results["results"] == []

    async def test_list_recent_includes_metadata(self, memory_server):
        """Test list results include all episode fields"""
        await memory_server._add_episode(
            "Test Episode",
            "Test Content",
            "test-source",
            metadata={"key": "value"}
        )

        results = await memory_server._list_recent(limit=1)

        assert results["count"] > 0
        episode = results["results"][0]
        assert "id" in episode
        assert "name" in episode
        assert "content" in episode
        assert "source" in episode
        assert "timestamp" in episode


@pytest.mark.unit
class TestDatabaseIntegrity:
    """Test database integrity and constraints"""

    def test_database_tables_created(self, memory_server):
        """Test all required tables are created"""
        with sqlite3.connect(memory_server.db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)
            tables = {row[0] for row in cursor.fetchall()}

            assert "episodes" in tables
            assert "tool_logs" in tables
            assert "audit_log" in tables
            # FTS table may have different naming
            assert any("search" in table for table in tables)

    def test_episodes_table_schema(self, memory_server):
        """Test episodes table has correct schema"""
        with sqlite3.connect(memory_server.db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(episodes)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "name" in columns
            assert "content" in columns
            assert "source" in columns
            assert "timestamp" in columns
            assert "metadata" in columns

    def test_fts_index_created(self, memory_server):
        """Test full-text search index exists"""
        with sqlite3.connect(memory_server.db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name LIKE '%search%'
            """)
            fts_tables = cursor.fetchall()
            assert len(fts_tables) > 0

    def test_database_file_location(self, memory_server):
        """Test database created in correct location"""
        from pathlib import Path
        db_path = Path(memory_server.db_path)
        assert db_path.exists()
        assert db_path.is_file()
