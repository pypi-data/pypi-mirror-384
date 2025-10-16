"""
Dependency analysis module for SemanticScout.

This module provides language-aware dependency analysis routing and strategies.
"""

from .dependency_router import DependencyAnalysisRouter
from .strategies import DependencyAnalysisStrategy

__all__ = ["DependencyAnalysisRouter", "DependencyAnalysisStrategy"]
