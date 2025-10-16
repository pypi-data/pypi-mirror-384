"""
Configuration management for SemanticScout enhancements.

This module provides both the new enhancement configuration system
and backward compatibility with the old config module.
"""

# New enhancement configuration
from .enhancement_config import (
    EnhancementConfig,
    ASTProcessingConfig,
    SymbolTableConfig,
    DependencyGraphConfig,
    QueryProcessingConfig,
    PerformanceConfig,
    LoggingConfig,
    ConfigurationManager,
    get_config_manager,
    get_enhancement_config,
    is_feature_enabled,
)

__all__ = [
    # New enhancement config
    "EnhancementConfig",
    "ASTProcessingConfig",
    "SymbolTableConfig",
    "DependencyGraphConfig",
    "QueryProcessingConfig",
    "PerformanceConfig",
    "LoggingConfig",
    "ConfigurationManager",
    "get_config_manager",
    "get_enhancement_config",
    "is_feature_enabled",
]
