"""
Unified change detection system with Git and hash-based fallback.

This module provides a unified interface for detecting file changes, automatically
choosing between Git-based detection (fast, reliable) and hash-based detection
(fallback for non-Git repositories).
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

from .git_change_detector import GitChangeDetector, IndexingMetadata
from ..symbol_table.symbol_table import SymbolTable

logger = logging.getLogger(__name__)


class ChangeDetectionStrategy:
    """Base class for change detection strategies."""
    
    def get_changed_files(
        self,
        root_path: Path,
        last_indexed_ref: Optional[str],
        file_extensions: Optional[Set[str]] = None,
    ) -> Dict[str, str]:
        """
        Get changed files since last indexing.
        
        Args:
            root_path: Root directory of the codebase
            last_indexed_ref: Reference to last indexed state (commit hash or timestamp)
            file_extensions: Optional set of file extensions to filter
            
        Returns:
            Dictionary mapping file paths to change types ('added', 'modified', 'deleted', 'committed')
        """
        raise NotImplementedError
    
    def get_current_ref(self) -> str:
        """Get current reference (commit hash or timestamp)."""
        raise NotImplementedError
    
    def get_all_files(
        self, root_path: Path, file_extensions: Optional[Set[str]] = None
    ) -> List[str]:
        """Get all tracked/indexed files."""
        raise NotImplementedError


class GitStrategy(ChangeDetectionStrategy):
    """Git-based change detection strategy."""
    
    def __init__(self, repo_path: Path):
        self.detector = GitChangeDetector(repo_path)
    
    def get_changed_files(
        self,
        root_path: Path,
        last_indexed_ref: Optional[str],
        file_extensions: Optional[Set[str]] = None,
    ) -> Dict[str, str]:
        if not last_indexed_ref:
            return {}
        return self.detector.get_all_changed_files(last_indexed_ref, file_extensions)
    
    def get_current_ref(self) -> str:
        return self.detector.get_current_commit()
    
    def get_all_files(
        self, root_path: Path, file_extensions: Optional[Set[str]] = None
    ) -> List[str]:
        return self.detector.get_tracked_files(file_extensions)


class HashStrategy(ChangeDetectionStrategy):
    """Hash-based change detection strategy for non-Git repositories."""
    
    def __init__(self, symbol_table: Optional[SymbolTable] = None):
        self.symbol_table = symbol_table
    
    def get_changed_files(
        self,
        root_path: Path,
        last_indexed_ref: Optional[str],
        file_extensions: Optional[Set[str]] = None,
    ) -> Dict[str, str]:
        """
        Detect changes by comparing file hashes.
        
        Args:
            root_path: Root directory of the codebase
            last_indexed_ref: Timestamp of last indexing (ISO format)
            file_extensions: Optional set of file extensions to filter
            
        Returns:
            Dictionary mapping file paths to change types
        """
        if not self.symbol_table:
            logger.warning("No symbol table available for hash-based change detection")
            return {}
        
        changed_files = {}
        
        # Get stored file metadata
        stored_metadata = self._get_stored_metadata()
        
        # Scan current files
        current_files = self._scan_files(root_path, file_extensions)
        
        # Compare hashes
        for file_path, current_hash in current_files.items():
            if file_path not in stored_metadata:
                # New file
                changed_files[file_path] = "added"
            elif stored_metadata[file_path] != current_hash:
                # Modified file
                changed_files[file_path] = "modified"
        
        # Check for deleted files
        for file_path in stored_metadata:
            if file_path not in current_files:
                changed_files[file_path] = "deleted"
        
        logger.info(f"Hash-based detection found {len(changed_files)} changed files")
        return changed_files
    
    def get_current_ref(self) -> str:
        """Return current timestamp as reference."""
        return datetime.utcnow().isoformat()
    
    def get_all_files(
        self, root_path: Path, file_extensions: Optional[Set[str]] = None
    ) -> List[str]:
        """Get all files in the directory."""
        current_files = self._scan_files(root_path, file_extensions)
        return list(current_files.keys())
    
    def _get_stored_metadata(self) -> Dict[str, str]:
        """Get stored file hashes from symbol table."""
        if not self.symbol_table:
            return {}
        
        metadata = {}
        cursor = self.symbol_table.conn.execute(
            "SELECT file_path, file_hash FROM file_metadata WHERE file_hash IS NOT NULL"
        )
        for row in cursor:
            metadata[row[0]] = row[1]
        
        return metadata
    
    def _scan_files(
        self, root_path: Path, file_extensions: Optional[Set[str]] = None
    ) -> Dict[str, str]:
        """
        Scan directory and compute file hashes.
        
        Returns:
            Dictionary mapping relative file paths to their MD5 hashes
        """
        file_hashes = {}
        
        for file_path in root_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Filter by extension
            if file_extensions and file_path.suffix not in file_extensions:
                continue
            
            # Skip hidden files and common ignore patterns
            if any(part.startswith('.') for part in file_path.parts):
                continue
            if any(part in ('node_modules', '__pycache__', 'venv', '.git') for part in file_path.parts):
                continue
            
            # Compute hash
            try:
                file_hash = self._compute_file_hash(file_path)
                relative_path = str(file_path.relative_to(root_path))
                file_hashes[relative_path] = file_hash
            except Exception as e:
                logger.warning(f"Failed to hash {file_path}: {e}")
        
        return file_hashes
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of file content."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()


class UnifiedChangeDetector:
    """
    Unified change detector that automatically chooses the best strategy.
    
    Prefers Git-based detection when available, falls back to hash-based detection.
    """
    
    def __init__(
        self,
        repo_path: Path,
        symbol_table: Optional[SymbolTable] = None,
        force_strategy: Optional[str] = None,
    ):
        """
        Initialize unified change detector.
        
        Args:
            repo_path: Path to repository/codebase root
            symbol_table: Optional symbol table for hash-based fallback
            force_strategy: Force specific strategy ('git' or 'hash'), None for auto-detect
        """
        self.repo_path = repo_path
        self.symbol_table = symbol_table
        
        # Auto-detect or force strategy
        if force_strategy == 'git':
            self.strategy = GitStrategy(repo_path)
            self.strategy_name = 'git'
            logger.info("Using Git-based change detection (forced)")
        elif force_strategy == 'hash':
            self.strategy = HashStrategy(symbol_table)
            self.strategy_name = 'hash'
            logger.info("Using hash-based change detection (forced)")
        else:
            # Auto-detect
            if GitChangeDetector.is_git_repository(repo_path):
                self.strategy = GitStrategy(repo_path)
                self.strategy_name = 'git'
                logger.info("Using Git-based change detection (auto-detected)")
            else:
                self.strategy = HashStrategy(symbol_table)
                self.strategy_name = 'hash'
                logger.info("Using hash-based change detection (no Git repository)")
    
    def get_changed_files(
        self,
        last_indexed_ref: Optional[str],
        file_extensions: Optional[Set[str]] = None,
    ) -> Dict[str, str]:
        """Get changed files since last indexing."""
        return self.strategy.get_changed_files(
            self.repo_path, last_indexed_ref, file_extensions
        )
    
    def get_current_ref(self) -> str:
        """Get current reference (commit hash or timestamp)."""
        return self.strategy.get_current_ref()
    
    def get_all_files(self, file_extensions: Optional[Set[str]] = None) -> List[str]:
        """Get all tracked/indexed files."""
        return self.strategy.get_all_files(self.repo_path, file_extensions)
    
    def is_git_based(self) -> bool:
        """Check if using Git-based strategy."""
        return self.strategy_name == 'git'
    
    def is_hash_based(self) -> bool:
        """Check if using hash-based strategy."""
        return self.strategy_name == 'hash'

