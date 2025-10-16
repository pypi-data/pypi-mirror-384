"""
AST caching system for improved performance.

This module provides disk-based caching of parsed AST results using diskcache
with LZ4 compression for efficient storage.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional
import diskcache
import lz4.frame
import msgpack

from ..config import get_enhancement_config
from ..paths import path_manager

logger = logging.getLogger(__name__)


class ASTCache:
    """
    Disk-based cache for AST parse results.
    
    Uses diskcache for persistent storage with LZ4 compression
    to minimize disk usage while maintaining fast access.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the AST cache.

        Args:
            cache_dir: Directory for cache storage. If None, uses ~/semanticscout/data/ast_cache.
                      This parameter exists primarily for testing purposes.
        """
        self.config = get_enhancement_config()

        # Determine cache directory
        if cache_dir is None:
            cache_dir = path_manager.get_ast_cache_dir()

        # Directory is already created by path_manager, but ensure it exists for custom paths
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize diskcache
        cache_size_mb = self.config.performance.cache_size_mb
        self.cache = diskcache.Cache(
            str(cache_dir),
            size_limit=cache_size_mb * 1024 * 1024,  # Convert MB to bytes
            eviction_policy='least-recently-used'
        )

        # Cache TTL in seconds
        self.ttl = self.config.ast_processing.cache_ttl_hours * 3600

        logger.info(f"Initialized AST cache at {cache_dir} with {cache_size_mb}MB limit")
    
    def get(self, file_path: Path, content: str, model_name: Optional[str] = None) -> Optional['ParseResult']:
        """
        Get cached parse result if available and valid.

        Args:
            file_path: Path to the file
            content: Current file content
            model_name: Optional embedding model name for cache key

        Returns:
            ParseResult if cached and valid, None otherwise
        """
        try:
            # Generate cache key from file path and content hash
            cache_key = self._generate_cache_key(file_path, content, model_name)

            # Try to get from cache
            cached_data = self.cache.get(cache_key)
            if cached_data is None:
                return None
            
            # Decompress and deserialize
            decompressed = lz4.frame.decompress(cached_data)
            result_dict = msgpack.unpackb(decompressed, raw=False)
            
            # Reconstruct ParseResult
            from .ast_processor import ParseResult, Symbol, Dependency, SymbolUsage

            symbols = [Symbol(**s) for s in result_dict['symbols']]
            dependencies = [Dependency(**d) for d in result_dict['dependencies']]
            symbol_usage = [SymbolUsage(**u) for u in result_dict['symbol_usage']]

            result = ParseResult(
                file_path=result_dict['file_path'],
                symbols=symbols,
                dependencies=dependencies,
                symbol_usage=symbol_usage,
                success=result_dict['success'],
                error=result_dict.get('error'),
                parse_time_ms=result_dict.get('parse_time_ms', 0.0),
                metadata=result_dict.get('metadata', {})
            )
            
            logger.debug(f"Cache hit for {file_path}")
            return result
            
        except Exception as e:
            logger.warning(f"Failed to get cached result for {file_path}: {e}")
            return None
    
    def set(self, file_path: Path, content: str, result: 'ParseResult', model_name: Optional[str] = None) -> None:
        """
        Cache a parse result.

        Args:
            file_path: Path to the file
            content: File content
            result: ParseResult to cache
            model_name: Optional embedding model name for cache key
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(file_path, content, model_name)
            
            # Convert ParseResult to dict
            result_dict = {
                'file_path': result.file_path,
                'symbols': [self._symbol_to_dict(s) for s in result.symbols],
                'dependencies': [self._dependency_to_dict(d) for d in result.dependencies],
                'symbol_usage': [self._symbol_usage_to_dict(u) for u in getattr(result, 'symbol_usage', [])],
                'success': result.success,
                'error': result.error,
                'parse_time_ms': result.parse_time_ms,
                'metadata': result.metadata
            }
            
            # Serialize and compress
            serialized = msgpack.packb(result_dict, use_bin_type=True)
            compressed = lz4.frame.compress(serialized)
            
            # Store in cache with TTL
            self.cache.set(cache_key, compressed, expire=self.ttl)
            
            logger.debug(f"Cached result for {file_path} (compressed size: {len(compressed)} bytes)")
            
        except Exception as e:
            logger.warning(f"Failed to cache result for {file_path}: {e}")

    def get_with_model(self, file_path: Path, content: str, model_name: str) -> Optional['ParseResult']:
        """
        Get cached parse result with explicit model name.

        This is a convenience method that ensures model-specific caching.

        Args:
            file_path: Path to the file
            content: Current file content
            model_name: Embedding model name

        Returns:
            ParseResult if cached and valid, None otherwise
        """
        return self.get(file_path, content, model_name=model_name)

    def set_with_model(self, file_path: Path, content: str, result: 'ParseResult', model_name: str) -> None:
        """
        Cache a parse result with explicit model name.

        This is a convenience method that ensures model-specific caching.

        Args:
            file_path: Path to the file
            content: File content
            result: ParseResult to cache
            model_name: Embedding model name
        """
        self.set(file_path, content, result, model_name=model_name)

    def clear(self) -> None:
        """Clear all cached data."""
        try:
            self.cache.clear()
            logger.info("Cleared AST cache")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            stats_tuple = self.cache.stats(enable=True)
            return {
                'size': len(self.cache),
                'volume': self.cache.volume(),
                'hits': stats_tuple[0] if stats_tuple else 0,
                'misses': stats_tuple[1] if stats_tuple else 0,
            }
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {}
    
    def _generate_cache_key(self, file_path: Path, content: str, model_name: Optional[str] = None) -> str:
        """
        Generate a cache key from file path, content, and optionally model name.

        Args:
            file_path: Path to the file
            content: File content
            model_name: Optional embedding model name

        Returns:
            Cache key string
        """
        # Hash the content
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

        # Include model name in cache key if provided
        if model_name:
            # Hash the model name to keep key length reasonable
            model_hash = hashlib.md5(model_name.encode('utf-8')).hexdigest()[:8]
            cache_key = f"{file_path}:{content_hash}:{model_hash}"
        else:
            # Backward compatibility: no model name in key
            cache_key = f"{file_path}:{content_hash}"

        return cache_key
    
    def _symbol_to_dict(self, symbol: 'Symbol') -> dict:
        """Convert Symbol to dictionary for serialization."""
        return {
            'name': symbol.name,
            'type': symbol.type,
            'file_path': symbol.file_path,
            'line_number': symbol.line_number,
            'column_number': symbol.column_number,
            'end_line_number': symbol.end_line_number,
            'end_column_number': symbol.end_column_number,
            'signature': symbol.signature,
            'documentation': symbol.documentation,
            'scope': symbol.scope,
            'is_exported': symbol.is_exported,
            'parent_symbol': symbol.parent_symbol,
            'metadata': symbol.metadata
        }
    
    def _dependency_to_dict(self, dependency: 'Dependency') -> dict:
        """Convert Dependency to dictionary for serialization."""
        return {
            'from_file': dependency.from_file,
            'to_file': dependency.to_file,
            'imported_symbols': dependency.imported_symbols,
            'import_type': dependency.import_type,
            'line_number': dependency.line_number,
            'is_type_only': dependency.is_type_only,
            'metadata': dependency.metadata
        }

    def _symbol_usage_to_dict(self, symbol_usage: 'SymbolUsage') -> dict:
        """Convert SymbolUsage to dictionary for serialization."""
        return {
            'from_symbol': symbol_usage.from_symbol,
            'to_symbol': symbol_usage.to_symbol,
            'usage_type': symbol_usage.usage_type,
            'from_file': symbol_usage.from_file,
            'to_file': symbol_usage.to_file,
            'line_number': symbol_usage.line_number,
            'column_number': symbol_usage.column_number,
            'metadata': symbol_usage.metadata
        }

    def _symbol_usage_to_dict(self, usage: 'SymbolUsage') -> dict:
        """Convert SymbolUsage to dictionary for serialization."""
        return {
            'from_symbol': usage.from_symbol,
            'to_symbol': usage.to_symbol,
            'usage_type': usage.usage_type,
            'from_file': usage.from_file,
            'to_file': usage.to_file,
            'line_number': usage.line_number,
            'column_number': usage.column_number,
            'metadata': usage.metadata
        }

    def __del__(self):
        """Clean up cache connection."""
        try:
            if hasattr(self, 'cache'):
                self.cache.close()
        except Exception:
            pass
