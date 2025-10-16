"""
Memory monitoring and optimization utilities.

This module provides tools for tracking memory usage and optimizing memory consumption.
"""

import gc
import logging
import psutil
import os
from typing import Optional

logger = logging.getLogger(__name__)


class MemoryMonitor:
    """
    Monitor memory usage of the current process.
    
    Uses psutil to track memory consumption and provide optimization suggestions.
    """
    
    def __init__(self):
        """Initialize the memory monitor."""
        self.process = psutil.Process(os.getpid())
        self._baseline_mb: Optional[float] = None
    
    def get_current_usage_mb(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Current memory usage in megabytes
        """
        mem_info = self.process.memory_info()
        return mem_info.rss / (1024 * 1024)  # Convert bytes to MB
    
    def get_current_usage_percent(self) -> float:
        """
        Get current memory usage as percentage of total system memory.
        
        Returns:
            Memory usage percentage (0-100)
        """
        return self.process.memory_percent()
    
    def set_baseline(self):
        """Set the current memory usage as baseline for delta calculations."""
        self._baseline_mb = self.get_current_usage_mb()
        logger.debug(f"Memory baseline set to {self._baseline_mb:.1f}MB")
    
    def get_delta_mb(self) -> float:
        """
        Get memory usage delta from baseline.
        
        Returns:
            Memory increase in MB since baseline was set, or current usage if no baseline
        """
        current = self.get_current_usage_mb()
        if self._baseline_mb is None:
            return current
        return current - self._baseline_mb
    
    def check_threshold(self, threshold_mb: float) -> bool:
        """
        Check if memory usage exceeds threshold.
        
        Args:
            threshold_mb: Memory threshold in MB
            
        Returns:
            True if current usage exceeds threshold
        """
        current = self.get_current_usage_mb()
        if current > threshold_mb:
            logger.warning(
                f"Memory usage ({current:.1f}MB) exceeds threshold ({threshold_mb}MB)"
            )
            return True
        return False
    
    def log_usage(self, context: str = ""):
        """
        Log current memory usage.
        
        Args:
            context: Optional context string to include in log message
        """
        current_mb = self.get_current_usage_mb()
        percent = self.get_current_usage_percent()
        
        msg = f"Memory usage: {current_mb:.1f}MB ({percent:.1f}%)"
        if context:
            msg = f"{context} - {msg}"
        
        if self._baseline_mb is not None:
            delta = self.get_delta_mb()
            msg += f" [Δ {delta:+.1f}MB from baseline]"
        
        logger.info(msg)
    
    def get_system_memory_info(self) -> dict:
        """
        Get system-wide memory information.
        
        Returns:
            Dictionary with system memory stats
        """
        mem = psutil.virtual_memory()
        return {
            'total_mb': mem.total / (1024 * 1024),
            'available_mb': mem.available / (1024 * 1024),
            'used_mb': mem.used / (1024 * 1024),
            'percent': mem.percent,
        }


def optimize_memory(aggressive: bool = False):
    """
    Optimize memory usage by triggering garbage collection.
    
    Args:
        aggressive: If True, performs more aggressive optimization
    """
    if aggressive:
        # Aggressive: Full collection of all generations
        logger.debug("Performing aggressive garbage collection")
        gc.collect(2)  # Collect generation 2 (oldest)
        gc.collect(1)  # Collect generation 1
        gc.collect(0)  # Collect generation 0 (youngest)
    else:
        # Normal: Standard garbage collection
        logger.debug("Performing standard garbage collection")
        gc.collect()


def get_gc_stats() -> dict:
    """
    Get garbage collection statistics.
    
    Returns:
        Dictionary with GC stats
    """
    counts = gc.get_count()
    stats = gc.get_stats()
    
    return {
        'counts': {
            'gen0': counts[0],
            'gen1': counts[1],
            'gen2': counts[2],
        },
        'collections': {
            f'gen{i}': stats[i].get('collections', 0)
            for i in range(len(stats))
        },
        'threshold': gc.get_threshold(),
    }


def log_memory_summary():
    """Log a summary of memory usage and GC stats."""
    monitor = MemoryMonitor()
    
    # Process memory
    current_mb = monitor.get_current_usage_mb()
    percent = monitor.get_current_usage_percent()
    
    # System memory
    sys_mem = monitor.get_system_memory_info()
    
    # GC stats
    gc_stats = get_gc_stats()
    
    logger.info(
        f"\n"
        f"Memory Summary:\n"
        f"  Process: {current_mb:.1f}MB ({percent:.1f}% of system)\n"
        f"  System: {sys_mem['used_mb']:.1f}MB / {sys_mem['total_mb']:.1f}MB "
        f"({sys_mem['percent']:.1f}% used)\n"
        f"  Available: {sys_mem['available_mb']:.1f}MB\n"
        f"  GC Counts: Gen0={gc_stats['counts']['gen0']}, "
        f"Gen1={gc_stats['counts']['gen1']}, Gen2={gc_stats['counts']['gen2']}"
    )

