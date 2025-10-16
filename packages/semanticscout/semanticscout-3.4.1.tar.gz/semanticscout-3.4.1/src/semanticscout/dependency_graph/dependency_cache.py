"""
Dependency cache for avoiding redundant import analysis.
"""

import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Metrics for dependency cache."""
    total_lookups: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    invalidations: int = 0
    entries_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_lookups == 0:
            return 0.0
        return self.cache_hits / self.total_lookups


@dataclass
class CacheEntry:
    """Cache entry for file dependencies."""
    file_path: str
    content_hash: str
    imports: List[str]
    exports: List[str]
    dependencies: Set[str]
    timestamp: float
    
    def is_valid(self, current_hash: str) -> bool:
        """Check if cache entry is still valid."""
        return self.content_hash == current_hash


class DependencyCache:
    """
    Cache for file dependency analysis results.
    
    Avoids re-analyzing unchanged files by caching import/export information
    and dependency relationships.
    """
    
    def __init__(self, max_entries: int = 10000):
        """
        Initialize dependency cache.
        
        Args:
            max_entries: Maximum number of cache entries (LRU eviction)
        """
        self.max_entries = max_entries
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # For LRU eviction
        self.metrics = CacheMetrics()
        
        # Reverse index: dependency -> files that depend on it
        self.reverse_deps: Dict[str, Set[str]] = defaultdict(set)
    
    def get(
        self,
        file_path: str,
        content_hash: str,
    ) -> Optional[CacheEntry]:
        """
        Get cached dependency information for a file.
        
        Args:
            file_path: Path to the file
            content_hash: MD5 hash of file content
            
        Returns:
            CacheEntry if valid cache hit, None otherwise
        """
        self.metrics.total_lookups += 1
        
        if file_path not in self.cache:
            self.metrics.cache_misses += 1
            logger.debug(f"Cache miss: {file_path}")
            return None
        
        entry = self.cache[file_path]
        
        # Validate cache entry
        if not entry.is_valid(content_hash):
            # Content changed - invalidate
            self.invalidate(file_path)
            self.metrics.cache_misses += 1
            logger.debug(f"Cache invalidated (content changed): {file_path}")
            return None
        
        # Cache hit!
        self.metrics.cache_hits += 1
        self._update_access(file_path)
        logger.debug(f"Cache hit: {file_path}")
        return entry
    
    def put(
        self,
        file_path: str,
        content_hash: str,
        imports: List[str],
        exports: List[str],
        dependencies: Set[str],
        timestamp: float,
    ):
        """
        Store dependency information in cache.
        
        Args:
            file_path: Path to the file
            content_hash: MD5 hash of file content
            imports: List of imported symbols
            exports: List of exported symbols
            dependencies: Set of file paths this file depends on
            timestamp: Timestamp of analysis
        """
        # Create cache entry
        entry = CacheEntry(
            file_path=file_path,
            content_hash=content_hash,
            imports=imports,
            exports=exports,
            dependencies=dependencies,
            timestamp=timestamp,
        )
        
        # Evict if at capacity
        if len(self.cache) >= self.max_entries and file_path not in self.cache:
            self._evict_lru()
        
        # Store entry
        self.cache[file_path] = entry
        self._update_access(file_path)
        
        # Update reverse dependencies
        for dep in dependencies:
            self.reverse_deps[dep].add(file_path)
        
        self.metrics.entries_count = len(self.cache)
        logger.debug(f"Cached dependencies for: {file_path}")
    
    def invalidate(self, file_path: str):
        """
        Invalidate cache entry for a file.
        
        Args:
            file_path: Path to the file
        """
        if file_path not in self.cache:
            return
        
        entry = self.cache[file_path]
        
        # Remove from reverse dependencies
        for dep in entry.dependencies:
            if dep in self.reverse_deps:
                self.reverse_deps[dep].discard(file_path)
                if not self.reverse_deps[dep]:
                    del self.reverse_deps[dep]
        
        # Remove entry
        del self.cache[file_path]
        if file_path in self.access_order:
            self.access_order.remove(file_path)
        
        self.metrics.invalidations += 1
        self.metrics.entries_count = len(self.cache)
        logger.debug(f"Invalidated cache for: {file_path}")
    
    def invalidate_dependents(self, file_path: str):
        """
        Invalidate all files that depend on the given file.
        
        When a file changes, all files that import from it need to be re-analyzed.
        
        Args:
            file_path: Path to the changed file
        """
        if file_path not in self.reverse_deps:
            return
        
        dependents = list(self.reverse_deps[file_path])
        for dependent in dependents:
            self.invalidate(dependent)
            logger.debug(f"Invalidated dependent: {dependent}")
    
    def invalidate_cascade(self, file_path: str):
        """
        Invalidate file and all its dependents recursively.
        
        Args:
            file_path: Path to the changed file
        """
        # Invalidate the file itself
        self.invalidate(file_path)
        
        # Invalidate all dependents (which may trigger more invalidations)
        self.invalidate_dependents(file_path)
    
    def _update_access(self, file_path: str):
        """Update access order for LRU eviction."""
        if file_path in self.access_order:
            self.access_order.remove(file_path)
        self.access_order.append(file_path)
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.access_order:
            return
        
        lru_file = self.access_order[0]
        self.invalidate(lru_file)
        logger.debug(f"Evicted LRU entry: {lru_file}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics."""
        return {
            "total_lookups": self.metrics.total_lookups,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "hit_rate": self.metrics.hit_rate,
            "invalidations": self.metrics.invalidations,
            "entries_count": self.metrics.entries_count,
            "max_entries": self.max_entries,
            "utilization": self.metrics.entries_count / self.max_entries,
        }
    
    def clear(self):
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        self.access_order.clear()
        self.reverse_deps.clear()
        self.metrics = CacheMetrics()
        logger.info(f"Cleared {count} cache entries")
    
    @staticmethod
    def compute_content_hash(content: str) -> str:
        """
        Compute MD5 hash of file content.
        
        Args:
            content: File content
            
        Returns:
            MD5 hash as hex string
        """
        return hashlib.md5(content.encode()).hexdigest()


class CachedDependencyAnalyzer:
    """
    Wrapper around dependency analyzer that uses caching.
    """
    
    def __init__(self, dependency_analyzer, cache: Optional[DependencyCache] = None):
        """
        Initialize cached dependency analyzer.
        
        Args:
            dependency_analyzer: Underlying dependency analyzer
            cache: Dependency cache (creates new if None)
        """
        self.analyzer = dependency_analyzer
        self.cache = cache or DependencyCache()
    
    def analyze_file(
        self,
        file_path: Path,
        content: str,
    ) -> Dict[str, Any]:
        """
        Analyze file dependencies with caching.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            Dictionary with imports, exports, and dependencies
        """
        import time
        
        # Compute content hash
        content_hash = DependencyCache.compute_content_hash(content)
        file_path_str = str(file_path)
        
        # Check cache
        cached = self.cache.get(file_path_str, content_hash)
        if cached:
            return {
                "imports": cached.imports,
                "exports": cached.exports,
                "dependencies": cached.dependencies,
                "from_cache": True,
            }
        
        # Cache miss - analyze file
        result = self.analyzer.analyze_file(file_path, content)
        
        # Store in cache
        self.cache.put(
            file_path=file_path_str,
            content_hash=content_hash,
            imports=result.get("imports", []),
            exports=result.get("exports", []),
            dependencies=set(result.get("dependencies", [])),
            timestamp=time.time(),
        )
        
        result["from_cache"] = False
        return result
    
    def invalidate_file(self, file_path: Path):
        """
        Invalidate cache for a file and its dependents.
        
        Args:
            file_path: Path to the file
        """
        self.cache.invalidate_cascade(str(file_path))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics."""
        return self.cache.get_metrics()

