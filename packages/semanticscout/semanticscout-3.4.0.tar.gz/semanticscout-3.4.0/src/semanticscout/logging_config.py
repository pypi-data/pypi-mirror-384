"""
Logging configuration for MCP server.

CRITICAL: MCP servers using STDIO transport MUST NEVER write to stdout.
All logging must go to stderr or files only, otherwise JSON-RPC messages will be corrupted.
"""

import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

from .paths import path_manager


def setup_logging(
    log_level: str = "INFO",
    log_file: str = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Configure logging for MCP server.

    IMPORTANT: All logs go to stderr and files, NEVER to stdout.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (defaults to ~/semanticscout/logs/mcp_server.log)
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup log files to keep (default: 5)

    Returns:
        Configured root logger
    """
    # Use default log file if none provided
    if log_file is None:
        log_file = str(path_manager.get_logs_dir() / "mcp_server.log")

    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # CRITICAL: Console handler writes to stderr, NOT stdout
    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Log initial message
    root_logger.info("=" * 60)
    root_logger.info("Logging configured successfully")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info(f"Console output: stderr (NOT stdout)")
    root_logger.info("=" * 60)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def redirect_stdout_to_stderr():
    """
    Redirect stdout to stderr to prevent accidental stdout writes.

    This is a safety measure to catch any third-party libraries or
    accidental print() statements that might write to stdout.

    WARNING: This is a drastic measure. Only use if absolutely necessary.
    """
    sys.stdout = sys.stderr
    logging.warning("stdout has been redirected to stderr for MCP compatibility")


def verify_no_stdout_writes():
    """
    Verify that nothing is being written to stdout.

    This is a test function to ensure logging configuration is correct.

    Returns:
        True if no stdout writes detected, False otherwise
    """
    import io

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    # Try logging
    logger = logging.getLogger("test")
    logger.info("Test message")
    logger.warning("Test warning")
    logger.error("Test error")

    # Check if anything was written to stdout
    stdout_content = sys.stdout.getvalue()

    # Restore stdout
    sys.stdout = old_stdout

    if stdout_content:
        logging.error(f"CRITICAL: Detected stdout writes: {stdout_content}")
        return False

    logging.info("✓ Verified: No stdout writes detected")
    return True


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    setup_logging(log_level="DEBUG")

    # Get logger
    logger = get_logger(__name__)

    # Test logging at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Verify no stdout writes
    verify_no_stdout_writes()

    # Test that print() statements would be visible (they shouldn't be used!)
    print("WARNING: This print() statement should NOT be used in MCP server code!")
    print("All output should use logger.info() or logger.error() instead")

    logger.info("Logging test complete")


