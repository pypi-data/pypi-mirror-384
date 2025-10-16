"""
Configuration management for SemanticScout enhancements.

This module handles loading, validation, and management of enhancement settings
including AST processing, symbol tables, dependency graphs, and performance tuning.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Import path manager for standardized paths
from semanticscout.paths import path_manager

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding provider and model."""
    provider: str = "sentence-transformers"  # "ollama", "openai", or "sentence-transformers"
    model: str = "all-MiniLM-L6-v2"  # Model name for the selected provider


@dataclass
class ASTProcessingConfig:
    """Configuration for AST processing features."""
    enabled: bool = True
    languages: List[str] = field(default_factory=lambda: [
        "c", "cpp", "python", "javascript", "typescript", "go", "rust", "java"
    ])
    file_extensions: List[str] = field(default_factory=lambda: [
        ".c", ".h", ".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".hh",
        ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java"
    ])
    cache_parsed_trees: bool = True
    cache_ttl_hours: int = 24
    parallel_processing: bool = True
    max_workers: int = 4
    max_file_size_mb: int = 10
    skip_node_modules: bool = True
    skip_test_files: bool = False


@dataclass
class SymbolTableConfig:
    """Configuration for symbol table features."""
    enabled: bool = True
    database_type: str = "sqlite"
    database_path: str = field(default_factory=lambda: str(path_manager.get_symbol_tables_dir() / "{collection_id}.db"))
    index_all_symbols: bool = True
    include_private_symbols: bool = False
    include_documentation: bool = True
    fuzzy_matching: bool = True
    fts_enabled: bool = True


@dataclass
class DependencyGraphConfig:
    """Configuration for dependency graph features."""
    enabled: bool = True
    max_depth: int = 10
    include_external_deps: bool = False
    detect_circular_deps: bool = True
    cache_graphs: bool = True
    graph_format: str = "networkx"
    enable_symbol_dependencies: bool = True


@dataclass
class QueryProcessingConfig:
    """Configuration for query processing features."""
    default_strategy: str = "auto"
    enable_intent_detection: bool = True
    intent_confidence_threshold: float = 0.7
    max_hybrid_results: int = 20
    dependency_expansion_limit: int = 5
    context_expansion_enabled: bool = True


@dataclass
class PerformanceConfig:
    """Configuration for performance settings."""
    max_memory_mb: int = 1024
    query_timeout_seconds: int = 30
    indexing_batch_size: int = 50
    enable_result_caching: bool = True
    cache_size_mb: int = 256
    enable_metrics: bool = True


@dataclass
class LoggingConfig:
    """Configuration for logging settings."""
    level: str = "INFO"
    enable_performance_logging: bool = True
    enable_query_logging: bool = True
    log_file: str = field(default_factory=lambda: str(path_manager.get_logs_dir() / "semanticscout_enhanced.log"))


@dataclass
class EnhancementConfig:
    """Main configuration class for all enhancements."""
    version: str = "2.0"
    enabled: bool = True
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    ast_processing: ASTProcessingConfig = field(default_factory=ASTProcessingConfig)
    symbol_table: SymbolTableConfig = field(default_factory=SymbolTableConfig)
    dependency_graph: DependencyGraphConfig = field(default_factory=DependencyGraphConfig)
    query_processing: QueryProcessingConfig = field(default_factory=QueryProcessingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigurationManager:
    """Manages loading, validation, and access to enhancement configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default locations.
        """
        self.config_path = self._resolve_config_path(config_path)
        self.config: Optional[EnhancementConfig] = None
        self._load_config()
    
    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """
        Resolve configuration file path.

        Always uses ~/semanticscout/config/enhancement_config.json unless explicitly overridden.
        The config_path parameter exists primarily for testing purposes.
        """
        if config_path:
            return Path(config_path)

        # Always use standardized path
        return path_manager.get_config_dir() / "enhancement_config.json"

    def _create_default_config_file(self) -> None:
        """
        Create default configuration file with all default values.

        This is called automatically when no config file exists.
        """
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert config to dictionary
            config_dict = {
                "version": self.config.version,
                "enabled": self.config.enabled,
                "embedding": {
                    "provider": self.config.embedding.provider,
                    "model": self.config.embedding.model
                },
                "ast_processing": {
                    "enabled": self.config.ast_processing.enabled,
                    "languages": self.config.ast_processing.languages,
                    "file_extensions": self.config.ast_processing.file_extensions,
                    "cache_parsed_trees": self.config.ast_processing.cache_parsed_trees,
                    "cache_ttl_hours": self.config.ast_processing.cache_ttl_hours,
                    "parallel_processing": self.config.ast_processing.parallel_processing,
                    "max_workers": self.config.ast_processing.max_workers,
                    "max_file_size_mb": self.config.ast_processing.max_file_size_mb,
                    "skip_node_modules": self.config.ast_processing.skip_node_modules,
                    "skip_test_files": self.config.ast_processing.skip_test_files
                },
                "symbol_table": {
                    "enabled": self.config.symbol_table.enabled,
                    "database_type": self.config.symbol_table.database_type,
                    "database_path": self.config.symbol_table.database_path,
                    "index_all_symbols": self.config.symbol_table.index_all_symbols,
                    "include_private_symbols": self.config.symbol_table.include_private_symbols,
                    "include_documentation": self.config.symbol_table.include_documentation,
                    "fuzzy_matching": self.config.symbol_table.fuzzy_matching,
                    "fts_enabled": self.config.symbol_table.fts_enabled
                },
                "dependency_graph": {
                    "enabled": self.config.dependency_graph.enabled,
                    "max_depth": self.config.dependency_graph.max_depth,
                    "include_external_deps": self.config.dependency_graph.include_external_deps,
                    "detect_circular_deps": self.config.dependency_graph.detect_circular_deps,
                    "cache_graphs": self.config.dependency_graph.cache_graphs,
                    "graph_format": self.config.dependency_graph.graph_format,
                    "enable_symbol_dependencies": self.config.dependency_graph.enable_symbol_dependencies
                },
                "query_processing": {
                    "default_strategy": self.config.query_processing.default_strategy,
                    "enable_intent_detection": self.config.query_processing.enable_intent_detection,
                    "intent_confidence_threshold": self.config.query_processing.intent_confidence_threshold,
                    "max_hybrid_results": self.config.query_processing.max_hybrid_results,
                    "dependency_expansion_limit": self.config.query_processing.dependency_expansion_limit,
                    "context_expansion_enabled": self.config.query_processing.context_expansion_enabled
                },
                "performance": {
                    "max_memory_mb": self.config.performance.max_memory_mb,
                    "query_timeout_seconds": self.config.performance.query_timeout_seconds,
                    "indexing_batch_size": self.config.performance.indexing_batch_size,
                    "enable_result_caching": self.config.performance.enable_result_caching,
                    "cache_size_mb": self.config.performance.cache_size_mb,
                    "enable_metrics": self.config.performance.enable_metrics
                },
                "logging": {
                    "level": self.config.logging.level,
                    "enable_performance_logging": self.config.logging.enable_performance_logging,
                    "enable_query_logging": self.config.logging.enable_query_logging,
                    "log_file": self.config.logging.log_file
                }
            }

            # Write to file with nice formatting
            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)

            logger.info(f"Created default configuration file at {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to create default configuration file: {e}")
            logger.info("Continuing with in-memory defaults")

    def _load_config(self) -> None:
        """Load configuration from file with environment variable overrides."""
        try:
            # Start with file-based config or defaults
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)

                # Extract enhancement_config section if it exists
                if "enhancement_config" in config_data:
                    config_data = config_data["enhancement_config"]

                self.config = self._create_config_from_dict(config_data)
                logger.info(f"Loaded base configuration from {self.config_path}")
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                self.config = EnhancementConfig()
                logger.info("Using default configuration")

                # Auto-create config file with defaults
                self._create_default_config_file()

            # Merge with SEMANTICSCOUT_CONFIG_JSON if provided (overrides file config)
            config_json = os.getenv("SEMANTICSCOUT_CONFIG_JSON")
            if config_json:
                try:
                    env_config_data = json.loads(config_json)
                    # Merge environment config into existing config
                    self._merge_config_dict(env_config_data)
                    logger.info("Merged configuration from SEMANTICSCOUT_CONFIG_JSON environment variable")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in SEMANTICSCOUT_CONFIG_JSON: {e}")

            # Apply environment variable overrides (these take precedence)
            self._apply_env_overrides()

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.info("Using default configuration")
            self.config = EnhancementConfig()
    
    def _merge_config_dict(self, data: Dict[str, Any]) -> None:
        """
        Merge configuration dictionary into existing config.

        This allows environment variable config to override file config
        without completely replacing it.

        Args:
            data: Configuration dictionary to merge
        """
        if not self.config:
            self.config = EnhancementConfig()

        # Update main config fields
        if "version" in data:
            self.config.version = data["version"]
        if "enabled" in data:
            self.config.enabled = data["enabled"]

        # Merge nested configurations (only update provided fields)
        if "ast_processing" in data:
            self.config.ast_processing = self._update_dataclass(
                self.config.ast_processing, data["ast_processing"]
            )

        if "symbol_table" in data:
            self.config.symbol_table = self._update_dataclass(
                self.config.symbol_table, data["symbol_table"]
            )

        if "dependency_graph" in data:
            self.config.dependency_graph = self._update_dataclass(
                self.config.dependency_graph, data["dependency_graph"]
            )

        if "query_processing" in data:
            self.config.query_processing = self._update_dataclass(
                self.config.query_processing, data["query_processing"]
            )

        if "performance" in data:
            self.config.performance = self._update_dataclass(
                self.config.performance, data["performance"]
            )

        if "logging" in data:
            self.config.logging = self._update_dataclass(
                self.config.logging, data["logging"]
            )

    def _create_config_from_dict(self, data: Dict[str, Any]) -> EnhancementConfig:
        """Create configuration object from dictionary data."""
        config = EnhancementConfig()
        
        # Update main config fields
        if "version" in data:
            config.version = data["version"]
        if "enabled" in data:
            config.enabled = data["enabled"]

        # Update nested configurations
        if "embedding" in data:
            config.embedding = self._update_dataclass(
                config.embedding, data["embedding"]
            )

        if "ast_processing" in data:
            config.ast_processing = self._update_dataclass(
                config.ast_processing, data["ast_processing"]
            )
        
        if "symbol_table" in data:
            config.symbol_table = self._update_dataclass(
                config.symbol_table, data["symbol_table"]
            )
        
        if "dependency_graph" in data:
            config.dependency_graph = self._update_dataclass(
                config.dependency_graph, data["dependency_graph"]
            )

        if "query_processing" in data:
            config.query_processing = self._update_dataclass(
                config.query_processing, data["query_processing"]
            )
        
        if "performance" in data:
            config.performance = self._update_dataclass(
                config.performance, data["performance"]
            )
        
        if "logging" in data:
            config.logging = self._update_dataclass(
                config.logging, data["logging"]
            )
        
        return config
    
    def _update_dataclass(self, instance: Any, data: Dict[str, Any]) -> Any:
        """Update dataclass instance with dictionary data."""
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        if not self.config:
            return

        # Main enhancement toggle
        if os.getenv("SEMANTICSCOUT_ENABLE_ENHANCEMENTS"):
            self.config.enabled = os.getenv("SEMANTICSCOUT_ENABLE_ENHANCEMENTS").lower() == "true"

        # AST processing overrides
        if os.getenv("SEMANTICSCOUT_ENABLE_AST"):
            self.config.ast_processing.enabled = os.getenv("SEMANTICSCOUT_ENABLE_AST").lower() == "true"

        if os.getenv("SEMANTICSCOUT_PARALLEL_WORKERS"):
            try:
                self.config.ast_processing.max_workers = int(os.getenv("SEMANTICSCOUT_PARALLEL_WORKERS"))
            except ValueError:
                logger.warning("Invalid SEMANTICSCOUT_PARALLEL_WORKERS value, using default")

        if os.getenv("SEMANTICSCOUT_MAX_FILE_SIZE_MB"):
            try:
                self.config.ast_processing.max_file_size_mb = int(os.getenv("SEMANTICSCOUT_MAX_FILE_SIZE_MB"))
            except ValueError:
                logger.warning("Invalid SEMANTICSCOUT_MAX_FILE_SIZE_MB value, using default")

        # Symbol table overrides
        if os.getenv("SEMANTICSCOUT_ENABLE_SYMBOLS"):
            self.config.symbol_table.enabled = os.getenv("SEMANTICSCOUT_ENABLE_SYMBOLS").lower() == "true"

        # Dependency graph overrides
        if os.getenv("SEMANTICSCOUT_ENABLE_DEPENDENCIES"):
            self.config.dependency_graph.enabled = os.getenv("SEMANTICSCOUT_ENABLE_DEPENDENCIES").lower() == "true"

        # Performance overrides
        if os.getenv("SEMANTICSCOUT_MAX_MEMORY_MB"):
            try:
                self.config.performance.max_memory_mb = int(os.getenv("SEMANTICSCOUT_MAX_MEMORY_MB"))
            except ValueError:
                logger.warning("Invalid SEMANTICSCOUT_MAX_MEMORY_MB value, using default")

        if os.getenv("SEMANTICSCOUT_QUERY_TIMEOUT"):
            try:
                self.config.performance.query_timeout_seconds = int(os.getenv("SEMANTICSCOUT_QUERY_TIMEOUT"))
            except ValueError:
                logger.warning("Invalid SEMANTICSCOUT_QUERY_TIMEOUT value, using default")

        if os.getenv("SEMANTICSCOUT_BATCH_SIZE"):
            try:
                self.config.performance.indexing_batch_size = int(os.getenv("SEMANTICSCOUT_BATCH_SIZE"))
            except ValueError:
                logger.warning("Invalid SEMANTICSCOUT_BATCH_SIZE value, using default")

        if os.getenv("SEMANTICSCOUT_CACHE_SIZE_MB"):
            try:
                self.config.performance.cache_size_mb = int(os.getenv("SEMANTICSCOUT_CACHE_SIZE_MB"))
            except ValueError:
                logger.warning("Invalid SEMANTICSCOUT_CACHE_SIZE_MB value, using default")
    
    def get_config(self) -> EnhancementConfig:
        """Get the current configuration."""
        if self.config is None:
            self.config = EnhancementConfig()
        return self.config
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a specific feature is enabled."""
        if not self.config or not self.config.enabled:
            return False
        
        feature_map = {
            "ast_processing": self.config.ast_processing.enabled,
            "symbol_table": self.config.symbol_table.enabled,
            "dependency_graph": self.config.dependency_graph.enabled,
            "query_processing": True,  # Always enabled if enhancements are enabled
            "performance": True,  # Always enabled if enhancements are enabled
        }
        
        return feature_map.get(feature, False)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        if not self.config:
            issues.append("Configuration not loaded")
            return issues
        
        # Validate AST processing config
        if self.config.ast_processing.enabled:
            if self.config.ast_processing.max_workers < 1:
                issues.append("AST processing max_workers must be >= 1")
            
            if self.config.ast_processing.max_file_size_mb < 1:
                issues.append("AST processing max_file_size_mb must be >= 1")
        
        # Validate performance config
        if self.config.performance.max_memory_mb < 256:
            issues.append("Performance max_memory_mb should be >= 256MB")
        
        if self.config.performance.query_timeout_seconds < 1:
            issues.append("Performance query_timeout_seconds must be >= 1")
        
        # Validate paths
        symbol_db_path = Path(self.config.symbol_table.database_path.replace("{collection_id}", "test"))
        if not symbol_db_path.parent.exists():
            issues.append(f"Symbol table directory does not exist: {symbol_db_path.parent}")
        
        return issues


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def get_enhancement_config() -> EnhancementConfig:
    """Get the current enhancement configuration."""
    return get_config_manager().get_config()


def is_feature_enabled(feature: str) -> bool:
    """Check if a specific enhancement feature is enabled."""
    return get_config_manager().is_feature_enabled(feature)
