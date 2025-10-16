"""
File discovery module for finding code files while respecting .gitignore patterns.
"""

import logging
from pathlib import Path
from typing import List, Set, Optional
import pathspec

# Configure logging to stderr (CRITICAL for MCP STDIO transport)
logger = logging.getLogger(__name__)


class FileDiscovery:
    """
    Discovers code files in a directory while respecting .gitignore patterns
    and filtering by file type.
    """

    # Default file extensions to include
    DEFAULT_INCLUDE_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".cs",
        ".swift",
        ".kt",
        ".scala",
        ".md",
        ".txt",
        ".yaml",
        ".yml",
        ".json",
        ".xml",
        ".html",
        ".css",
        ".scss",
        ".sql",
    }

    # Default patterns to exclude (in addition to .gitignore)
    DEFAULT_EXCLUDE_PATTERNS = [
        ".git/",
        ".git/**",
        "node_modules/",
        "node_modules/**",
        "__pycache__/",
        "__pycache__/**",
        "*.pyc",
        "*.pyo",
        "*.so",
        "*.dll",
        "*.dylib",
        "*.exe",
        "*.bin",
        "*.class",
        "*.jar",
        "*.war",
        ".venv/",
        ".venv/**",
        "venv/",
        "venv/**",
        "env/",
        "env/**",
        ".env",
        "dist/",
        "dist/**",
        "build/",
        "build/**",
        "target/",
        "target/**",
        ".idea/",
        ".idea/**",
        ".vscode/",
        ".vscode/**",
        "*.min.js",
        "*.min.css",
        ".DS_Store",
        # v2.4.4: Exclude analysis/documentation folders (avoid meta-results)
        "analysis/",
        "analysis/**",
        ".augster/",
        ".augster/**",
        # v2.4.4: Exclude library folders (avoid minified code)
        "lib/",
        "lib/**",
        "vendor/",
        "vendor/**",
        "packages/",
        "packages/**",
        "LICENSE*",
        "MANIFEST*",
        "htmlcov/",
        "htmlcov/**"
    ]

    def __init__(
        self,
        include_extensions: Optional[Set[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_depth: int = 50,
        max_file_size_mb: float = 10.0,
        filter_untracked_files: bool = True,
    ):
        """
        Initialize the file discovery system.

        Args:
            include_extensions: Set of file extensions to include (e.g., {'.py', '.js'})
            exclude_patterns: Additional patterns to exclude beyond defaults
            max_depth: Maximum directory depth to traverse (prevents infinite loops)
            max_file_size_mb: Maximum file size in MB (files larger than this are skipped)
            filter_untracked_files: Whether to filter out untracked files (default: True)
        """
        self.include_extensions = include_extensions or self.DEFAULT_INCLUDE_EXTENSIONS
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS.copy()
        if exclude_patterns:
            self.exclude_patterns.extend(exclude_patterns)
        self.max_depth = max_depth
        self.max_file_size_mb = max_file_size_mb
        self.filter_untracked_files = filter_untracked_files
        self._visited_paths: Set[Path] = set()

    def discover_files(self, root_path: str | Path, untracked_files: Optional[List[str]] = None) -> List[Path]:
        """
        Discover all code files in the given directory.

        Args:
            root_path: Root directory to search
            untracked_files: Optional list of untracked file paths to exclude

        Returns:
            List of Path objects for discovered files

        Raises:
            ValueError: If root_path doesn't exist or isn't a directory
        """
        root = Path(root_path).resolve()

        if not root.exists():
            raise ValueError(f"Path does not exist: {root}")

        if not root.is_dir():
            raise ValueError(f"Path is not a directory: {root}")

        logger.info(f"Starting file discovery in: {root}")

        # Load .gitignore patterns
        gitignore_spec = self._load_gitignore_patterns(root)

        # Convert untracked files to set of Path objects for efficient lookup
        untracked_paths = set()
        if untracked_files and self.filter_untracked_files:
            for file_path in untracked_files:
                try:
                    # Convert relative path to absolute path
                    abs_path = (root / file_path).resolve()
                    untracked_paths.add(abs_path)
                except Exception as e:
                    logger.warning(f"Could not process untracked file path {file_path}: {e}")

            logger.info(f"Will filter {len(untracked_paths)} untracked files")

        # Reset visited paths for this discovery session
        self._visited_paths = set()

        # Discover files
        discovered_files = []
        self._discover_recursive(root, root, gitignore_spec, discovered_files, untracked_paths, depth=0)

        logger.info(f"Discovered {len(discovered_files)} files in {root}")

        return discovered_files

    def _discover_recursive(
        self,
        current_path: Path,
        root_path: Path,
        gitignore_spec: Optional[pathspec.PathSpec],
        discovered_files: List[Path],
        untracked_paths: Set[Path],
        depth: int,
    ) -> None:
        """
        Recursively discover files in a directory.

        Args:
            current_path: Current directory being processed
            root_path: Original root directory
            gitignore_spec: Compiled gitignore patterns
            discovered_files: List to append discovered files to
            untracked_paths: Set of untracked file paths to exclude
            depth: Current recursion depth
        """
        # Check depth limit
        if depth > self.max_depth:
            logger.warning(f"Max depth ({self.max_depth}) reached at: {current_path}")
            return

        # Resolve symlinks and check for cycles
        try:
            resolved_path = current_path.resolve()
        except (OSError, RuntimeError) as e:
            logger.warning(f"Could not resolve path {current_path}: {e}")
            return

        if resolved_path in self._visited_paths:
            logger.debug(f"Skipping already visited path: {resolved_path}")
            return

        self._visited_paths.add(resolved_path)

        # Iterate through directory contents
        try:
            entries = list(current_path.iterdir())
        except PermissionError:
            logger.warning(f"Permission denied accessing: {current_path}")
            return
        except OSError as e:
            logger.warning(f"Error accessing {current_path}: {e}")
            return

        for entry in entries:
            # Get relative path for pattern matching
            try:
                rel_path = entry.relative_to(root_path)
            except ValueError:
                # Entry is not relative to root (shouldn't happen, but be safe)
                continue

            # Convert to string with forward slashes for pathspec
            rel_path_str = str(rel_path).replace("\\", "/")

            # Check if should be excluded
            if self._should_exclude(rel_path_str, entry, gitignore_spec):
                continue

            # Check if file is untracked and should be filtered
            if entry.is_file() and untracked_paths and entry.resolve() in untracked_paths:
                logger.debug(f"Filtering untracked file: {entry}")
                continue

            if entry.is_file():
                # Check if file should be included
                if self._should_include_file(entry):
                    discovered_files.append(entry)
            elif entry.is_dir():
                # Recurse into subdirectory
                self._discover_recursive(
                    entry, root_path, gitignore_spec, discovered_files, untracked_paths, depth + 1
                )

    def _should_exclude(
        self,
        rel_path_str: str,
        entry: Path,
        gitignore_spec: Optional[pathspec.PathSpec],
    ) -> bool:
        """
        Check if a path should be excluded based on patterns.

        Args:
            rel_path_str: Relative path as string with forward slashes
            entry: Path object
            gitignore_spec: Compiled gitignore patterns

        Returns:
            True if should be excluded, False otherwise
        """
        # Check default exclude patterns
        exclude_spec = pathspec.PathSpec.from_lines("gitwildmatch", self.exclude_patterns)

        # Add trailing slash for directories
        check_path = rel_path_str + "/" if entry.is_dir() else rel_path_str

        if exclude_spec.match_file(check_path):
            return True

        # Check gitignore patterns
        if gitignore_spec and gitignore_spec.match_file(check_path):
            return True

        return False

    def _should_include_file(self, file_path: Path) -> bool:
        """
        Check if a file should be included based on its extension and size.

        Args:
            file_path: Path to the file

        Returns:
            True if file should be included, False otherwise
        """
        # Check extension
        if file_path.suffix.lower() not in self.include_extensions:
            return False

        # Check file size
        try:
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)

            if file_size_mb > self.max_file_size_mb:
                logger.warning(
                    f"Skipping large file ({file_size_mb:.2f}MB > {self.max_file_size_mb}MB): {file_path}"
                )
                return False
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not check size of {file_path}: {e}")
            return False

        return True

    def _load_gitignore_patterns(self, root_path: Path) -> Optional[pathspec.PathSpec]:
        """
        Load and compile .gitignore patterns from the root directory.

        Args:
            root_path: Root directory to search for .gitignore

        Returns:
            Compiled PathSpec object or None if no .gitignore found
        """
        gitignore_path = root_path / ".gitignore"

        if not gitignore_path.exists():
            logger.debug(f"No .gitignore found at: {gitignore_path}")
            return None

        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                patterns = f.read().splitlines()

            # Filter out comments and empty lines
            patterns = [
                line.strip()
                for line in patterns
                if line.strip() and not line.strip().startswith("#")
            ]

            logger.info(f"Loaded {len(patterns)} patterns from .gitignore")

            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)

        except Exception as e:
            logger.warning(f"Error loading .gitignore from {gitignore_path}: {e}")
            return None


