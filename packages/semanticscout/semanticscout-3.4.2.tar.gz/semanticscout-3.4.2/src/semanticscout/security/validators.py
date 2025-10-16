"""
Security validators for input validation and sanitization.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class PathValidator:
    """Validates and sanitizes file system paths."""

    def __init__(self, allowed_directories: Optional[list[str]] = None):
        """
        Initialize path validator.

        Args:
            allowed_directories: List of allowed base directories (default: current working directory)
        """
        if allowed_directories is None:
            # Default to current working directory
            self.allowed_directories = [Path.cwd()]
        else:
            self.allowed_directories = [
                Path(d).resolve() for d in allowed_directories
            ]

        logger.info(f"Initialized path validator with {len(self.allowed_directories)} allowed directories")

    def validate_path(self, path: str) -> Path:
        """
        Validate and sanitize a file system path.

        Args:
            path: Path to validate

        Returns:
            Resolved absolute Path object

        Raises:
            ValidationError: If path is invalid or not allowed
        """
        if not path or not path.strip():
            raise ValidationError("Path cannot be empty")

        try:
            # Resolve to absolute path
            resolved_path = Path(path).resolve()

            # Check if path exists
            if not resolved_path.exists():
                raise ValidationError(f"Path does not exist: {path}")

            # Check if path is within allowed directories
            is_allowed = False
            for allowed_dir in self.allowed_directories:
                try:
                    # Check if resolved_path is relative to allowed_dir
                    resolved_path.relative_to(allowed_dir)
                    is_allowed = True
                    break
                except ValueError:
                    # Not relative to this allowed directory
                    continue

            if not is_allowed:
                raise ValidationError(
                    f"Path is not within allowed directories: {path}"
                )

            # Check for symlinks to sensitive areas
            if resolved_path.is_symlink():
                target = resolved_path.readlink()
                # Recursively validate the symlink target
                return self.validate_path(str(target))

            logger.debug(f"Validated path: {resolved_path}")
            return resolved_path

        except (OSError, PermissionError) as e:
            raise ValidationError(f"Cannot access path: {path} - {str(e)}")

    def validate_directory(self, path: str) -> Path:
        """
        Validate that path is a directory.

        Args:
            path: Path to validate

        Returns:
            Resolved absolute Path object

        Raises:
            ValidationError: If path is not a directory
        """
        resolved_path = self.validate_path(path)

        if not resolved_path.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")

        return resolved_path

    def validate_file(self, path: str) -> Path:
        """
        Validate that path is a file.

        Args:
            path: Path to validate

        Returns:
            Resolved absolute Path object

        Raises:
            ValidationError: If path is not a file
        """
        resolved_path = self.validate_path(path)

        if not resolved_path.is_file():
            raise ValidationError(f"Path is not a file: {path}")

        return resolved_path


class InputValidator:
    """Validates and sanitizes user inputs."""

    MAX_QUERY_LENGTH = 1000
    MIN_TOP_K = 1
    MAX_TOP_K = 100
    MAX_FILE_SIZE_MB = 10.0
    MAX_CODEBASE_SIZE_GB = 10.0
    MAX_FILES = 100000

    @staticmethod
    def validate_query(query: str) -> str:
        """
        Validate and sanitize a search query.

        Args:
            query: Query string to validate

        Returns:
            Sanitized query string

        Raises:
            ValidationError: If query is invalid
        """
        if not query or not query.strip():
            raise ValidationError("Query cannot be empty")

        # Strip whitespace
        query = query.strip()

        # Check length
        if len(query) > InputValidator.MAX_QUERY_LENGTH:
            raise ValidationError(
                f"Query exceeds maximum length of {InputValidator.MAX_QUERY_LENGTH} characters"
            )

        logger.debug(f"Validated query: {query[:50]}...")
        return query

    @staticmethod
    def validate_top_k(top_k: int) -> int:
        """
        Validate top_k parameter.

        Args:
            top_k: Number of results to return

        Returns:
            Validated top_k value

        Raises:
            ValidationError: If top_k is invalid
        """
        if not isinstance(top_k, int):
            raise ValidationError("top_k must be an integer")

        if top_k < InputValidator.MIN_TOP_K or top_k > InputValidator.MAX_TOP_K:
            raise ValidationError(
                f"top_k must be between {InputValidator.MIN_TOP_K} and {InputValidator.MAX_TOP_K}"
            )

        return top_k

    @staticmethod
    def validate_collection_name(name: str) -> str:
        """
        Validate collection name.

        Args:
            name: Collection name to validate

        Returns:
            Validated collection name

        Raises:
            ValidationError: If name is invalid
        """
        if not name or not name.strip():
            raise ValidationError("Collection name cannot be empty")

        # Strip whitespace
        name = name.strip()

        # Check for invalid characters (only allow alphanumeric, underscore, hyphen)
        if not all(c.isalnum() or c in "_-" for c in name):
            raise ValidationError(
                "Collection name can only contain alphanumeric characters, underscores, and hyphens"
            )

        # Check length
        if len(name) > 255:
            raise ValidationError("Collection name exceeds maximum length of 255 characters")

        return name

    @staticmethod
    def validate_codebase_size(path: Path) -> None:
        """
        Validate that codebase size is within limits.

        Args:
            path: Path to codebase directory

        Raises:
            ValidationError: If codebase is too large
        """
        total_size = 0
        file_count = 0
        skipped_files = 0

        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                try:
                    file_size = file_path.stat().st_size

                    # Check individual file size - SKIP instead of failing
                    file_size_mb = file_size / (1024 * 1024)
                    if file_size_mb > InputValidator.MAX_FILE_SIZE_MB:
                        logger.warning(
                            f"Skipping large file ({file_size_mb:.2f}MB > {InputValidator.MAX_FILE_SIZE_MB}MB): {file_path}"
                        )
                        skipped_files += 1
                        continue

                    total_size += file_size
                    file_count += 1

                    # Check total file count
                    if file_count > InputValidator.MAX_FILES:
                        raise ValidationError(
                            f"Codebase exceeds maximum file count of {InputValidator.MAX_FILES}"
                        )

                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue

        # Check total size
        total_size_gb = total_size / (1024 * 1024 * 1024)
        if total_size_gb > InputValidator.MAX_CODEBASE_SIZE_GB:
            raise ValidationError(
                f"Codebase exceeds maximum size of {InputValidator.MAX_CODEBASE_SIZE_GB}GB"
            )

        logger.info(
            f"Validated codebase: {file_count} files, {total_size_gb:.2f}GB, {skipped_files} files skipped (too large)"
        )


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(
        self,
        max_indexing_per_hour: int = 100,
        max_search_per_minute: int = 1000,
    ):
        """
        Initialize rate limiter.

        Args:
            max_indexing_per_hour: Maximum indexing requests per hour
            max_search_per_minute: Maximum search requests per minute
        """
        self.max_indexing_per_hour = max_indexing_per_hour
        self.max_search_per_minute = max_search_per_minute

        self.indexing_requests: list[datetime] = []
        self.search_requests: list[datetime] = []

        logger.info(
            f"Initialized rate limiter: {max_indexing_per_hour} indexing/hour, "
            f"{max_search_per_minute} search/minute"
        )

    def check_indexing_rate(self) -> None:
        """
        Check if indexing request is within rate limit.

        Raises:
            ValidationError: If rate limit exceeded
        """
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        # Remove old requests
        self.indexing_requests = [
            req for req in self.indexing_requests if req > one_hour_ago
        ]

        # Check limit
        if len(self.indexing_requests) >= self.max_indexing_per_hour:
            raise ValidationError(
                f"Rate limit exceeded: Maximum {self.max_indexing_per_hour} indexing requests per hour"
            )

        # Record this request
        self.indexing_requests.append(now)
        logger.debug(f"Indexing request allowed ({len(self.indexing_requests)}/{self.max_indexing_per_hour})")

    def check_search_rate(self) -> None:
        """
        Check if search request is within rate limit.

        Raises:
            ValidationError: If rate limit exceeded
        """
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Remove old requests
        self.search_requests = [
            req for req in self.search_requests if req > one_minute_ago
        ]

        # Check limit
        if len(self.search_requests) >= self.max_search_per_minute:
            raise ValidationError(
                f"Rate limit exceeded: Maximum {self.max_search_per_minute} search requests per minute"
            )

        # Record this request
        self.search_requests.append(now)
        logger.debug(f"Search request allowed ({len(self.search_requests)}/{self.max_search_per_minute})")


