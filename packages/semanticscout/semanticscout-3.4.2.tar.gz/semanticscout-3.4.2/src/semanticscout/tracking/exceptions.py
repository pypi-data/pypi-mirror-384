"""
Exception classes for query intent tracking.
"""


class QueryTrackingError(Exception):
    """Base exception for query tracking operations."""
    pass


class ValidationError(QueryTrackingError):
    """Raised when input validation fails."""
    pass


class StorageError(QueryTrackingError):
    """Raised when vector storage operations fail."""
    pass
