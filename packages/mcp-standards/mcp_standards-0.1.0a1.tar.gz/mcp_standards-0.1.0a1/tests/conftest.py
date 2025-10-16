"""Shared pytest fixtures for mcp-standards tests"""
import pytest
import sqlite3
from pathlib import Path
from typing import Generator
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_standards.server import main


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Directory for test data files"""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Temporary database for tests"""
    db_path = tmp_path / "test_knowledge.db"
    return db_path


@pytest.fixture
def mock_project(tmp_path: Path) -> Path:
    """Mock project structure with config files"""
    project = tmp_path / "test_project"
    project.mkdir()

    # Create .editorconfig
    editorconfig = project / ".editorconfig"
    editorconfig.write_text("""root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true
""")

    # Create pyproject.toml
    pyproject = project / "pyproject.toml"
    pyproject.write_text("""[project]
name = "test-project"
version = "1.0.0"

[tool.black]
line-length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
""")

    # Create package.json
    package_json = project / "package.json"
    package_json.write_text("""{
  "name": "test-project",
  "version": "1.0.0",
  "scripts": {
    "test": "jest",
    "lint": "eslint ."
  }
}
""")

    return project


@pytest.fixture
def db_connection(temp_db: Path) -> Generator[sqlite3.Connection, None, None]:
    """Direct database connection for testing"""
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def sample_episodes() -> list[dict]:
    """Sample episode data for testing"""
    return [
        {
            "name": "Python Type Hints",
            "content": "Always use type hints for function parameters and return values",
            "source": "coding-standards"
        },
        {
            "name": "API Documentation",
            "content": "Document all public APIs with docstrings following Google style",
            "source": "documentation"
        },
        {
            "name": "Error Handling",
            "content": "Use specific exception types, avoid bare except clauses",
            "source": "best-practices"
        },
        {
            "name": "Database Migrations",
            "content": "Always create reversible database migrations with down methods",
            "source": "database"
        },
        {
            "name": "Security Headers",
            "content": "Set security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options",
            "source": "security"
        }
    ]


@pytest.fixture
def malicious_inputs() -> dict[str, str]:
    """Collection of malicious inputs for security testing"""
    return {
        "sql_injection": "'; DROP TABLE episodes; --",
        "path_traversal": "../../etc/passwd",
        "path_traversal_windows": "..\\..\\windows\\system32\\config",
        "xss": "<script>alert('XSS')</script>",
        "command_injection": "; rm -rf /",
        "null_byte": "test\x00.txt",
        "unicode_exploit": "\u202e\u202dtxt.exe",
        "long_input": "A" * 100000
    }


@pytest.fixture
def claude_md_content() -> str:
    """Sample CLAUDE.md content for testing"""
    return """# Project Coding Standards

## Code Style
- Use 2 spaces for indentation
- Maximum line length: 88
- Use single quotes for strings

## Testing
- Minimum coverage: 80%
- Use pytest for testing
- Write tests before implementation

## Documentation
- Document all public APIs
- Use Google-style docstrings
"""
