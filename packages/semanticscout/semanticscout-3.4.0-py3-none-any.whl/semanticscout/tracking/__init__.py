"""
Query intent tracking module for SemanticScout.

This module provides functionality to track query intents and relevance feedback
to build a meta-learning system for improved search performance over time.
"""

from .query_intent_tracker import QueryIntentTracker
from .exceptions import QueryTrackingError, ValidationError, StorageError

__all__ = [
    "QueryIntentTracker",
    "QueryTrackingError", 
    "ValidationError",
    "StorageError"
]
