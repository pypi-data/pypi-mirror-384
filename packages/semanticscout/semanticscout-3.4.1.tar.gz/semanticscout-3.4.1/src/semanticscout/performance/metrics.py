"""
Performance metrics collection and monitoring.

This module provides utilities for tracking and reporting performance metrics
across the SemanticScout system.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    
    # Timing metrics (in seconds)
    total_time: float = 0.0
    ast_parsing_time: float = 0.0
    symbol_extraction_time: float = 0.0
    dependency_extraction_time: float = 0.0
    embedding_generation_time: float = 0.0
    vector_store_time: float = 0.0
    query_time: float = 0.0
    
    # Count metrics
    files_processed: int = 0
    symbols_extracted: int = 0
    dependencies_tracked: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    # Memory metrics (in MB)
    peak_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    
    # Operation counts
    operation_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    operation_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    
    def add_operation(self, operation: str, duration: float):
        """
        Record an operation and its duration.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
        """
        self.operation_counts[operation] += 1
        self.operation_times[operation].append(duration)
    
    def get_avg_operation_time(self, operation: str) -> float:
        """
        Get average time for an operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Average time in seconds, or 0.0 if no operations recorded
        """
        times = self.operation_times.get(operation, [])
        return sum(times) / len(times) if times else 0.0
    
    def get_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate.
        
        Returns:
            Cache hit rate as a percentage (0-100)
        """
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            'timing': {
                'total_time': self.total_time,
                'ast_parsing_time': self.ast_parsing_time,
                'symbol_extraction_time': self.symbol_extraction_time,
                'dependency_extraction_time': self.dependency_extraction_time,
                'embedding_generation_time': self.embedding_generation_time,
                'vector_store_time': self.vector_store_time,
                'query_time': self.query_time,
            },
            'counts': {
                'files_processed': self.files_processed,
                'symbols_extracted': self.symbols_extracted,
                'dependencies_tracked': self.dependencies_tracked,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
            },
            'memory': {
                'peak_memory_mb': self.peak_memory_mb,
                'avg_memory_mb': self.avg_memory_mb,
            },
            'cache_hit_rate': self.get_cache_hit_rate(),
            'operations': {
                op: {
                    'count': self.operation_counts[op],
                    'avg_time': self.get_avg_operation_time(op),
                    'total_time': sum(self.operation_times[op]),
                }
                for op in self.operation_counts.keys()
            }
        }
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        lines = [
            "Performance Metrics:",
            f"  Total Time: {self.total_time:.2f}s",
            f"  Files Processed: {self.files_processed}",
            f"  Symbols Extracted: {self.symbols_extracted}",
            f"  Dependencies Tracked: {self.dependencies_tracked}",
            f"  Cache Hit Rate: {self.get_cache_hit_rate():.1f}%",
            f"  Peak Memory: {self.peak_memory_mb:.1f}MB",
        ]
        
        if self.operation_counts:
            lines.append("  Operations:")
            for op, count in self.operation_counts.items():
                avg_time = self.get_avg_operation_time(op)
                lines.append(f"    {op}: {count} ops, {avg_time*1000:.2f}ms avg")
        
        return "\n".join(lines)


class PerformanceMonitor:
    """
    Performance monitoring context manager and utility.
    
    Tracks timing, memory usage, and operation counts.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.metrics = PerformanceMetrics()
        self._start_time: Optional[float] = None
        self._operation_stack: List[tuple] = []
    
    def start(self):
        """Start monitoring."""
        self._start_time = time.time()
    
    def stop(self):
        """Stop monitoring and finalize metrics."""
        if self._start_time:
            self.metrics.total_time = time.time() - self._start_time
            self._start_time = None
    
    @contextmanager
    def measure(self, operation: str):
        """
        Context manager for measuring operation duration.
        
        Args:
            operation: Name of the operation to measure
            
        Example:
            with monitor.measure("ast_parsing"):
                # ... do work ...
                pass
        """
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.metrics.add_operation(operation, duration)
    
    def record_cache_hit(self):
        """Record a cache hit."""
        self.metrics.cache_hits += 1
    
    def record_cache_miss(self):
        """Record a cache miss."""
        self.metrics.cache_misses += 1
    
    def record_file_processed(self):
        """Record a file being processed."""
        self.metrics.files_processed += 1
    
    def record_symbols_extracted(self, count: int):
        """Record symbols extracted."""
        self.metrics.symbols_extracted += count
    
    def record_dependencies_tracked(self, count: int):
        """Record dependencies tracked."""
        self.metrics.dependencies_tracked += count
    
    def update_memory_usage(self, memory_mb: float):
        """
        Update memory usage metrics.
        
        Args:
            memory_mb: Current memory usage in MB
        """
        if memory_mb > self.metrics.peak_memory_mb:
            self.metrics.peak_memory_mb = memory_mb
        
        # Update running average
        if self.metrics.avg_memory_mb == 0:
            self.metrics.avg_memory_mb = memory_mb
        else:
            # Simple moving average
            self.metrics.avg_memory_mb = (self.metrics.avg_memory_mb + memory_mb) / 2
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get current metrics."""
        return self.metrics
    
    def reset(self):
        """Reset all metrics."""
        self.metrics = PerformanceMetrics()
        self._start_time = None
        self._operation_stack = []
    
    def log_summary(self):
        """Log a summary of performance metrics."""
        logger.info(f"\n{self.metrics}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False

