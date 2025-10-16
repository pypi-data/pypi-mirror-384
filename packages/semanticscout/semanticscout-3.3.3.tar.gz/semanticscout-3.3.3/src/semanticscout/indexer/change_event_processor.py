"""
Change event processor with priority queue, rate limiting, and circuit breaker.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from queue import PriorityQueue
from enum import IntEnum

from ..utils.rate_limiter import RateLimiter, CircuitBreaker, RateLimitConfig

logger = logging.getLogger(__name__)


class EventPriority(IntEnum):
    """Priority levels for file change events (lower number = higher priority)."""
    MODIFIED = 1  # Highest priority - existing files changed
    ADDED = 2     # Medium priority - new files
    DELETED = 3   # Lowest priority - files removed


@dataclass(order=True)
class PrioritizedEvent:
    """File change event with priority."""
    priority: int
    timestamp: float
    event: Dict[str, Any] = field(compare=False)


@dataclass
class ProcessorMetrics:
    """Metrics for change event processor."""
    total_events_received: int = 0
    total_events_processed: int = 0
    total_events_failed: int = 0
    total_events_rate_limited: int = 0
    events_by_type: Dict[str, int] = field(default_factory=lambda: {
        "added": 0,
        "modified": 0,
        "deleted": 0,
        "renamed": 0
    })
    processing_times: List[float] = field(default_factory=list)
    last_processed_time: Optional[float] = None
    suspicious_patterns_detected: int = 0


class ChangeEventProcessor:
    """
    Processes file change events with priority queue, rate limiting, and safety features.
    """
    
    def __init__(
        self,
        delta_indexer,
        rate_limit_config: Optional[RateLimitConfig] = None,
        enable_circuit_breaker: bool = True,
    ):
        """
        Initialize change event processor.
        
        Args:
            delta_indexer: DeltaIndexer instance for applying updates
            rate_limit_config: Rate limit configuration
            enable_circuit_breaker: Whether to enable circuit breaker
        """
        self.delta_indexer = delta_indexer
        self.rate_limiter = RateLimiter(rate_limit_config)
        self.circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None
        
        self.event_queue = PriorityQueue()
        self.metrics = ProcessorMetrics()
        
        # Suspicious pattern detection
        self.rapid_fire_threshold = 50  # events in 1 second
        self.mass_change_threshold = 100  # events in one batch
    
    def queue_events(
        self,
        events: List[Dict[str, Any]],
        workspace_root: Path,
    ) -> Dict[str, Any]:
        """
        Queue file change events for processing.
        
        Args:
            events: List of file change events
            workspace_root: Root directory of workspace
            
        Returns:
            Dictionary with queuing results
        """
        queued = 0
        rate_limited = 0
        suspicious = False
        
        # Check for suspicious patterns
        if len(events) > self.mass_change_threshold:
            logger.warning(
                f"Suspicious pattern: {len(events)} events in single batch "
                f"(threshold: {self.mass_change_threshold})"
            )
            self.metrics.suspicious_patterns_detected += 1
            suspicious = True
        
        # Check for rapid fire
        now = time.time()
        recent_events = [
            ts for ts in self.metrics.processing_times[-50:]
            if now - ts <= 1.0
        ]
        if len(recent_events) > self.rapid_fire_threshold:
            logger.warning(
                f"Suspicious pattern: {len(recent_events)} events in 1 second "
                f"(threshold: {self.rapid_fire_threshold})"
            )
            self.metrics.suspicious_patterns_detected += 1
            suspicious = True
        
        # Queue events with priority
        for event in events:
            self.metrics.total_events_received += 1
            
            # Rate limiting
            if not self.rate_limiter.allow_event():
                rate_limited += 1
                self.metrics.total_events_rate_limited += 1
                continue
            
            # Determine priority
            event_type = event.get("type", "modified")
            priority = self._get_priority(event_type)
            
            # Create prioritized event
            prioritized = PrioritizedEvent(
                priority=priority,
                timestamp=event.get("timestamp", time.time()),
                event=event
            )
            
            self.event_queue.put(prioritized)
            queued += 1
            
            # Update metrics
            if event_type in self.metrics.events_by_type:
                self.metrics.events_by_type[event_type] += 1
        
        return {
            "queued": queued,
            "rate_limited": rate_limited,
            "queue_size": self.event_queue.qsize(),
            "suspicious_pattern_detected": suspicious,
        }
    
    def process_queue(
        self,
        collection_name: str,
        root_path: Path,
        max_events: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Process queued file change events.
        
        Args:
            collection_name: Name of the collection
            root_path: Root directory of codebase
            max_events: Maximum number of events to process (None = all)
            
        Returns:
            Dictionary with processing results
        """
        processed = 0
        failed = 0
        results = []
        
        while not self.event_queue.empty():
            if max_events and processed >= max_events:
                break
            
            # Get next event
            prioritized_event = self.event_queue.get()
            event = prioritized_event.event
            
            # Process event
            start_time = time.time()
            try:
                if self.circuit_breaker:
                    result = self.circuit_breaker.call(
                        self._process_single_event,
                        event,
                        collection_name,
                        root_path
                    )
                else:
                    result = self._process_single_event(
                        event,
                        collection_name,
                        root_path
                    )
                
                results.append(result)
                processed += 1
                self.metrics.total_events_processed += 1
                
            except Exception as e:
                logger.error(f"Failed to process event {event}: {e}")
                failed += 1
                self.metrics.total_events_failed += 1
                results.append({
                    "success": False,
                    "error": str(e),
                    "event": event
                })
            
            # Update metrics
            processing_time = time.time() - start_time
            self.metrics.processing_times.append(processing_time)
            if len(self.metrics.processing_times) > 1000:
                self.metrics.processing_times = self.metrics.processing_times[-1000:]
            self.metrics.last_processed_time = time.time()
        
        return {
            "processed": processed,
            "failed": failed,
            "remaining": self.event_queue.qsize(),
            "results": results,
        }
    
    def _process_single_event(
        self,
        event: Dict[str, Any],
        collection_name: str,
        root_path: Path,
    ) -> Dict[str, Any]:
        """Process a single file change event."""
        event_type = event.get("type")
        file_path = event.get("path")
        
        if not file_path:
            raise ValueError("Event missing 'path' field")
        
        absolute_path = root_path / file_path
        
        if event_type in ["added", "modified"]:
            # Update file
            result = self.delta_indexer.update_file(
                file_path=absolute_path,
                collection_name=collection_name,
                root_path=root_path,
            )
            return {
                "success": result.success,
                "event_type": event_type,
                "file_path": file_path,
                "chunks_added": result.chunks_added,
                "chunks_reused": result.chunks_reused,
                "error": result.error,
            }
        
        elif event_type == "deleted":
            # Delete file from index
            result = self.delta_indexer.delete_file(
                file_path=absolute_path,
                collection_name=collection_name,
                root_path=root_path,
            )
            return {
                "success": result.success,
                "event_type": event_type,
                "file_path": file_path,
                "chunks_removed": result.chunks_removed,
                "error": result.error,
            }
        
        elif event_type == "renamed":
            # Handle rename as delete + add
            old_path = event.get("old_path")
            if old_path:
                # Delete old
                self.delta_indexer.delete_file(
                    file_path=root_path / old_path,
                    collection_name=collection_name,
                    root_path=root_path,
                )
            
            # Add new
            result = self.delta_indexer.update_file(
                file_path=absolute_path,
                collection_name=collection_name,
                root_path=root_path,
            )
            return {
                "success": result.success,
                "event_type": event_type,
                "file_path": file_path,
                "old_path": old_path,
                "chunks_added": result.chunks_added,
                "error": result.error,
            }
        
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def _get_priority(self, event_type: str) -> int:
        """Get priority for event type."""
        if event_type == "modified":
            return EventPriority.MODIFIED
        elif event_type == "added":
            return EventPriority.ADDED
        elif event_type == "deleted":
            return EventPriority.DELETED
        else:
            return EventPriority.MODIFIED  # Default to high priority
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processor metrics."""
        avg_processing_time = (
            sum(self.metrics.processing_times) / len(self.metrics.processing_times)
            if self.metrics.processing_times else 0.0
        )
        
        return {
            "total_events_received": self.metrics.total_events_received,
            "total_events_processed": self.metrics.total_events_processed,
            "total_events_failed": self.metrics.total_events_failed,
            "total_events_rate_limited": self.metrics.total_events_rate_limited,
            "events_by_type": self.metrics.events_by_type,
            "queue_size": self.event_queue.qsize(),
            "avg_processing_time_ms": avg_processing_time * 1000,
            "last_processed_time": self.metrics.last_processed_time,
            "suspicious_patterns_detected": self.metrics.suspicious_patterns_detected,
            "rate_limiter": self.rate_limiter.get_metrics(),
            "circuit_breaker": (
                self.circuit_breaker.get_state()
                if self.circuit_breaker else None
            ),
        }
    
    def clear_queue(self) -> int:
        """Clear all queued events. Returns number of events cleared."""
        count = 0
        while not self.event_queue.empty():
            self.event_queue.get()
            count += 1
        return count
    
    def reset(self):
        """Reset processor state."""
        self.clear_queue()
        self.rate_limiter.reset()
        if self.circuit_breaker:
            self.circuit_breaker.reset()
        self.metrics = ProcessorMetrics()
        logger.info("Change event processor reset")

