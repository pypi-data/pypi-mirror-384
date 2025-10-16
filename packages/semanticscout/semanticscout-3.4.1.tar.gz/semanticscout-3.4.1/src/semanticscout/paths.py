"""
Centralized path management for SemanticScout.

This module provides a single source of truth for all file system paths used by SemanticScout.
All data, configuration, and logs are stored under ~/semanticscout on all platforms (Windows, macOS, Linux).

Directory Structure:
    ~/semanticscout/
    ├── config/              # Configuration files
    │   └── enhancement_config.json
    ├── data/                # Application data
    │   ├── chroma_db/       # Vector store database
    │   ├── symbol_tables/   # Symbol table SQLite databases
    │   ├── dependency_graphs/  # Dependency graph pickle files
    │   └── ast_cache/       # AST parsing cache
    ├── models/              # Cached embedding models
    └── logs/                # Log files
        └── mcp_server.log

Platform-specific paths:
    - Windows: C:\\Users\\YourName\\semanticscout
    - macOS: /Users/yourname/semanticscout
    - Linux: /home/yourname/semanticscout
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PathManager:
    """
    Manages all file system paths for SemanticScout.
    
    This class provides centralized path resolution for all SemanticScout components,
    ensuring consistent directory structure across all platforms.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the path manager.
        
        Args:
            base_dir: Optional base directory override. If None, uses ~/semanticscout.
                     This parameter exists primarily for testing purposes.
        """
        if base_dir is None:
            self._base_dir = Path.home() / "semanticscout"
        else:
            self._base_dir = Path(base_dir)
    
    def get_app_root(self) -> Path:
        """
        Get the application root directory.
        
        Returns:
            Path to ~/semanticscout (or override if set)
        """
        return self._base_dir
    
    def get_config_dir(self) -> Path:
        """
        Get the configuration directory.
        
        Returns:
            Path to ~/semanticscout/config
        """
        return self._base_dir / "config"
    
    def get_data_dir(self) -> Path:
        """
        Get the data directory.
        
        Returns:
            Path to ~/semanticscout/data
        """
        return self._base_dir / "data"
    
    def get_logs_dir(self) -> Path:
        """
        Get the logs directory.
        
        Returns:
            Path to ~/semanticscout/logs
        """
        return self._base_dir / "logs"
    
    def get_vector_store_dir(self) -> Path:
        """
        Get the vector store directory.
        
        Returns:
            Path to ~/semanticscout/data/chroma_db
        """
        return self.get_data_dir() / "chroma_db"
    
    def get_symbol_tables_dir(self) -> Path:
        """
        Get the symbol tables directory.
        
        Returns:
            Path to ~/semanticscout/data/symbol_tables
        """
        return self.get_data_dir() / "symbol_tables"
    
    def get_dependency_graphs_dir(self) -> Path:
        """
        Get the dependency graphs directory.
        
        Returns:
            Path to ~/semanticscout/data/dependency_graphs
        """
        return self.get_data_dir() / "dependency_graphs"
    
    def get_ast_cache_dir(self) -> Path:
        """
        Get the AST cache directory.

        Returns:
            Path to ~/semanticscout/data/ast_cache
        """
        return self.get_data_dir() / "ast_cache"

    def get_models_dir(self) -> Path:
        """
        Get the models directory.

        Returns:
            Path to ~/semanticscout/models
        """
        return self._base_dir / "models"
    
    def ensure_directories(self) -> None:
        """
        Create all required directories if they don't exist.
        
        This method is called automatically during module initialization.
        It creates the entire directory structure with appropriate permissions.
        
        Raises:
            OSError: If directories cannot be created (e.g., permission denied)
        """
        directories = [
            self.get_app_root(),
            self.get_config_dir(),
            self.get_data_dir(),
            self.get_logs_dir(),
            self.get_vector_store_dir(),
            self.get_symbol_tables_dir(),
            self.get_dependency_graphs_dir(),
            self.get_ast_cache_dir(),
            self.get_models_dir(),
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                raise
    
    def get_info(self) -> dict:
        """
        Get information about all managed paths.
        
        Returns:
            Dictionary with path information for debugging/logging
        """
        return {
            "app_root": str(self.get_app_root()),
            "config_dir": str(self.get_config_dir()),
            "data_dir": str(self.get_data_dir()),
            "logs_dir": str(self.get_logs_dir()),
            "vector_store_dir": str(self.get_vector_store_dir()),
            "symbol_tables_dir": str(self.get_symbol_tables_dir()),
            "dependency_graphs_dir": str(self.get_dependency_graphs_dir()),
            "ast_cache_dir": str(self.get_ast_cache_dir()),
            "models_dir": str(self.get_models_dir()),
        }


# Global singleton instance
path_manager = PathManager()

# Ensure all directories exist on module import
try:
    path_manager.ensure_directories()
    logger.info(f"SemanticScout paths initialized: {path_manager.get_app_root()}")
except OSError as e:
    logger.error(f"Failed to initialize SemanticScout directories: {e}")
    logger.error("Please ensure you have write permissions to your home directory")
    raise


# Convenience function for getting the singleton
def get_path_manager() -> PathManager:
    """
    Get the global path manager instance.
    
    Returns:
        The global PathManager singleton
    """
    return path_manager


if __name__ == "__main__":
    # Test/demo the path manager
    print("SemanticScout Path Manager")
    print("=" * 60)
    print("\nDirectory Structure:")
    print("-" * 60)
    
    info = path_manager.get_info()
    for key, value in info.items():
        print(f"{key:25s}: {value}")
    
    print("\n" + "=" * 60)
    print("All directories have been created and are ready to use.")

