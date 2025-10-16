"""
Dependency Graph module for SemanticScout enhancements.

This module provides NetworkX-based dependency graph construction and analysis
for tracking file-level and symbol-level dependencies.
"""

from .dependency_graph import DependencyGraph, DependencyGraphManager

__all__ = [
    "DependencyGraph",
    "DependencyGraphManager",
]
