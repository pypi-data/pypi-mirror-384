"""
Symbol Table module for SemanticScout enhancements.

This module provides SQLite-based symbol storage and lookup with
full-text search and fuzzy matching capabilities.
"""

from .symbol_table import SymbolTable, SymbolTableManager

__all__ = [
    "SymbolTable",
    "SymbolTableManager",
]
