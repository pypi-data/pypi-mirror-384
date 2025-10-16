"""Basic smoke tests for MCP Standards"""
import pytest
import sys
from pathlib import Path


def test_python_version():
    """Verify Python version is 3.10+"""
    assert sys.version_info >= (3, 10), "Python 3.10+ required"


def test_import_mcp_standards():
    """Verify main package can be imported"""
    try:
        import mcp_standards
        assert mcp_standards.__version__ == "0.1.0"
    except ImportError:
        pytest.skip("Package not installed in editable mode")


def test_src_structure():
    """Verify source directory structure exists"""
    src_dir = Path(__file__).parent.parent / "src" / "mcp_standards"
    assert src_dir.exists(), "src/mcp_standards directory should exist"
    assert (src_dir / "__init__.py").exists(), "__init__.py should exist"


def test_pyproject_exists():
    """Verify pyproject.toml exists"""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml should exist"


def test_readme_exists():
    """Verify README.md exists"""
    readme = Path(__file__).parent.parent / "README.md"
    assert readme.exists(), "README.md should exist"


def test_license_exists():
    """Verify LICENSE exists"""
    license_file = Path(__file__).parent.parent / "LICENSE"
    assert license_file.exists(), "LICENSE should exist"


@pytest.mark.parametrize("doc_file", [
    "README.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "docs/guides/QUICKSTART.md",
    "docs/guides/SECURITY.md",
    "docs/technical/ARCHITECTURE.md",
])
def test_documentation_files(doc_file):
    """Verify documentation files exist"""
    doc_path = Path(__file__).parent.parent / doc_file
    assert doc_path.exists(), f"{doc_file} should exist"
