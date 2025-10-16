"""
SQLite-based symbol table for efficient symbol storage and lookup.

This module provides a comprehensive symbol table implementation with:
- Fast symbol lookup by name, type, file
- Full-text search using SQLite FTS5
- Fuzzy matching capabilities
- Batch operations for performance
- Dependency tracking
"""

import sqlite3
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, TYPE_CHECKING
from dataclasses import asdict
from difflib import SequenceMatcher

if TYPE_CHECKING:
    from semanticscout.ast_processing.ast_processor import SymbolUsage

from ..config import get_enhancement_config
from ..ast_processing import Symbol, Dependency
from ..paths import path_manager

logger = logging.getLogger(__name__)


class SymbolTable:
    """
    SQLite-based symbol table with full-text search and fuzzy matching.
    
    Provides efficient storage and retrieval of code symbols with support for:
    - Exact symbol lookup
    - Full-text search
    - Fuzzy matching
    - Batch operations
    - Dependency tracking
    """
    
    def __init__(self, db_path: Optional[Path] = None, collection_name: str = "default"):
        """
        Initialize the symbol table.

        Args:
            db_path: Path to SQLite database file. If None, uses ~/semanticscout/data/symbol_tables.
                    This parameter exists primarily for testing purposes.
            collection_name: Name of the collection (for multi-codebase support)
        """
        self.config = get_enhancement_config()

        # Determine database path
        if db_path is None:
            db_dir = path_manager.get_symbol_tables_dir()
            db_path = db_dir / f"{collection_name}.db"

        self.db_path = db_path
        self.collection_name = collection_name

        # Connect to database
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Create tables
        self._create_tables()

        logger.info(f"Initialized symbol table at {db_path}")

    def _create_tables(self):
        """Create symbol table schema with indexes and FTS."""
        self.conn.executescript("""
            -- Main symbols table
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_name TEXT NOT NULL DEFAULT 'default',
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                column_number INTEGER NOT NULL,
                end_line_number INTEGER,
                end_column_number INTEGER,
                signature TEXT,
                documentation TEXT,
                scope TEXT,
                is_exported BOOLEAN DEFAULT 0,
                parent_symbol TEXT,
                metadata TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Indexes for fast lookup
            CREATE INDEX IF NOT EXISTS idx_symbols_collection ON symbols(collection_name);
            CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
            CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path);
            CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(type);
            CREATE INDEX IF NOT EXISTS idx_symbols_exported ON symbols(is_exported);
            CREATE INDEX IF NOT EXISTS idx_symbols_parent ON symbols(parent_symbol);
            CREATE INDEX IF NOT EXISTS idx_symbols_composite ON symbols(collection_name, name, type, file_path);
            
            -- Full-text search index
            CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
                name, signature, documentation,
                content='symbols', content_rowid='id'
            );
            
            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS symbols_ai AFTER INSERT ON symbols BEGIN
                INSERT INTO symbols_fts(rowid, name, signature, documentation)
                VALUES (new.id, new.name, new.signature, new.documentation);
            END;
            
            CREATE TRIGGER IF NOT EXISTS symbols_ad AFTER DELETE ON symbols BEGIN
                INSERT INTO symbols_fts(symbols_fts, rowid, name, signature, documentation)
                VALUES('delete', old.id, old.name, old.signature, old.documentation);
            END;
            
            CREATE TRIGGER IF NOT EXISTS symbols_au AFTER UPDATE ON symbols BEGIN
                INSERT INTO symbols_fts(symbols_fts, rowid, name, signature, documentation)
                VALUES('delete', old.id, old.name, old.signature, old.documentation);
                INSERT INTO symbols_fts(rowid, name, signature, documentation)
                VALUES (new.id, new.name, new.signature, new.documentation);
            END;
            
            -- Dependencies table
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_name TEXT NOT NULL DEFAULT 'default',
                from_file TEXT NOT NULL,
                to_file TEXT NOT NULL,
                imported_symbols TEXT,  -- JSON array
                import_type TEXT NOT NULL,
                line_number INTEGER,
                is_type_only BOOLEAN DEFAULT 0,
                metadata TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Indexes for dependency queries
            CREATE INDEX IF NOT EXISTS idx_deps_collection ON dependencies(collection_name);
            CREATE INDEX IF NOT EXISTS idx_deps_from ON dependencies(from_file);
            CREATE INDEX IF NOT EXISTS idx_deps_to ON dependencies(to_file);
            CREATE INDEX IF NOT EXISTS idx_deps_composite ON dependencies(collection_name, from_file, to_file);
            
            -- File metadata table
            CREATE TABLE IF NOT EXISTS file_metadata (
                file_path TEXT NOT NULL,
                collection_name TEXT NOT NULL DEFAULT 'default',
                last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                symbol_count INTEGER DEFAULT 0,
                dependency_count INTEGER DEFAULT 0,
                file_hash TEXT,
                embedding_model TEXT,
                embedding_dimensions INTEGER,
                PRIMARY KEY (file_path, collection_name)
            );

            -- Symbol usage table for tracking where symbols are used
            CREATE TABLE IF NOT EXISTS symbol_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_name TEXT NOT NULL DEFAULT 'default',
                from_symbol TEXT NOT NULL,
                to_symbol TEXT NOT NULL,
                usage_type TEXT NOT NULL,  -- call, reference, implements, extends, type_annotation
                from_file TEXT NOT NULL,
                to_file TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                column_number INTEGER DEFAULT 0,
                metadata TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Indexes for symbol usage queries
            CREATE INDEX IF NOT EXISTS idx_usage_collection ON symbol_usage(collection_name);
            CREATE INDEX IF NOT EXISTS idx_usage_to_symbol ON symbol_usage(to_symbol);
            CREATE INDEX IF NOT EXISTS idx_usage_from_symbol ON symbol_usage(from_symbol);
            CREATE INDEX IF NOT EXISTS idx_usage_from_file ON symbol_usage(from_file);
            CREATE INDEX IF NOT EXISTS idx_usage_to_file ON symbol_usage(to_file);
            CREATE INDEX IF NOT EXISTS idx_usage_type ON symbol_usage(usage_type);
            CREATE INDEX IF NOT EXISTS idx_usage_composite ON symbol_usage(collection_name, to_symbol, usage_type);
        """)
        self.conn.commit()

    def insert_symbols(self, symbols: List[Symbol]) -> int:
        """
        Batch insert symbols.
        
        Args:
            symbols: List of Symbol objects to insert
            
        Returns:
            Number of symbols inserted
        """
        if not symbols:
            return 0
        
        try:
            symbol_data = [
                (
                    self.collection_name,
                    s.name, s.type, s.file_path, s.line_number, s.column_number,
                    s.end_line_number, s.end_column_number,
                    s.signature, s.documentation, s.scope,
                    s.is_exported, s.parent_symbol,
                    json.dumps(s.metadata) if s.metadata else None
                )
                for s in symbols
            ]

            cursor = self.conn.executemany("""
                INSERT INTO symbols
                (collection_name, name, type, file_path, line_number, column_number,
                 end_line_number, end_column_number,
                 signature, documentation, scope, is_exported, parent_symbol, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, symbol_data)

            self.conn.commit()

            logger.debug(f"Inserted {len(symbols)} symbols")
            return cursor.rowcount

        except Exception as e:
            logger.error(f"Failed to insert symbols: {e}", exc_info=True)
            self.conn.rollback()
            return 0

    def delete_symbols_by_file(self, file_path: str) -> int:
        """
        Delete all symbols for a specific file.

        Args:
            file_path: Relative file path to delete symbols for

        Returns:
            Number of symbols deleted
        """
        try:
            cursor = self.conn.execute(
                "DELETE FROM symbols WHERE file_path = ? AND collection_name = ?",
                (file_path, self.collection_name)
            )
            self.conn.commit()

            deleted_count = cursor.rowcount
            logger.debug(f"Deleted {deleted_count} symbols for file: {file_path}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete symbols for {file_path}: {e}", exc_info=True)
            self.conn.rollback()
            return 0

    def insert_dependencies(self, dependencies: List[Dependency]) -> int:
        """
        Batch insert dependencies.
        
        Args:
            dependencies: List of Dependency objects to insert
            
        Returns:
            Number of dependencies inserted
        """
        if not dependencies:
            return 0
        
        try:
            dep_data = [
                (
                    self.collection_name,
                    d.from_file, d.to_file,
                    json.dumps(d.imported_symbols) if d.imported_symbols else None,
                    d.import_type, d.line_number, d.is_type_only,
                    json.dumps(d.metadata) if d.metadata else None
                )
                for d in dependencies
            ]

            cursor = self.conn.executemany("""
                INSERT INTO dependencies
                (collection_name, from_file, to_file, imported_symbols, import_type, line_number, is_type_only, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, dep_data)

            self.conn.commit()

            logger.debug(f"Inserted {len(dependencies)} dependencies")
            return cursor.rowcount

        except Exception as e:
            logger.error(f"Failed to insert dependencies: {e}", exc_info=True)
            self.conn.rollback()
            return 0

    def insert_symbol_usage(self, symbol_usage: List['SymbolUsage']) -> int:
        """
        Batch insert symbol usage relationships.

        Args:
            symbol_usage: List of SymbolUsage objects to insert

        Returns:
            Number of symbol usage records inserted
        """
        if not symbol_usage:
            return 0

        try:
            usage_data = [
                (
                    self.collection_name,
                    u.from_symbol, u.to_symbol, u.usage_type,
                    u.from_file, u.to_file, u.line_number, u.column_number,
                    json.dumps(u.metadata) if u.metadata else None
                )
                for u in symbol_usage
            ]

            cursor = self.conn.executemany("""
                INSERT INTO symbol_usage
                (collection_name, from_symbol, to_symbol, usage_type, from_file, to_file, line_number, column_number, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, usage_data)

            self.conn.commit()

            logger.debug(f"Inserted {len(symbol_usage)} symbol usage records")
            return cursor.rowcount

        except Exception as e:
            logger.error(f"Failed to insert symbol usage: {e}", exc_info=True)
            self.conn.rollback()
            return 0

    def find_symbol_usage(self, symbol_name: str, usage_type: Optional[str] = None) -> List[Dict]:
        """
        Find where a symbol is used.

        Args:
            symbol_name: Name of the symbol to find usage for
            usage_type: Optional filter by usage type (call, reference, etc.)

        Returns:
            List of usage records as dictionaries
        """
        try:
            query = """
                SELECT from_symbol, to_symbol, usage_type, from_file, to_file,
                       line_number, column_number, metadata
                FROM symbol_usage
                WHERE collection_name = ? AND to_symbol = ?
            """
            params = [self.collection_name, symbol_name]

            if usage_type:
                query += " AND usage_type = ?"
                params.append(usage_type)

            query += " ORDER BY from_file, line_number"

            cursor = self.conn.execute(query, params)
            results = cursor.fetchall()

            return [
                {
                    'from_symbol': row[0],
                    'to_symbol': row[1],
                    'usage_type': row[2],
                    'from_file': row[3],
                    'to_file': row[4],
                    'line_number': row[5],
                    'column_number': row[6],
                    'metadata': json.loads(row[7]) if row[7] else {}
                }
                for row in results
            ]

        except Exception as e:
            logger.error(f"Failed to find symbol usage for {symbol_name}: {e}", exc_info=True)
            return []

    def find_callers_by_usage(self, symbol_name: str) -> List[Dict]:
        """
        Find all callers of a symbol using actual usage tracking.

        Args:
            symbol_name: Name of the symbol to find callers for

        Returns:
            List of caller information as dictionaries
        """
        try:
            query = """
                SELECT DISTINCT from_symbol, from_file, line_number, usage_type
                FROM symbol_usage
                WHERE collection_name = ? AND to_symbol = ? AND usage_type IN ('call', 'reference')
                ORDER BY from_file, line_number
            """

            cursor = self.conn.execute(query, [self.collection_name, symbol_name])
            results = cursor.fetchall()

            return [
                {
                    'caller': row[0],
                    'file_path': row[1],
                    'line_number': row[2],
                    'usage_type': row[3]
                }
                for row in results
            ]

        except Exception as e:
            logger.error(f"Failed to find callers for {symbol_name}: {e}", exc_info=True)
            return []

    def find_callees_by_usage(self, symbol_name: str) -> List[Dict]:
        """
        Find all symbols that a given symbol calls/uses.

        Args:
            symbol_name: Name of the symbol to find callees for

        Returns:
            List of callee information as dictionaries
        """
        try:
            query = """
                SELECT DISTINCT to_symbol, to_file, line_number, usage_type
                FROM symbol_usage
                WHERE collection_name = ? AND from_symbol = ? AND usage_type IN ('call', 'reference')
                ORDER BY to_file, line_number
            """

            cursor = self.conn.execute(query, [self.collection_name, symbol_name])
            results = cursor.fetchall()

            return [
                {
                    'callee': row[0],
                    'file_path': row[1],
                    'line_number': row[2],
                    'usage_type': row[3]
                }
                for row in results
            ]

        except Exception as e:
            logger.error(f"Failed to find callees for {symbol_name}: {e}", exc_info=True)
            return []

    def find_transitive_callers(self, symbol_name: str, max_depth: int = 3) -> List[Dict]:
        """
        Find all transitive callers (callers of callers) up to a specified depth.

        Args:
            symbol_name: Name of the symbol to find transitive callers for
            max_depth: Maximum depth to traverse (default: 3)

        Returns:
            List of transitive caller information with depth
        """
        try:
            visited = set()
            all_callers = []

            def find_callers_recursive(target_symbol: str, current_depth: int):
                if current_depth > max_depth or target_symbol in visited:
                    return

                visited.add(target_symbol)
                direct_callers = self.find_callers_by_usage(target_symbol)

                for caller in direct_callers:
                    caller_info = caller.copy()
                    caller_info['depth'] = current_depth
                    caller_info['target_symbol'] = target_symbol
                    all_callers.append(caller_info)

                    # Recursively find callers of this caller
                    find_callers_recursive(caller['caller'], current_depth + 1)

            find_callers_recursive(symbol_name, 1)

            # Sort by depth, then by file and line
            all_callers.sort(key=lambda x: (x['depth'], x['file_path'], x['line_number']))

            return all_callers

        except Exception as e:
            logger.error(f"Failed to find transitive callers for {symbol_name}: {e}", exc_info=True)
            return []

    def find_cross_file_usage(self, symbol_name: str) -> List[Dict]:
        """
        Find usage of a symbol across different files.

        Args:
            symbol_name: Name of the symbol to find cross-file usage for

        Returns:
            List of cross-file usage information
        """
        try:
            query = """
                SELECT DISTINCT from_symbol, to_symbol, usage_type, from_file, to_file,
                       line_number, column_number
                FROM symbol_usage
                WHERE collection_name = ? AND to_symbol = ? AND from_file != to_file
                ORDER BY from_file, line_number
            """

            cursor = self.conn.execute(query, [self.collection_name, symbol_name])
            results = cursor.fetchall()

            return [
                {
                    'from_symbol': row[0],
                    'to_symbol': row[1],
                    'usage_type': row[2],
                    'from_file': row[3],
                    'to_file': row[4],
                    'line_number': row[5],
                    'column_number': row[6]
                }
                for row in results
            ]

        except Exception as e:
            logger.error(f"Failed to find cross-file usage for {symbol_name}: {e}", exc_info=True)
            return []

    def get_symbol_usage_stats(self, symbol_name: str) -> Dict:
        """
        Get comprehensive usage statistics for a symbol.

        Args:
            symbol_name: Name of the symbol to get stats for

        Returns:
            Dictionary with usage statistics
        """
        try:
            # Count total usage
            cursor = self.conn.execute("""
                SELECT COUNT(*) FROM symbol_usage
                WHERE collection_name = ? AND to_symbol = ?
            """, [self.collection_name, symbol_name])
            total_usage = cursor.fetchone()[0]

            # Count by usage type
            cursor = self.conn.execute("""
                SELECT usage_type, COUNT(*) FROM symbol_usage
                WHERE collection_name = ? AND to_symbol = ?
                GROUP BY usage_type
            """, [self.collection_name, symbol_name])
            usage_by_type = dict(cursor.fetchall())

            # Count unique callers
            cursor = self.conn.execute("""
                SELECT COUNT(DISTINCT from_symbol) FROM symbol_usage
                WHERE collection_name = ? AND to_symbol = ? AND usage_type IN ('call', 'reference')
            """, [self.collection_name, symbol_name])
            unique_callers = cursor.fetchone()[0]

            # Count files using this symbol
            cursor = self.conn.execute("""
                SELECT COUNT(DISTINCT from_file) FROM symbol_usage
                WHERE collection_name = ? AND to_symbol = ?
            """, [self.collection_name, symbol_name])
            files_using = cursor.fetchone()[0]

            return {
                'symbol_name': symbol_name,
                'total_usage': total_usage,
                'usage_by_type': usage_by_type,
                'unique_callers': unique_callers,
                'files_using': files_using
            }

        except Exception as e:
            logger.error(f"Failed to get usage stats for {symbol_name}: {e}", exc_info=True)
            return {}

    def find_unused_symbols(self) -> List[Dict]:
        """
        Find symbols that are defined but never used.

        Returns:
            List of unused symbol information
        """
        try:
            query = """
                SELECT s.name, s.type, s.file_path, s.line_number
                FROM symbols s
                LEFT JOIN symbol_usage u ON s.name = u.to_symbol AND s.collection_name = u.collection_name
                WHERE s.collection_name = ? AND u.to_symbol IS NULL
                ORDER BY s.file_path, s.line_number
            """

            cursor = self.conn.execute(query, [self.collection_name])
            results = cursor.fetchall()

            return [
                {
                    'name': row[0],
                    'type': row[1],
                    'file_path': row[2],
                    'line_number': row[3]
                }
                for row in results
            ]

        except Exception as e:
            logger.error(f"Failed to find unused symbols: {e}", exc_info=True)
            return []

    def lookup_symbol(self, name: str, symbol_type: Optional[str] = None,
                     file_path: Optional[str] = None) -> List[Dict]:
        """
        Find symbols by exact name match.
        
        Args:
            name: Symbol name to search for
            symbol_type: Optional symbol type filter (function, class, etc.)
            file_path: Optional file path filter
            
        Returns:
            List of matching symbols as dictionaries
        """
        query = "SELECT * FROM symbols WHERE collection_name = ? AND name = ?"
        params = [self.collection_name, name]

        if symbol_type:
            query += " AND type = ?"
            params.append(symbol_type)

        if file_path:
            query += " AND file_path = ?"
            params.append(file_path)

        query += " ORDER BY file_path, line_number"

        try:
            cursor = self.conn.execute(query, params)
            results = [self._row_to_dict(row) for row in cursor.fetchall()]
            logger.debug(f"Found {len(results)} symbols for name '{name}'")
            return results
        except Exception as e:
            logger.error(f"Failed to lookup symbol: {e}")
            return []

    @lru_cache(maxsize=1000)
    def lookup_symbol_cached(self, name: str, symbol_type: Optional[str] = None,
                            file_path: Optional[str] = None) -> tuple:
        """
        Cached version of lookup_symbol for frequently accessed symbols.

        Args:
            name: Symbol name to search for
            symbol_type: Optional symbol type filter (function, class, etc.)
            file_path: Optional file path filter

        Returns:
            Tuple of matching symbols (immutable for caching)

        Note:
            Returns tuple instead of list for cache compatibility.
            Convert to list if needed: list(result)
        """
        results = self.lookup_symbol(name, symbol_type, file_path)
        # Convert to tuple of tuples for immutability (required for caching)
        return tuple(tuple(r.items()) for r in results)

    def clear_lookup_cache(self):
        """Clear the lookup cache. Call after bulk inserts/updates."""
        self.lookup_symbol_cached.cache_clear()
        logger.debug("Symbol lookup cache cleared")

    def search_symbols(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Full-text search for symbols.
        
        Args:
            query: Search query (FTS5 syntax supported)
            limit: Maximum number of results
            
        Returns:
            List of matching symbols ordered by relevance
        """
        try:
            cursor = self.conn.execute("""
                SELECT s.*, rank FROM symbols s
                JOIN symbols_fts fts ON s.id = fts.rowid
                WHERE symbols_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, [query, limit])
            
            results = [self._row_to_dict(row) for row in cursor.fetchall()]
            logger.debug(f"FTS search for '{query}' returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Failed to search symbols: {e}")
            return []

    def fuzzy_search(self, query: str, threshold: float = 0.6, limit: int = 20) -> List[Dict]:
        """
        Fuzzy search for symbols using similarity matching.

        Args:
            query: Search query
            threshold: Similarity threshold (0.0 to 1.0)
            limit: Maximum number of results

        Returns:
            List of matching symbols with similarity scores
        """
        if not self.config.symbol_table.fuzzy_matching:
            logger.warning("Fuzzy matching is disabled in configuration")
            return []

        try:
            # Get all symbol names (could be optimized with a cache)
            cursor = self.conn.execute("SELECT DISTINCT name FROM symbols")
            all_names = [row[0] for row in cursor.fetchall()]

            # Calculate similarity scores
            matches = []
            query_lower = query.lower()

            for name in all_names:
                name_lower = name.lower()

                # Calculate similarity using SequenceMatcher
                similarity = SequenceMatcher(None, query_lower, name_lower).ratio()

                # Also check if query is a substring (boost score)
                if query_lower in name_lower:
                    similarity = max(similarity, 0.8)

                if similarity >= threshold:
                    matches.append((name, similarity))

            # Sort by similarity (descending)
            matches.sort(key=lambda x: x[1], reverse=True)
            matches = matches[:limit]

            # Get full symbol data for matches
            results = []
            for name, similarity in matches:
                symbols = self.lookup_symbol(name)
                for symbol in symbols:
                    symbol['similarity_score'] = similarity
                    results.append(symbol)

            logger.debug(f"Fuzzy search for '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Failed to fuzzy search: {e}")
            return []

    def get_symbols_by_file(self, file_path: str) -> List[Dict]:
        """
        Get all symbols in a specific file.

        Args:
            file_path: Path to the file

        Returns:
            List of symbols in the file
        """
        try:
            cursor = self.conn.execute("""
                SELECT * FROM symbols
                WHERE file_path = ?
                ORDER BY line_number
            """, [file_path])

            results = [self._row_to_dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            logger.error(f"Failed to get symbols by file: {e}")
            return []

    def get_exported_symbols(self, file_path: Optional[str] = None) -> List[Dict]:
        """
        Get all exported symbols, optionally filtered by file.

        Args:
            file_path: Optional file path filter

        Returns:
            List of exported symbols
        """
        try:
            if file_path:
                cursor = self.conn.execute("""
                    SELECT * FROM symbols
                    WHERE is_exported = 1 AND file_path = ?
                    ORDER BY name
                """, [file_path])
            else:
                cursor = self.conn.execute("""
                    SELECT * FROM symbols
                    WHERE is_exported = 1
                    ORDER BY file_path, name
                """)

            results = [self._row_to_dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            logger.error(f"Failed to get exported symbols: {e}")
            return []

    def get_dependencies(self, file_path: str, direction: str = "from") -> List[Dict]:
        """
        Get dependencies for a file.

        Args:
            file_path: Path to the file
            direction: "from" for imports, "to" for files that import this file

        Returns:
            List of dependencies
        """
        try:
            if direction == "from":
                cursor = self.conn.execute("""
                    SELECT * FROM dependencies
                    WHERE from_file = ?
                    ORDER BY line_number
                """, [file_path])
            else:
                cursor = self.conn.execute("""
                    SELECT * FROM dependencies
                    WHERE to_file = ?
                """, [file_path])

            results = []
            for row in cursor.fetchall():
                dep = dict(row)
                # Parse JSON fields
                if dep['imported_symbols']:
                    dep['imported_symbols'] = json.loads(dep['imported_symbols'])
                if dep['metadata']:
                    dep['metadata'] = json.loads(dep['metadata'])
                results.append(dep)

            return results
        except Exception as e:
            logger.error(f"Failed to get dependencies: {e}")
            return []

    def find_callers(self, symbol_name: str, max_results: int = 10) -> List[Dict]:
        """
        Find all functions/methods that potentially call a specific symbol.

        This is a heuristic implementation that finds functions/methods in the same
        file(s) as the target symbol. It does NOT perform actual call graph analysis,
        so it may return false positives (functions that don't actually call the symbol).

        For proper call graph analysis, symbol-level dependencies would need to be
        tracked during AST processing and stored in the dependency graph.

        Args:
            symbol_name: Name of the symbol to find callers for
            max_results: Maximum number of callers to return (default: 10)

        Returns:
            List of symbol dictionaries representing potential callers

        Note:
            This implementation uses a file-based heuristic and may include functions
            that don't actually call the target symbol. Future enhancements should
            implement proper call graph analysis.
        """
        try:
            # First, find the target symbol to get its file path(s)
            target_symbols = self.lookup_symbol(symbol_name)

            if not target_symbols:
                logger.debug(f"Symbol '{symbol_name}' not found")
                return []

            # Get unique file paths where the symbol is defined
            file_paths = list(set(s['file_path'] for s in target_symbols))
            logger.debug(f"Found symbol '{symbol_name}' in {len(file_paths)} file(s)")

            # Find all functions/methods in the same file(s)
            # Use placeholders for the IN clause
            placeholders = ','.join('?' * len(file_paths))
            query = f"""
                SELECT * FROM symbols
                WHERE collection_name = ?
                AND type IN ('function', 'method')
                AND file_path IN ({placeholders})
                AND name != ?
                ORDER BY file_path, line_number
                LIMIT ?
            """

            params = [self.collection_name] + file_paths + [symbol_name, max_results]
            cursor = self.conn.execute(query, params)

            results = [self._row_to_dict(row) for row in cursor.fetchall()]
            logger.debug(f"Found {len(results)} potential callers for '{symbol_name}'")
            return results

        except Exception as e:
            logger.error(f"Failed to find callers for '{symbol_name}': {e}", exc_info=True)
            return []

    def delete_file_symbols(self, file_path: str) -> int:
        """
        Delete all symbols and dependencies for a file.

        Args:
            file_path: Path to the file

        Returns:
            Number of symbols deleted
        """
        try:
            # Delete symbols
            cursor = self.conn.execute("DELETE FROM symbols WHERE file_path = ?", [file_path])
            symbol_count = cursor.rowcount

            # Delete dependencies
            self.conn.execute("DELETE FROM dependencies WHERE from_file = ?", [file_path])

            # Delete file metadata
            self.conn.execute("DELETE FROM file_metadata WHERE file_path = ?", [file_path])

            self.conn.commit()

            logger.debug(f"Deleted {symbol_count} symbols for {file_path}")
            return symbol_count

        except Exception as e:
            logger.error(f"Failed to delete file symbols: {e}")
            self.conn.rollback()
            return 0

    def update_file_metadata(
        self,
        file_path: str,
        file_hash: Optional[str] = None,
        symbol_count: Optional[int] = None,
        dependency_count: Optional[int] = None,
        embedding_model: Optional[str] = None,
        embedding_dimensions: Optional[int] = None,
    ) -> None:
        """
        Update or insert file metadata.

        Args:
            file_path: Path to the file
            file_hash: Content hash of the file
            symbol_count: Number of symbols in the file
            dependency_count: Number of dependencies in the file
            embedding_model: Name of the embedding model used
            embedding_dimensions: Dimension of embeddings
        """
        try:
            # Use UPSERT (INSERT OR REPLACE)
            self.conn.execute("""
                INSERT INTO file_metadata (
                    file_path, collection_name, last_indexed, symbol_count, dependency_count,
                    file_hash, embedding_model, embedding_dimensions
                )
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path, collection_name) DO UPDATE SET
                    last_indexed = CURRENT_TIMESTAMP,
                    symbol_count = COALESCE(excluded.symbol_count, symbol_count),
                    dependency_count = COALESCE(excluded.dependency_count, dependency_count),
                    file_hash = COALESCE(excluded.file_hash, file_hash),
                    embedding_model = COALESCE(excluded.embedding_model, embedding_model),
                    embedding_dimensions = COALESCE(excluded.embedding_dimensions, embedding_dimensions)
            """, (file_path, self.collection_name, symbol_count, dependency_count, file_hash, embedding_model, embedding_dimensions))
            self.conn.commit()
            logger.debug(f"Updated file metadata for {file_path}")
        except Exception as e:
            logger.error(f"Failed to update file metadata: {e}")
            self.conn.rollback()

    def get_file_metadata(self, file_path: str) -> Optional[Dict]:
        """
        Get metadata for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file metadata or None if not found
        """
        try:
            cursor = self.conn.execute("""
                SELECT * FROM file_metadata WHERE file_path = ? AND collection_name = ?
            """, (file_path, self.collection_name))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None

    def get_files_by_model(
        self, embedding_model: Optional[str] = None, embedding_dimensions: Optional[int] = None
    ) -> List[Dict]:
        """
        Get files indexed with a specific embedding model or dimension.

        Args:
            embedding_model: Filter by embedding model name (optional)
            embedding_dimensions: Filter by embedding dimensions (optional)

        Returns:
            List of file metadata dictionaries
        """
        try:
            query = "SELECT * FROM file_metadata WHERE 1=1"
            params = []

            if embedding_model is not None:
                query += " AND embedding_model = ?"
                params.append(embedding_model)

            if embedding_dimensions is not None:
                query += " AND embedding_dimensions = ?"
                params.append(embedding_dimensions)

            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get files by model: {e}")
            return []

    def get_statistics(self) -> Dict:
        """
        Get symbol table statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            stats = {}

            # Total symbols
            cursor = self.conn.execute("SELECT COUNT(*) FROM symbols WHERE collection_name = ?", (self.collection_name,))
            stats['total_symbols'] = cursor.fetchone()[0]

            # Symbols by type
            cursor = self.conn.execute("""
                SELECT type, COUNT(*) as count
                FROM symbols
                WHERE collection_name = ?
                GROUP BY type
            """, (self.collection_name,))
            stats['symbols_by_type'] = {row[0]: row[1] for row in cursor.fetchall()}

            # Total dependencies
            cursor = self.conn.execute("SELECT COUNT(*) FROM dependencies WHERE collection_name = ?", (self.collection_name,))
            stats['total_dependencies'] = cursor.fetchone()[0]

            # Total files
            cursor = self.conn.execute("SELECT COUNT(DISTINCT file_path) FROM symbols WHERE collection_name = ?", (self.collection_name,))
            stats['total_files'] = cursor.fetchone()[0]

            # Exported symbols
            cursor = self.conn.execute("SELECT COUNT(*) FROM symbols WHERE collection_name = ? AND is_exported = 1", (self.collection_name,))
            stats['exported_symbols'] = cursor.fetchone()[0]

            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def clear(self) -> None:
        """Clear all data from the symbol table."""
        try:
            self.conn.execute("DELETE FROM symbols")
            self.conn.execute("DELETE FROM dependencies")
            self.conn.execute("DELETE FROM file_metadata")
            self.conn.commit()
            logger.info("Cleared symbol table")
        except Exception as e:
            logger.error(f"Failed to clear symbol table: {e}")
            self.conn.rollback()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert a database row to a dictionary."""
        result = dict(row)

        # Parse JSON fields
        if 'metadata' in result and result['metadata']:
            try:
                result['metadata'] = json.loads(result['metadata'])
            except:
                result['metadata'] = {}

        return result

    def close(self):
        """Close the database connection."""
        try:
            self.conn.close()
            logger.debug("Closed symbol table connection")
        except Exception as e:
            logger.error(f"Failed to close connection: {e}")

    def __del__(self):
        """Cleanup on deletion."""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass


class SymbolTableManager:
    """
    Manager for multiple symbol tables (multi-codebase support).
    """

    def __init__(self):
        """Initialize the symbol table manager."""
        self.tables: Dict[str, SymbolTable] = {}

    def get_table(self, collection_name: str) -> SymbolTable:
        """
        Get or create a symbol table for a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            SymbolTable instance
        """
        if collection_name not in self.tables:
            self.tables[collection_name] = SymbolTable(collection_name=collection_name)

        return self.tables[collection_name]

    def close_all(self):
        """Close all symbol tables."""
        for table in self.tables.values():
            table.close()
        self.tables.clear()

    def __del__(self):
        """Cleanup on deletion."""
        self.close_all()
