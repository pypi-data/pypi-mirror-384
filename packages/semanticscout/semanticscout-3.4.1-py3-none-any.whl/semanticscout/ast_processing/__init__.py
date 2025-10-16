"""
AST Processing module for SemanticScout enhancements.

This module provides enhanced AST parsing capabilities for extracting
symbols, dependencies, and structural information from code files.
"""

from .ast_processor import ASTProcessor, Symbol, Dependency, ParseResult
from .ast_cache import ASTCache

__all__ = [
    "ASTProcessor",
    "Symbol",
    "Dependency",
    "ParseResult",
    "ASTCache",
]
