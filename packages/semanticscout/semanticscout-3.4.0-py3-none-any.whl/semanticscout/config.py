"""
Configuration management for the MCP server.
"""

import os
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Import path manager for standardized paths
from semanticscout.paths import path_manager

# Import enhancement config for embedding configuration
from semanticscout.config.enhancement_config import get_enhancement_config

logger = logging.getLogger(__name__)

# Import version from package
try:
    from semanticscout import __version__
except ImportError:
    __version__ = "2.2.1"  # Fallback if import fails


@dataclass
class ServerConfig:
    """Configuration for the MCP server."""

    # Embedding provider settings
    embedding_provider: str = "sentence-transformers"  # "ollama", "openai", or "sentence-transformers" (DEFAULT: sentence-transformers)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "nomic-embed-text"
    openai_api_key: Optional[str] = None
    openai_model: str = "text-embedding-3-small"
    sentence_transformers_model: str = "all-mpnet-base-v2"  # NEW: for sentence-transformers provider
    embedding_dimensions: int = 768  # 768 for nomic-embed-text and all-mpnet-base-v2, 384 for all-MiniLM-L6-v2, 1536 for openai
    lazy_loading: bool = True  # NEW: Enable lazy loading for faster startup (default: True)

    # GPU and device settings
    device_preference: str = "auto"  # "auto", "cuda", "cpu", "cuda:0", etc.
    gpu_batch_size: int = 64  # Batch size for GPU processing (higher for better GPU utilization)
    cpu_batch_size: int = 16  # Batch size for CPU processing (lower to avoid memory issues)
    gpu_memory_monitoring: bool = False  # Enable GPU memory usage monitoring and logging

    # Vector store settings
    vector_store_path: str = field(default_factory=lambda: str(path_manager.get_vector_store_dir()))

    # Code chunking settings
    chunk_size_min: int = 500
    chunk_size_max: int = 3000  # UPDATED: increased from 1500 to 3000
    chunk_overlap: int = 50

    # Context expansion settings (NEW)
    context_expansion_enabled: bool = True
    default_expansion_level: str = "medium"  # 'none', 'low', 'medium', 'high'
    max_expansion_radius: int = 5  # Max number of neighboring chunks to retrieve
    include_file_context: bool = True  # Include file-level chunks in expansion
    include_import_context: bool = True  # Include imported modules in expansion
    max_result_length: int = 5000  # Max characters per search result (was 500)

    # Resource limits
    max_codebase_size_gb: float = 10.0
    max_file_size_mb: float = 10.0
    max_files: int = 100000

    # Rate limiting
    max_indexing_requests_per_hour: int = 10
    max_search_requests_per_minute: int = 100

    # Logging settings
    log_level: str = "INFO"
    log_file: str = field(default_factory=lambda: str(path_manager.get_logs_dir() / "mcp_server.log"))

    # Server settings
    server_name: str = "semanticscout"
    server_version: str = "1.0.0"

    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()

    def validate(self):
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate embedding provider (FIXED: added sentence-transformers)
        if self.embedding_provider not in ["ollama", "openai", "sentence-transformers"]:
            raise ValueError(
                f"Invalid embedding_provider: {self.embedding_provider}. "
                "Must be 'ollama', 'openai', or 'sentence-transformers'"
            )

        # Validate OpenAI API key if using OpenAI
        if self.embedding_provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "openai_api_key is required when using OpenAI embedding provider"
            )

        # Validate chunk sizes
        if self.chunk_size_min < 100:
            raise ValueError("chunk_size_min must be at least 100")

        if self.chunk_size_max < self.chunk_size_min:
            raise ValueError("chunk_size_max must be >= chunk_size_min")

        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")

        # Validate resource limits
        if self.max_codebase_size_gb <= 0:
            raise ValueError("max_codebase_size_gb must be > 0")

        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be > 0")

        if self.max_files <= 0:
            raise ValueError("max_files must be > 0")

        # Validate rate limits
        if self.max_indexing_requests_per_hour <= 0:
            raise ValueError("max_indexing_requests_per_hour must be > 0")

        if self.max_search_requests_per_minute <= 0:
            raise ValueError("max_search_requests_per_minute must be > 0")

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"Invalid log_level: {self.log_level}. "
                f"Must be one of {valid_log_levels}"
            )

        # Validate embedding dimensions
        if self.embedding_dimensions <= 0:
            raise ValueError("embedding_dimensions must be > 0")

        # Validate context expansion settings (NEW)
        valid_expansion_levels = ["none", "low", "medium", "high"]
        if self.default_expansion_level not in valid_expansion_levels:
            raise ValueError(
                f"Invalid default_expansion_level: {self.default_expansion_level}. "
                f"Must be one of {valid_expansion_levels}"
            )

        if self.max_expansion_radius < 0:
            raise ValueError("max_expansion_radius must be >= 0")

        if self.max_result_length < 100:
            raise ValueError("max_result_length must be at least 100")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "embedding_provider": self.embedding_provider,
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "openai_model": self.openai_model,
            "embedding_dimensions": self.embedding_dimensions,
            "vector_store_path": self.vector_store_path,
            "chunk_size_min": self.chunk_size_min,
            "chunk_size_max": self.chunk_size_max,
            "chunk_overlap": self.chunk_overlap,
            # NEW: Context expansion settings
            "context_expansion_enabled": self.context_expansion_enabled,
            "default_expansion_level": self.default_expansion_level,
            "max_expansion_radius": self.max_expansion_radius,
            "include_file_context": self.include_file_context,
            "include_import_context": self.include_import_context,
            "max_result_length": self.max_result_length,
            # END NEW
            "max_codebase_size_gb": self.max_codebase_size_gb,
            "max_file_size_mb": self.max_file_size_mb,
            "max_files": self.max_files,
            "max_indexing_requests_per_hour": self.max_indexing_requests_per_hour,
            "max_search_requests_per_minute": self.max_search_requests_per_minute,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "server_name": self.server_name,
            "server_version": self.server_version,
        }


def load_config(env_file: Optional[str] = None) -> ServerConfig:
    """
    Load configuration from environment variables.

    Args:
        env_file: Path to .env file (default: .env in current directory)

    Returns:
        ServerConfig instance

    Raises:
        ValueError: If configuration is invalid
    """
    # Load .env file if it exists
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()  # Load from .env in current directory

    # Load enhancement config first (base layer)
    try:
        enhancement_config = get_enhancement_config()
        base_embedding_config = {
            "provider": enhancement_config.embedding.provider,
            "model": enhancement_config.embedding.model
        }
        logger.info(f"Loaded base embedding config from enhancement_config.json: {base_embedding_config}")
        logger.info(f"Enhancement config file path: {enhancement_config.config_path if hasattr(enhancement_config, 'config_path') else 'unknown'}")
    except Exception as e:
        logger.warning(f"Failed to load enhancement config: {e}. Using defaults.")
        base_embedding_config = {
            "provider": "sentence-transformers",
            "model": "all-MiniLM-L6-v2"
        }

    # Parse SEMANTICSCOUT_CONFIG_JSON if present (overrides enhancement config)
    embedding_config = base_embedding_config.copy()  # Start with enhancement config
    config_json = os.getenv("SEMANTICSCOUT_CONFIG_JSON")
    if config_json:
        try:
            logger.info(f"SEMANTICSCOUT_CONFIG_JSON content: {config_json[:200]}...")  # Log first 200 chars
            config_data = json.loads(config_json)
            env_embedding = config_data.get("embedding", {})
            if env_embedding:
                logger.info(f"Environment embedding config: {env_embedding}")
                embedding_config.update(env_embedding)  # Override with env config
                logger.info("Overriding embedding configuration from SEMANTICSCOUT_CONFIG_JSON")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in SEMANTICSCOUT_CONFIG_JSON: {e}")

    # Determine embedding provider (env vars take final precedence)
    provider = os.getenv("EMBEDDING_PROVIDER") or embedding_config.get("provider", "sentence-transformers")
    logger.info(f"Embedding provider: {provider}")

    # Determine model based on provider (env vars take final precedence)
    if provider == "sentence-transformers":
        # Precedence: SENTENCE_TRANSFORMERS_MODEL env var → embedding_config → default
        sentence_transformers_model = (
            os.getenv("SENTENCE_TRANSFORMERS_MODEL") or
            embedding_config.get("model", "all-MiniLM-L6-v2")
        )
        ollama_model = os.getenv("OLLAMA_MODEL", "nomic-embed-text")
        openai_model = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
        logger.info(f"Sentence-transformers model: {sentence_transformers_model}")
        logger.info(f"Final embedding config - Provider: {provider}, Model: {sentence_transformers_model}")
    elif provider == "ollama":
        # Precedence: OLLAMA_MODEL env var → embedding_config → default
        ollama_model = (
            os.getenv("OLLAMA_MODEL") or
            embedding_config.get("model", "nomic-embed-text")
        )
        sentence_transformers_model = os.getenv("SENTENCE_TRANSFORMERS_MODEL", "all-MiniLM-L6-v2")
        openai_model = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
        logger.info(f"Ollama model: {ollama_model}")
    elif provider == "openai":
        # Precedence: OPENAI_MODEL env var → embedding_config → default
        openai_model = (
            os.getenv("OPENAI_MODEL") or
            embedding_config.get("model", "text-embedding-3-small")
        )
        ollama_model = os.getenv("OLLAMA_MODEL", "nomic-embed-text")
        sentence_transformers_model = os.getenv("SENTENCE_TRANSFORMERS_MODEL", "all-MiniLM-L6-v2")
        logger.info(f"OpenAI model: {openai_model}")
    else:
        # Unknown provider, use defaults
        logger.warning(f"Unknown embedding provider: {provider}. Using defaults.")
        ollama_model = os.getenv("OLLAMA_MODEL", "nomic-embed-text")
        openai_model = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
        sentence_transformers_model = os.getenv("SENTENCE_TRANSFORMERS_MODEL", "all-MiniLM-L6-v2")

    # Create configuration from environment variables and JSON
    config = ServerConfig(
        # Embedding provider settings
        embedding_provider=provider,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=ollama_model,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=openai_model,
        sentence_transformers_model=sentence_transformers_model,
        embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "768")),
        lazy_loading=os.getenv("LAZY_LOADING", "true").lower() == "true",
        # GPU and device settings
        device_preference=os.getenv("DEVICE_PREFERENCE", "auto"),
        gpu_batch_size=int(os.getenv("GPU_BATCH_SIZE", "64")),
        cpu_batch_size=int(os.getenv("CPU_BATCH_SIZE", "16")),
        gpu_memory_monitoring=os.getenv("GPU_MEMORY_MONITORING", "false").lower() == "true",
        # Vector store settings
        vector_store_path=os.getenv("VECTOR_STORE_PATH", str(path_manager.get_vector_store_dir())),
        # Code chunking settings
        chunk_size_min=int(os.getenv("CHUNK_SIZE_MIN", "500")),
        chunk_size_max=int(os.getenv("CHUNK_SIZE_MAX", "3000")),  # UPDATED: 1500 -> 3000
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
        # Context expansion settings (NEW)
        context_expansion_enabled=os.getenv("CONTEXT_EXPANSION_ENABLED", "true").lower() == "true",
        default_expansion_level=os.getenv("DEFAULT_EXPANSION_LEVEL", "medium"),
        max_expansion_radius=int(os.getenv("MAX_EXPANSION_RADIUS", "5")),
        include_file_context=os.getenv("INCLUDE_FILE_CONTEXT", "true").lower() == "true",
        include_import_context=os.getenv("INCLUDE_IMPORT_CONTEXT", "true").lower() == "true",
        max_result_length=int(os.getenv("MAX_RESULT_LENGTH", "5000")),
        # Resource limits
        max_codebase_size_gb=float(os.getenv("MAX_CODEBASE_SIZE_GB", "10.0")),
        max_file_size_mb=float(os.getenv("MAX_FILE_SIZE_MB", "10.0")),
        max_files=int(os.getenv("MAX_FILES", "100000")),
        # Rate limiting
        max_indexing_requests_per_hour=int(
            os.getenv("MAX_INDEXING_REQUESTS_PER_HOUR", "10")
        ),
        max_search_requests_per_minute=int(
            os.getenv("MAX_SEARCH_REQUESTS_PER_MINUTE", "100")
        ),
        # Logging settings
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", str(path_manager.get_logs_dir() / "mcp_server.log")),
        # Server settings
        server_name=os.getenv("SERVER_NAME", "semanticscout"),
        server_version=os.getenv("SERVER_VERSION", __version__),
    )

    return config


# Example usage
if __name__ == "__main__":
    # Load configuration
    config = load_config()

    # Print configuration
    print("Configuration:")
    print("-" * 60)
    for key, value in config.to_dict().items():
        # Hide API key
        if "api_key" in key.lower() and value:
            value = "***HIDDEN***"
        print(f"{key}: {value}")
    print("-" * 60)


