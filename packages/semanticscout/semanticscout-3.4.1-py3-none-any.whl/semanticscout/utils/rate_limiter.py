"""
Rate limiter for file change events.
"""

import time
import logging
from typing import Optional
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_events_per_second: int = 10
    max_events_per_minute: int = 100
    burst_size: int = 20  # Allow short bursts
    cooldown_seconds: int = 5  # Cooldown after hitting limit


@dataclass
class RateLimitMetrics:
    """Metrics for rate limiting."""
    total_events: int = 0
    allowed_events: int = 0
    rejected_events: int = 0
    last_rejection_time: Optional[float] = None
    rejection_count_last_minute: int = 0
    event_timestamps: deque = field(default_factory=lambda: deque(maxlen=100))


class RateLimiter:
    """
    Token bucket rate limiter for file change events.
    
    Prevents overwhelming the system with too many file change events.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self.metrics = RateLimitMetrics()
        
        # Token bucket for per-second limiting
        self.tokens = self.config.burst_size
        self.last_refill = time.time()
        
        # Sliding window for per-minute limiting
        self.minute_window = deque(maxlen=self.config.max_events_per_minute)
        
        # Circuit breaker state
        self.in_cooldown = False
        self.cooldown_until = 0.0
    
    def allow_event(self) -> bool:
        """
        Check if an event should be allowed.
        
        Returns:
            True if event is allowed, False if rate limited
        """
        now = time.time()
        
        # Check cooldown
        if self.in_cooldown:
            if now < self.cooldown_until:
                self.metrics.rejected_events += 1
                self.metrics.last_rejection_time = now
                return False
            else:
                # Cooldown expired
                self.in_cooldown = False
                logger.info("Rate limiter cooldown expired, resuming normal operation")
        
        # Refill tokens (per-second limit)
        self._refill_tokens(now)
        
        # Check per-second limit (token bucket)
        if self.tokens < 1:
            self._handle_rejection(now, "per-second limit exceeded")
            return False
        
        # Check per-minute limit (sliding window)
        self._clean_minute_window(now)
        if len(self.minute_window) >= self.config.max_events_per_minute:
            self._handle_rejection(now, "per-minute limit exceeded")
            return False
        
        # Allow event
        self.tokens -= 1
        self.minute_window.append(now)
        self.metrics.event_timestamps.append(now)
        self.metrics.total_events += 1
        self.metrics.allowed_events += 1
        
        return True
    
    def _refill_tokens(self, now: float):
        """Refill token bucket based on elapsed time."""
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.config.max_events_per_second
        
        self.tokens = min(
            self.config.burst_size,
            self.tokens + tokens_to_add
        )
        self.last_refill = now
    
    def _clean_minute_window(self, now: float):
        """Remove events older than 1 minute from sliding window."""
        cutoff = now - 60.0
        while self.minute_window and self.minute_window[0] < cutoff:
            self.minute_window.popleft()
    
    def _handle_rejection(self, now: float, reason: str):
        """Handle rate limit rejection."""
        self.metrics.rejected_events += 1
        self.metrics.last_rejection_time = now
        self.metrics.rejection_count_last_minute += 1
        
        # Check if we should enter cooldown
        if self.metrics.rejection_count_last_minute > 10:
            self.in_cooldown = True
            self.cooldown_until = now + self.config.cooldown_seconds
            logger.warning(
                f"Rate limiter entering cooldown for {self.config.cooldown_seconds}s "
                f"due to excessive rejections ({reason})"
            )
        else:
            logger.debug(f"Rate limit rejection: {reason}")
    
    def get_metrics(self) -> dict:
        """
        Get rate limiter metrics.
        
        Returns:
            Dictionary of metrics
        """
        now = time.time()
        
        # Calculate events per second (last 10 seconds)
        recent_events = [
            ts for ts in self.metrics.event_timestamps
            if now - ts <= 10.0
        ]
        events_per_second = len(recent_events) / 10.0 if recent_events else 0.0
        
        return {
            "total_events": self.metrics.total_events,
            "allowed_events": self.metrics.allowed_events,
            "rejected_events": self.metrics.rejected_events,
            "rejection_rate": (
                self.metrics.rejected_events / self.metrics.total_events
                if self.metrics.total_events > 0 else 0.0
            ),
            "events_per_second": events_per_second,
            "in_cooldown": self.in_cooldown,
            "tokens_available": int(self.tokens),
            "minute_window_size": len(self.minute_window),
        }
    
    def reset(self):
        """Reset rate limiter state."""
        self.tokens = self.config.burst_size
        self.last_refill = time.time()
        self.minute_window.clear()
        self.in_cooldown = False
        self.cooldown_until = 0.0
        self.metrics = RateLimitMetrics()
        logger.info("Rate limiter reset")


class CircuitBreaker:
    """
    Circuit breaker for file change event processing.
    
    Prevents cascading failures by stopping processing after repeated failures.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            half_open_max_calls: Max calls to allow in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = "closed"  # closed, open, half_open
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.opened_at = 0.0
        self.half_open_calls = 0
    
    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "open":
            # Check if we should transition to half-open
            if time.time() - self.opened_at >= self.recovery_timeout:
                self.state = "half_open"
                self.half_open_calls = 0
                logger.info("Circuit breaker transitioning to half-open state")
            else:
                raise Exception("Circuit breaker is open - too many failures")
        
        if self.state == "half_open":
            if self.half_open_calls >= self.half_open_max_calls:
                raise Exception("Circuit breaker half-open limit reached")
            self.half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == "half_open":
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                # Recovered!
                self.state = "closed"
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker closed - system recovered")
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "half_open":
            # Failed during recovery - back to open
            self.state = "open"
            self.opened_at = time.time()
            logger.warning("Circuit breaker reopened - recovery failed")
        elif self.failure_count >= self.failure_threshold:
            # Too many failures - open circuit
            self.state = "open"
            self.opened_at = time.time()
            logger.error(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def get_state(self) -> dict:
        """Get circuit breaker state."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
        }
    
    def reset(self):
        """Reset circuit breaker."""
        self.state = "closed"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.opened_at = 0.0
        self.half_open_calls = 0
        logger.info("Circuit breaker reset")

