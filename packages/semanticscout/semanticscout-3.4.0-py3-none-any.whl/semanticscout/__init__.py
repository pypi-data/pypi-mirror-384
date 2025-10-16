"""
SemanticScout - A context engine MCP server for AI agents.

This package provides tools for indexing codebases and retrieving relevant code
using semantic search, exposed through the Model Context Protocol (MCP).
"""

import tomllib
from pathlib import Path


def _get_version() -> str:
    """Read version from pyproject.toml."""
    try:
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
                return pyproject.get("project", {}).get("version", "unknown")
    except Exception:
        pass
    return "unknown"


__version__ = _get_version()


