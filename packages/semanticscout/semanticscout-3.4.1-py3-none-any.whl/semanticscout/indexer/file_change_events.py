"""
File change event schema and validation for real-time incremental indexing.

This module defines the schema for file change events that can be sent from
editors/MCP clients to trigger incremental updates. Events are validated for
security and correctness before processing.
"""

import logging
from pathlib import Path
from typing import List, Literal, Optional, TypedDict
from datetime import datetime

logger = logging.getLogger(__name__)


# Type definitions for file change events
FileChangeType = Literal["added", "modified", "deleted", "renamed"]


class FileChangeEvent(TypedDict):
    """
    Schema for a single file change event.
    
    Attributes:
        type: Type of change ('added', 'modified', 'deleted', 'renamed')
        path: Relative path to the changed file (relative to workspace root)
        old_path: Previous path for renamed files (required only for 'renamed' type)
        timestamp: Unix timestamp (milliseconds) when the change occurred
        content_hash: Optional MD5 hash of file content for validation
    
    Examples:
        # File added
        {
            "type": "added",
            "path": "src/new_module.py",
            "timestamp": 1696800000000,
            "content_hash": "5d41402abc4b2a76b9719d911017c592"
        }
        
        # File modified
        {
            "type": "modified",
            "path": "src/existing_module.py",
            "timestamp": 1696800001000,
            "content_hash": "7d793037a0760186574b0282f2f435e7"
        }
        
        # File deleted
        {
            "type": "deleted",
            "path": "src/old_module.py",
            "timestamp": 1696800002000
        }
        
        # File renamed
        {
            "type": "renamed",
            "path": "src/new_name.py",
            "old_path": "src/old_name.py",
            "timestamp": 1696800003000,
            "content_hash": "098f6bcd4621d373cade4e832627b4f6"
        }
    """
    type: FileChangeType
    path: str
    old_path: Optional[str]
    timestamp: int
    content_hash: Optional[str]


class FileChangeBatch(TypedDict):
    """
    Schema for a batch of file change events.
    
    Attributes:
        events: List of file change events to process
        workspace_root: Absolute path to workspace root directory
        debounce_ms: Debounce time in milliseconds (events within this window are batched)
    
    Example:
        {
            "events": [
                {
                    "type": "modified",
                    "path": "src/module1.py",
                    "timestamp": 1696800000000,
                    "content_hash": "abc123"
                },
                {
                    "type": "added",
                    "path": "src/module2.py",
                    "timestamp": 1696800001000,
                    "content_hash": "def456"
                }
            ],
            "workspace_root": "/home/user/project",
            "debounce_ms": 500
        }
    """
    events: List[FileChangeEvent]
    workspace_root: str
    debounce_ms: int


class ValidationError(Exception):
    """Exception raised when event validation fails."""
    pass


class FileChangeEventValidator:
    """Validator for file change events with security checks."""
    
    # Maximum reasonable timestamp (current time + 1 hour)
    MAX_TIMESTAMP_OFFSET_MS = 3600000  # 1 hour
    
    # Minimum reasonable timestamp (1 year ago)
    MIN_TIMESTAMP_OFFSET_MS = 31536000000  # 1 year
    
    @staticmethod
    def validate_event(event: FileChangeEvent, workspace_root: Path) -> None:
        """
        Validate a single file change event.
        
        Args:
            event: File change event to validate
            workspace_root: Workspace root directory for path validation
            
        Raises:
            ValidationError: If event is invalid
        """
        # Validate type
        if event["type"] not in ("added", "modified", "deleted", "renamed"):
            raise ValidationError(f"Invalid event type: {event['type']}")
        
        # Validate path
        if not event.get("path"):
            raise ValidationError("Event must have a 'path' field")
        
        FileChangeEventValidator._validate_path(event["path"], workspace_root)
        
        # Validate old_path for renamed events
        if event["type"] == "renamed":
            if not event.get("old_path"):
                raise ValidationError("Renamed event must have 'old_path' field")
            FileChangeEventValidator._validate_path(event["old_path"], workspace_root)
        
        # Validate timestamp
        if not event.get("timestamp"):
            raise ValidationError("Event must have a 'timestamp' field")
        
        FileChangeEventValidator._validate_timestamp(event["timestamp"])
        
        # Validate content_hash if present
        if event.get("content_hash"):
            FileChangeEventValidator._validate_content_hash(event["content_hash"])
    
    @staticmethod
    def validate_batch(batch: FileChangeBatch) -> None:
        """
        Validate a batch of file change events.
        
        Args:
            batch: File change batch to validate
            
        Raises:
            ValidationError: If batch is invalid
        """
        # Validate workspace_root
        if not batch.get("workspace_root"):
            raise ValidationError("Batch must have 'workspace_root' field")
        
        workspace_root = Path(batch["workspace_root"])
        if not workspace_root.exists():
            raise ValidationError(f"Workspace root does not exist: {workspace_root}")
        
        if not workspace_root.is_dir():
            raise ValidationError(f"Workspace root is not a directory: {workspace_root}")
        
        # Validate debounce_ms
        if not batch.get("debounce_ms"):
            raise ValidationError("Batch must have 'debounce_ms' field")
        
        if not isinstance(batch["debounce_ms"], int) or batch["debounce_ms"] < 0:
            raise ValidationError(f"Invalid debounce_ms: {batch['debounce_ms']}")
        
        # Validate events
        if "events" not in batch:
            raise ValidationError("Batch must have 'events' field")

        if not isinstance(batch["events"], list):
            raise ValidationError("Events must be a list")

        if len(batch["events"]) == 0:
            raise ValidationError("Batch must contain at least one event")
        
        # Validate each event
        for i, event in enumerate(batch["events"]):
            try:
                FileChangeEventValidator.validate_event(event, workspace_root)
            except ValidationError as e:
                raise ValidationError(f"Event {i} validation failed: {e}")
    
    @staticmethod
    def _validate_path(path: str, workspace_root: Path) -> None:
        """
        Validate file path for security (prevent path traversal).

        Args:
            path: Relative file path
            workspace_root: Workspace root directory

        Raises:
            ValidationError: If path is invalid or unsafe
        """
        # Check for absolute paths (cross-platform)
        # On Windows, /etc/passwd is not absolute, but starts with / which is suspicious
        if Path(path).is_absolute() or path.startswith('/') or path.startswith('\\'):
            raise ValidationError(f"Path must be relative: {path}")

        # Check for path traversal attempts
        if ".." in Path(path).parts:
            raise ValidationError(f"Path traversal detected: {path}")

        # Resolve full path and check it's within workspace
        try:
            full_path = (workspace_root / path).resolve()
            workspace_root_resolved = workspace_root.resolve()

            # Check if path is within workspace
            if not str(full_path).startswith(str(workspace_root_resolved)):
                raise ValidationError(f"Path outside workspace: {path}")
        except Exception as e:
            raise ValidationError(f"Invalid path: {path} ({e})")
    
    @staticmethod
    def _validate_timestamp(timestamp: int) -> None:
        """
        Validate timestamp is reasonable.
        
        Args:
            timestamp: Unix timestamp in milliseconds
            
        Raises:
            ValidationError: If timestamp is unreasonable
        """
        if not isinstance(timestamp, int):
            raise ValidationError(f"Timestamp must be an integer: {timestamp}")
        
        current_time_ms = int(datetime.utcnow().timestamp() * 1000)
        
        # Check timestamp is not too far in the future
        if timestamp > current_time_ms + FileChangeEventValidator.MAX_TIMESTAMP_OFFSET_MS:
            raise ValidationError(f"Timestamp too far in future: {timestamp}")
        
        # Check timestamp is not too far in the past
        if timestamp < current_time_ms - FileChangeEventValidator.MIN_TIMESTAMP_OFFSET_MS:
            raise ValidationError(f"Timestamp too far in past: {timestamp}")
    
    @staticmethod
    def _validate_content_hash(content_hash: str) -> None:
        """
        Validate content hash format.
        
        Args:
            content_hash: MD5 hash string
            
        Raises:
            ValidationError: If hash format is invalid
        """
        if not isinstance(content_hash, str):
            raise ValidationError(f"Content hash must be a string: {content_hash}")
        
        # MD5 hash is 32 hexadecimal characters
        if len(content_hash) != 32:
            raise ValidationError(f"Invalid MD5 hash length: {len(content_hash)}")
        
        # Check all characters are hexadecimal
        try:
            int(content_hash, 16)
        except ValueError:
            raise ValidationError(f"Invalid MD5 hash format: {content_hash}")

