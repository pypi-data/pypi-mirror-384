"""
MCP Server for codebase indexing and retrieval.

This server exposes indexing and retrieval functionality as MCP tools
that AI agents can use to understand codebases.
"""

import sys
import os
import signal
from typing import Optional, List
from mcp.server.fastmcp import FastMCP

# Import path manager FIRST to ensure directories exist
from semanticscout.paths import path_manager

# Import logging configuration
from semanticscout.logging_config import setup_logging, get_logger

# Import from config.py module (not config/ package)
import importlib.util
import sys
from pathlib import Path

# Load config.py module directly to avoid shadowing by config/ package
config_module_path = Path(__file__).parent / "config.py"
spec = importlib.util.spec_from_file_location("semanticscout_config_module", config_module_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
load_config = config_module.load_config
ServerConfig = config_module.ServerConfig

from semanticscout import __version__
from semanticscout.embeddings.ollama_provider import OllamaEmbeddingProvider
from semanticscout.embeddings import SentenceTransformerProvider  # NEW
from semanticscout.embeddings.base import EmbeddingProvider
from semanticscout.vector_store.chroma_store import ChromaVectorStore
from semanticscout.indexer.file_discovery import FileDiscovery
from semanticscout.indexer.code_chunker import ASTCodeChunker
from semanticscout.indexer.pipeline import IndexingPipeline
from semanticscout.retriever.query_processor import QueryProcessor
from semanticscout.retriever.semantic_search import SemanticSearcher
from semanticscout.retriever.context_expander import ContextExpander
from semanticscout.retriever.hybrid_retriever import HybridRetriever  # NEW
from semanticscout.symbol_table.symbol_table import SymbolTable, SymbolTableManager  # NEW
from semanticscout.dependency_graph.dependency_graph import DependencyGraph, DependencyGraphManager  # NEW
from semanticscout.query_analysis.query_analyzer import QueryAnalyzer  # NEW
from semanticscout.config import get_enhancement_config  # NEW from config/ package
from semanticscout.security.validators import (
    PathValidator,
    InputValidator,
    RateLimiter,
    ValidationError,
)
from semanticscout.indexer.file_change_events import (  # NEW
    FileChangeBatch,
    FileChangeEventValidator,
    ValidationError as EventValidationError,
)
from semanticscout.indexer.change_detector import UnifiedChangeDetector  # NEW
import json  # NEW

# Get logger (will use root logger until setup_logging is called)
logger = get_logger(__name__)

# Global server state
config: Optional[ServerConfig] = None
embedding_provider: Optional[EmbeddingProvider] = None
vector_store: Optional[ChromaVectorStore] = None
query_processor: Optional[QueryProcessor] = None
semantic_searcher: Optional[SemanticSearcher] = None
context_expander: Optional[ContextExpander] = None
hybrid_retriever: Optional[HybridRetriever] = None  # NEW
symbol_table_manager: Optional[SymbolTableManager] = None  # NEW - Manager for multi-collection support
dependency_graph_manager: Optional[DependencyGraphManager] = None  # NEW - Manager for multi-collection support
query_analyzer: Optional[QueryAnalyzer] = None  # NEW
enhancement_config = None  # NEW - Enhancement configuration
path_validator: Optional[PathValidator] = None
rate_limiter: Optional[RateLimiter] = None
change_detector: Optional[UnifiedChangeDetector] = None  # NEW

# Initialize FastMCP server
mcp = FastMCP("codebase-context")


def initialize_components():
    """
    Initialize all server components.

    All data is stored in ~/semanticscout (cross-platform).

    Raises:
        Exception: If initialization fails
    """
    global config, embedding_provider, vector_store
    global query_processor, semantic_searcher
    global context_expander, hybrid_retriever, symbol_table_manager, dependency_graph_manager, query_analyzer
    global enhancement_config, path_validator, rate_limiter

    logger.info("=" * 60)
    logger.info("INITIALIZING MCP SERVER COMPONENTS")
    logger.info("=" * 60)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        logger.info(f"✓ Configuration loaded: {config.server_name} v{config.server_version}")
        logger.info(f"  Embedding provider: {config.embedding_provider}")

        # Use standardized vector store path
        vector_store_path = config.vector_store_path
        logger.info(f"  Vector store: {vector_store_path}")

        # Initialize embedding provider
        logger.info("Initializing embedding provider...")
        if config.embedding_provider == "ollama":
            embedding_provider = OllamaEmbeddingProvider(
                base_url=config.ollama_base_url,
                model=config.ollama_model,
            )
            # Check health
            if not embedding_provider.check_health():
                raise RuntimeError(
                    f"Ollama server not available at {config.ollama_base_url}. "
                    "Please start Ollama and ensure the model is available."
                )
            logger.info(f"✓ Ollama provider initialized: {config.ollama_model}")
        elif config.embedding_provider == "sentence-transformers":
            # NEW: Support for sentence-transformers provider with configurable lazy loading
            embedding_provider = SentenceTransformerProvider(
                model_name=config.sentence_transformers_model,
                lazy_loading=config.lazy_loading,
            )
            if config.lazy_loading:
                logger.info(f"✓ SentenceTransformer provider initialized with lazy loading: {config.sentence_transformers_model}")
            else:
                logger.info(f"✓ SentenceTransformer provider initialized: {config.sentence_transformers_model}")
        elif config.embedding_provider == "openai":
            # TODO: Implement OpenAI provider
            raise NotImplementedError("OpenAI provider not yet implemented")
        else:
            raise ValueError(f"Unknown embedding provider: {config.embedding_provider}")

        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = ChromaVectorStore(persist_directory=vector_store_path)
        logger.info(f"✓ Vector store initialized: {vector_store_path}")

        # Initialize query processor
        logger.info("Initializing query processor...")
        query_processor = QueryProcessor(
            embedding_provider=embedding_provider,
            enable_cache=True,
        )
        logger.info("✓ Query processor initialized")

        # Initialize context expander (NEW)
        logger.info("Initializing context expander...")
        context_expander = ContextExpander(vector_store=vector_store)
        logger.info("✓ Context expander initialized")

        # Initialize semantic searcher
        logger.info("Initializing semantic searcher...")
        semantic_searcher = SemanticSearcher(
            vector_store=vector_store,
            query_processor=query_processor,
            context_expander=context_expander,
        )
        logger.info("✓ Semantic searcher initialized")

        # Initialize enhancement components (NEW)
        enhancement_config = get_enhancement_config()
        if enhancement_config.enabled:
            logger.info("Initializing enhancement components...")

            # Initialize query analyzer
            query_analyzer = QueryAnalyzer()
            logger.info("✓ Query analyzer initialized")

            # Initialize symbol table manager (for multi-collection support)
            symbol_table_manager = SymbolTableManager()
            logger.info("✓ Symbol table manager initialized")

            # Initialize dependency graph manager (for multi-collection support)
            dependency_graph_manager = DependencyGraphManager()
            logger.info("✓ Dependency graph manager initialized")

            # Get default collection instances for context_expander and hybrid_retriever
            default_symbol_table = symbol_table_manager.get_table("default")
            default_dependency_graph = dependency_graph_manager.get_graph("default")

            # Update context expander with enhancement components
            context_expander.symbol_table = default_symbol_table
            context_expander.dependency_graph = default_dependency_graph
            logger.info("✓ Context expander enhanced with symbol table and dependency graph")

            # Initialize hybrid retriever
            hybrid_retriever = HybridRetriever(
                semantic_searcher=semantic_searcher,
                symbol_table=default_symbol_table,
                dependency_graph=default_dependency_graph,
                query_analyzer=query_analyzer,
            )
            logger.info("✓ Hybrid retriever initialized")
        else:
            logger.info("Enhancement components disabled in configuration")
            query_analyzer = None
            symbol_table_manager = None
            dependency_graph_manager = None
            hybrid_retriever = None

        # NOTE: IndexingPipeline is now created per index_codebase call with collection-specific instances
        # No global indexing_pipeline instance needed

        # Initialize security validators
        logger.info("Initializing security validators...")
        # Allow access to all paths (users can index any directory they have read access to)
        allowed_dirs = [
            "/",  # Allow all paths
        ]
        path_validator = PathValidator(allowed_directories=allowed_dirs)
        rate_limiter = RateLimiter(
            max_indexing_per_hour=config.max_indexing_requests_per_hour,
            max_search_per_minute=config.max_search_requests_per_minute,
        )
        logger.info("✓ Security validators initialized")

        logger.info("=" * 60)
        logger.info("✅ ALL COMPONENTS INITIALIZED SUCCESSFULLY")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}", exc_info=True)
        raise


def start_background_model_loading():
    """Start background loading of the embedding model after server is ready."""
    global embedding_provider, config

    if (embedding_provider and hasattr(embedding_provider, 'load_model_async') and
        config and config.lazy_loading):
        logger.info("Starting background model loading...")
        embedding_provider.load_model_async()
        logger.info("Background model loading initiated")
    elif config and not config.lazy_loading:
        logger.info("Lazy loading disabled - model already loaded during initialization")


def shutdown_handler(signum, frame):
    """
    Handle graceful shutdown.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info("=" * 60)
    logger.info("SHUTTING DOWN MCP SERVER")
    logger.info("=" * 60)
    logger.info("Received shutdown signal, cleaning up...")

    # Cleanup resources
    if query_processor:
        logger.info("Clearing query cache...")
        query_processor.clear_cache()

    logger.info("✓ Cleanup complete")
    logger.info("Goodbye!")
    sys.exit(0)


def _create_embedding_provider_for_model(
    model_name: str,
    dimensions: int,
    config: "ServerConfig"
) -> EmbeddingProvider:
    """
    Create an embedding provider for a specific model.

    This helper function enables auto-detection of collection embedding models
    and creates the appropriate provider on-the-fly.

    Args:
        model_name: Name of the embedding model (e.g., "nomic-embed-text", "all-MiniLM-L6-v2")
        dimensions: Expected embedding dimensions
        config: Server configuration

    Returns:
        EmbeddingProvider instance configured for the specified model

    Raises:
        ValueError: If model is unknown or cannot be auto-detected
    """
    logger.info(f"Creating embedding provider for model: {model_name} ({dimensions} dims)")

    # Map model names to providers
    if model_name == "nomic-embed-text":
        # Ollama provider
        provider = OllamaEmbeddingProvider(
            base_url=config.ollama_base_url,
            model="nomic-embed-text"
        )
        # Verify Ollama is available
        if not provider.check_health():
            raise RuntimeError(
                f"Ollama server not available at {config.ollama_base_url}. "
                "Please start Ollama and ensure the model is available."
            )
        logger.info(f"✓ Created Ollama provider: {model_name}")
        return provider

    elif model_name in ["all-MiniLM-L6-v2", "all-mpnet-base-v2", "paraphrase-MiniLM-L6-v2"]:
        # Sentence-transformers provider
        provider = SentenceTransformerProvider(
            model_name=model_name
        )
        logger.info(f"✓ Created SentenceTransformer provider: {model_name}")
        return provider

    elif model_name and model_name.startswith("text-embedding-"):
        # OpenAI models
        try:
            from semanticscout.embeddings.openai_provider import OpenAIEmbeddingProvider
            provider = OpenAIEmbeddingProvider(
                api_key=config.openai_api_key,
                model=model_name
            )
            logger.info(f"✓ Created OpenAI provider: {model_name}")
            return provider
        except ImportError:
            raise ValueError(
                f"OpenAI provider not available. Model: {model_name}"
            )

    else:
        # Unknown model - provide helpful error
        raise ValueError(
            f"Unknown embedding model: '{model_name}' ({dimensions} dims). "
            f"Cannot auto-detect provider. Supported models: "
            f"nomic-embed-text (Ollama), all-MiniLM-L6-v2 (SentenceTransformers), "
            f"all-mpnet-base-v2 (SentenceTransformers), text-embedding-* (OpenAI)"
        )


@mcp.tool()
def get_server_info() -> dict:
    """
    Get information about the MCP server.

    Returns:
        Dictionary with server information including version, configuration, and status.
    """
    logger.info("Tool called: get_server_info")

    # Get actual runtime embedding provider info
    provider_name = "unknown"
    model_name = "unknown"
    dimensions = 768  # Default fallback

    if embedding_provider:
        # Get actual provider type from the instance
        provider_class_name = embedding_provider.__class__.__name__
        if "Ollama" in provider_class_name:
            provider_name = "ollama"
        elif "OpenAI" in provider_class_name:
            provider_name = "openai"
        elif "SentenceTransformer" in provider_class_name:
            provider_name = "sentence-transformers"
        else:
            provider_name = provider_class_name

        # Get actual model name and dimensions from provider
        try:
            model_name = embedding_provider.get_model_name()
            dimensions = embedding_provider.get_dimensions()
        except Exception as e:
            logger.warning(f"Could not get model info from provider: {e}")
            # Use config fallback based on provider type
            if config:
                if config.embedding_provider == "ollama":
                    model_name = config.ollama_model
                elif config.embedding_provider == "sentence-transformers":
                    model_name = config.sentence_transformers_model
                elif config.embedding_provider == "openai":
                    model_name = config.openai_model
                # Only use config dimensions as last resort
                dimensions = config.embedding_dimensions
            else:
                model_name = "unknown"

    return {
        "name": config.server_name if config else "semanticscout",
        "version": __version__,  # Use actual package version
        "embedding_provider": provider_name,
        "embedding_model": model_name,
        "embedding_dimensions": dimensions,
        "vector_store_path": config.vector_store_path if config else "unknown",
        "status": "running",
    }


def _suggest_collections_for_path(path: str) -> List[str]:
    """
    Suggest collections that might contain the given path.

    Args:
        path: File or directory path

    Returns:
        List of collection names that might be relevant
    """
    from pathlib import Path

    try:
        abs_path = Path(path).resolve()
    except Exception:
        return []

    suggestions = []

    for collection_name in vector_store.list_collections():
        try:
            collection = vector_store.client.get_collection(name=collection_name)
            metadata = collection.metadata or {}
            codebase_path = metadata.get("codebase_path")

            if codebase_path:
                codebase_path_obj = Path(codebase_path).resolve()
                # Check if path is within this codebase
                try:
                    abs_path.relative_to(codebase_path_obj)
                    suggestions.append(collection_name)
                except ValueError:
                    # Not a subpath
                    continue
        except Exception:
            continue

    return suggestions


def _get_collection_files(collection_name: str) -> dict:
    """
    Get associated files for a collection (symbol table, dependency graph).

    Args:
        collection_name: Name of the collection

    Returns:
        Dictionary with file information:
        {
            "symbol_table": {"path": str, "size_bytes": int},
            "dependency_graph": {"path": str, "size_bytes": int}
        }
    """
    from pathlib import Path
    from semanticscout.paths import path_manager

    files = {}

    # Check symbol table
    symbol_table_path = path_manager.get_symbol_tables_dir() / f"{collection_name}.db"
    if symbol_table_path.exists():
        files["symbol_table"] = {
            "path": str(symbol_table_path),
            "size_bytes": symbol_table_path.stat().st_size
        }

    # Check dependency graph
    dep_graph_path = path_manager.get_dependency_graphs_dir() / f"{collection_name}.pkl"
    if dep_graph_path.exists():
        files["dependency_graph"] = {
            "path": str(dep_graph_path),
            "size_bytes": dep_graph_path.stat().st_size
        }

    return files


@mcp.tool()
def list_collections(show_current_config: bool = False) -> dict:
    """
    List all indexed codebases (collections) in the vector store.

    Args:
        show_current_config: If True, show current server embedding config instead of
                           stored collection metadata. Useful to see what model would
                           be used for new operations.

    Returns:
        Dictionary with list of collections. By default shows stored metadata from
        when collection was created. With show_current_config=True, shows current
        server configuration.

        Each collection contains:
        - name: Full collection name (project name + unique UUID)
        - codebase_path: Absolute path to the indexed codebase (if available)
        - embedding_model: Name of the embedding model (stored or current)
        - embedding_dimensions: Dimension size of the embedding vectors (stored or current)
        - processor_type: Type of AST processor used (e.g., "tree-sitter")
        - chunk_count: Number of code chunks indexed in the collection
        - associated_files: Dictionary of associated files (symbol_table, dependency_graph)

        Example response:
        {
            "collections": [
                {
                    "name": "morfeus_qt_a1b2c3d4",
                    "codebase_path": "/home/user/projects/morfeus_qt",
                    "embedding_model": "all-MiniLM-L6-v2",
                    "embedding_dimensions": 384,
                    "processor_type": "tree-sitter",
                    "chunk_count": 72,
                    "associated_files": {
                        "symbol_table": {
                            "path": "/home/user/semanticscout/data/symbol_tables/morfeus_qt_a1b2c3d4.db",
                            "size_bytes": 524288
                        },
                        "dependency_graph": {
                            "path": "/home/user/semanticscout/data/dependency_graphs/morfeus_qt_a1b2c3d4.pkl",
                            "size_bytes": 102400
                        }
                    }
                }
            ],
            "total_collections": 1
        }
    """
    logger.info("Tool called: list_collections")

    try:
        collections = vector_store.list_collections()

        # Get stats for each collection and extract metadata
        collection_info = []
        for collection_name in collections:
            stats = vector_store.get_stats(collection_name)

            # Extract metadata from stats
            metadata = stats.get("metadata", {})

            # Get embedding model and dimensions (stored vs current config)
            if show_current_config and embedding_provider:
                # Show current server config
                try:
                    embedding_model = embedding_provider.get_model_name()
                    embedding_dimensions = embedding_provider.get_dimensions()
                except Exception as e:
                    logger.warning(f"Could not get current embedding info: {e}")
                    # Fall back to stored metadata
                    embedding_model = metadata.get("embedding_model", "unknown")
                    embedding_dimensions = metadata.get("embedding_dimensions", 0)
            else:
                # Use stored metadata (default behavior)
                embedding_model = metadata.get("embedding_model", "unknown")
                embedding_dimensions = metadata.get("embedding_dimensions", 0)

            # Get processor type from metadata
            processor_type = metadata.get("processor_type", "unknown")

            # Get codebase path from metadata
            codebase_path = metadata.get("codebase_path")

            # Get associated files
            associated_files = _get_collection_files(collection_name)

            # Use full collection name (no parsing needed - UUID-based names)
            config_type = "current" if show_current_config else "stored"
            logger.debug(f"Collection: '{collection_name}', model: '{embedding_model}' ({config_type}), dims: {embedding_dimensions}, processor: '{processor_type}', chunks: {stats['count']}, files: {len(associated_files)}")

            coll_info = {
                "name": collection_name,  # Full name with UUID
                "embedding_model": embedding_model,
                "embedding_dimensions": embedding_dimensions,
                "processor_type": processor_type,
                "chunk_count": stats["count"],
                "associated_files": associated_files,
            }

            # Add codebase_path if available
            if codebase_path:
                coll_info["codebase_path"] = codebase_path

            collection_info.append(coll_info)

        return {
            "collections": collection_info,
            "total_collections": len(collections),
        }

    except Exception as e:
        logger.error(f"Error listing collections: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def index_codebase(path: str = None, incremental: bool = False) -> str:
    """
    Index a codebase directory for semantic search.

    This tool discovers all code files in the directory, chunks them semantically,
    generates embeddings, and stores them in the vector database for later retrieval.

    Args:
        path: Path to the codebase directory to index.
              If not provided, uses WORKSPACE_PATH environment variable.
              Example: C:/git/MyProject or /home/user/projects/myproject
        incremental: If True, only index changed files (5-10x faster for small changes).
                     If False, perform full re-indexing (default: False).
                     Incremental mode uses Git or file hashing to detect changes.

    Returns:
        Human-readable status message with indexing statistics

    Examples:
        # Full indexing (default)
        index_codebase(path="C:/git/MyProject")

        # Incremental indexing (only changed files)
        index_codebase(path="C:/git/MyProject", incremental=True)
    """
    # DEBUG: Log what we received
    logger.info(f"DEBUG: index_codebase called with path={repr(path)}, type={type(path)}")

    # Use environment variable if path not provided or if it's the default '.'
    if path is None or (isinstance(path, str) and (not path.strip() or path.strip() == '.')):
        workspace_path = os.getenv("WORKSPACE_PATH")
        if workspace_path:
            path = workspace_path
            logger.info(f"Using WORKSPACE_PATH environment variable: {path}")
            # Debug: Check if path exists
            from pathlib import Path as PathLib
            logger.info(f"DEBUG: Path exists? {PathLib(path).exists()}")
            logger.info(f"DEBUG: Path is absolute? {PathLib(path).is_absolute()}")
            logger.info(f"DEBUG: Resolved path: {PathLib(path).resolve()}")
        else:
            error_msg = """❌ ERROR: Path parameter is required!

No path was provided and WORKSPACE_PATH environment variable is not set.

Options:
1. Provide path explicitly: index_codebase(path="C:/git/MyProject")
2. Set WORKSPACE_PATH environment variable in your MCP JSON config

Examples:
  • Windows: C:/git/MyProject
  • Mac: /Users/yourname/projects/myproject
  • Linux: /home/yourname/projects/myproject
"""
            logger.error("index_codebase called without path and no WORKSPACE_PATH env var")
            return error_msg

    logger.info(f"Tool called: index_codebase(path={path})")

    try:
        # Safety check: Prevent indexing sensitive system directories
        sensitive_paths = ['/app', '/app/src', '/app/semanticscout', '/usr', '/bin', '/sbin', '/etc']
        if any(path.strip().rstrip('/').startswith(sp) for sp in sensitive_paths):
            error_msg = f"""❌ ERROR: Cannot index system or internal directories!

You attempted to index: {path}

This appears to be a system or internal directory. Please index your project directory instead.

Examples:
  • Windows: C:/git/MyProject
  • Mac: /Users/yourname/projects/myproject
  • Linux: /home/yourname/projects/myproject
"""
            logger.error(f"Rejected attempt to index sensitive directory: {path}")
            return error_msg

        # Check rate limit
        rate_limiter.check_indexing_rate()

        # Validate path
        validated_path = path_validator.validate_directory(path)
        logger.info(f"Validated path: {validated_path}")

        # Validate codebase size
        InputValidator.validate_codebase_size(validated_path)

        # Determine processor type that will be used for this indexing
        processor_type = "tree-sitter"
        logger.info(f"Processor type for duplicate check: {processor_type}")
        logger.info(f"Embedding model for duplicate check: {embedding_provider.get_model_name()}")
        logger.info(f"Codebase path for duplicate check: {validated_path}")

        # Check for existing collections with same path, model, AND processor type
        existing_collections = vector_store.find_collections_by_path_and_model(
            str(validated_path),
            embedding_provider.get_model_name(),
            processor_type=processor_type
        )

        logger.info(f"Found {len(existing_collections)} existing collections matching criteria")

        if existing_collections:
            # Found existing collection(s) - inform user
            response = f"⚠️  Existing collection(s) found for this codebase:\n\n"
            for coll_name in existing_collections:
                stats = vector_store.get_stats(coll_name)
                response += f"  • {coll_name} ({stats['count']} chunks)\n"

            response += f"\n💡 Options:\n"
            response += f"  1. Use incremental indexing to update existing collection:\n"
            response += f"     → Not yet implemented - coming soon!\n"
            response += f"  2. Clear old index first, then re-index:\n"
            response += f"     → clear_index('{existing_collections[0]}')\n"
            response += f"     → Then call index_codebase again\n"
            response += f"  3. Create a new collection anyway (not recommended - will create duplicate)\n"
            response += f"     → Just call index_codebase again to proceed\n"

            logger.info(f"Found {len(existing_collections)} existing collections for {validated_path}")
            return response

        # Generate unique collection name from path (includes UUID for uniqueness)
        # Embedding model and processor type are stored in metadata, not in the name
        collection_name = vector_store.generate_collection_name(str(validated_path))
        logger.info(f"Collection name: {collection_name}")

        # Get collection-specific instances from managers
        if symbol_table_manager and dependency_graph_manager:
            symbol_table = symbol_table_manager.get_table(collection_name)
            dependency_graph = dependency_graph_manager.get_graph(collection_name)
            logger.info(f"Retrieved collection-specific instances for: {collection_name}")
        else:
            symbol_table = None
            dependency_graph = None
            logger.info("Enhancement features disabled, indexing without symbol table and dependency graph")

        # Create IndexingPipeline instance for this indexing operation
        indexing_pipeline = IndexingPipeline(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            symbol_table=symbol_table,
            dependency_graph=dependency_graph,
            change_detector=change_detector,
        )
        logger.info("✓ Indexing pipeline created for this operation")

        # Progress callback for reporting
        def progress_callback(stage: str, current: int, total: int):
            """Report progress during indexing."""
            if total > 0:
                percentage = int((current / total) * 100)
                logger.info(f"Progress: {stage} - {current}/{total} ({percentage}%)")

        # Index the codebase
        if incremental:
            logger.info("Starting incremental indexing...")
        else:
            logger.info("Starting full indexing...")

        stats = indexing_pipeline.index_codebase(
            root_path=str(validated_path),
            collection_name=collection_name,
            progress_callback=progress_callback,
            incremental=incremental,
        )

        # Ensure persistence of symbol table and dependency graph
        if symbol_table:
            symbol_table.conn.commit()
            logger.info("✓ Symbol table changes committed")
        if dependency_graph:
            dependency_graph.save_to_file()
            logger.info("✓ Dependency graph saved to file")

        # Format response
        mode_str = "incremental" if stats.incremental_mode else "full"

        # Get embedding provider info
        provider_name = embedding_provider.get_model_name()
        dimensions = embedding_provider.get_dimensions()
        # Determine provider type from the embedding provider class name
        provider_type = embedding_provider.__class__.__name__.replace("Provider", "").replace("Embedding", "").lower()
        if "sentence" in provider_type:
            provider_type = "sentence-transformers"
        elif "ollama" in provider_type:
            provider_type = "ollama"

        # Determine symbol extraction method
        symbol_extraction = "Tree-sitter (AST)" if indexing_pipeline.ast_processor else "Disabled"

        response = f"""✅ Successfully indexed codebase: {validated_path.name}

Mode: {mode_str.upper()}

🔧 Configuration:
  • Embedding Provider: {provider_type}
  • Model: {provider_name}
  • Dimensions: {dimensions}
  • Symbol Extraction: {symbol_extraction}

📊 Statistics:
  • Files discovered: {stats.files_discovered}
  • Files indexed: {stats.files_indexed}
  • Files failed: {stats.files_failed}
  • Chunks created: {stats.chunks_created}
  • Embeddings generated: {stats.embeddings_generated}
  • Symbols extracted: {stats.symbols_extracted}
  • Dependencies tracked: {stats.dependencies_tracked}
  • Time elapsed: {stats.time_elapsed:.2f}s

Collection: {collection_name}

You can now search this codebase using the search_code tool."""

        # Add incremental mode details if applicable
        if stats.incremental_mode:
            files_changed = stats.files_indexed
            files_unchanged = stats.files_discovered - stats.files_indexed
            response += f"\n\n🔄 Incremental Update:"
            response += f"\n  • Files changed: {files_changed}"
            response += f"\n  • Files unchanged: {files_unchanged}"
            if files_changed > 0:
                speedup = stats.files_discovered / max(files_changed, 1)
                response += f"\n  • Speedup: ~{speedup:.1f}x faster"

        if stats.errors:
            response += f"\n\n⚠️ Errors encountered:\n"
            for error in stats.errors[:5]:  # Show first 5 errors
                response += f"  • {error}\n"
            if len(stats.errors) > 5:
                response += f"  ... and {len(stats.errors) - 5} more errors\n"

        logger.info(f"Indexing complete: {stats.files_indexed} files, {stats.chunks_created} chunks")
        return response

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return f"❌ Validation Error: {str(e)}"

    except Exception as e:
        logger.error(f"Error indexing codebase: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


@mcp.tool()
def search_code(
    query: str,
    collection_name: str,
    top_k: int = 10,  # CHANGED: Increased from 5 to 10
    expansion_level: str = "medium",  # NEW
    max_result_length: int = 5000,  # NEW
    exclude_test_files: bool = True,  # NEW - Filter test files by default
    coverage_mode: str = "",  # NEW - Coverage mode
) -> str:
    """
    Search indexed codebase using natural language queries with context expansion.

    Args:
        query: Natural language search query (e.g., "authentication function")
        collection_name: Name of the collection to search (from index_codebase or list_collections)
        top_k: Number of results to return (default: 10, max: 100). Takes priority over coverage_mode.
        expansion_level: Context expansion level - 'none', 'low', 'medium', 'high' (default: 'medium')
        max_result_length: Maximum characters per result (default: 5000, was 500)
        exclude_test_files: If True (default), exclude test files from results. Set to False to include test files.
        coverage_mode: Coverage level - 'focused' (5), 'balanced' (10), 'comprehensive' (20), 'exhaustive' (50). Only used if top_k is default value.

    Returns:
        Human-readable search results with code snippets, imports, and metadata

    Expansion Levels:
        - none: No expansion, return original chunks only
        - low: Include file context (imports), ~90 lines per result
        - medium: Include file context + neighbors, ~180 lines per result (recommended)
        - high: Include file context + neighbors + imports, ~300+ lines per result

    Coverage Modes (only applied when top_k is default value of 10):
        - focused: 5 results - Quick overview of most relevant code
        - balanced: 10 results - Good balance of coverage and relevance (default)
        - comprehensive: 20 results - Broad coverage for complex queries
        - exhaustive: 50 results - Maximum coverage for architectural queries

        Note: Explicit top_k values always take priority over coverage_mode settings.

    Test File Filtering:
        - By default, test files are excluded from results to focus on production code
        - Test files are detected by path patterns (/tests/, /test/), file names (*.test.*, *Test.cs), and AST patterns
        - Set exclude_test_files=False to include test files in results
    """
    logger.info(
        f"Tool called: search_code(query={query[:50]}..., collection={collection_name}, "
        f"top_k={top_k}, expansion={expansion_level}, coverage_mode={coverage_mode})"
    )

    try:
        # Check rate limit
        rate_limiter.check_search_rate()

        # Coverage mode mapping (NEW)
        COVERAGE_MODES = {
            'focused': 5,
            'balanced': 10,
            'comprehensive': 20,
            'exhaustive': 50
        }

        # Architectural query patterns (NEW)
        ARCHITECTURAL_QUERY_PATTERNS = [
            'dependency injection',
            'service registration',
            'service wiring',
            'configuration',
            'startup',
            'di container',
            'ioc',
            'program.cs',
            'configureservices',
        ]

        # Detect architectural queries and auto-increase coverage (NEW)
        query_lower = query.lower()
        for pattern in ARCHITECTURAL_QUERY_PATTERNS:
            if pattern in query_lower:
                # Auto-set to comprehensive mode if not already set
                if coverage_mode == 'balanced':  # Only override default
                    coverage_mode = 'comprehensive'
                    logger.info(f"🏗️ Architectural query detected ('{pattern}'): auto-increasing coverage to 'comprehensive' (20 results)")
                break

        # Apply coverage mode only if top_k is still at default value (NEW)
        # Explicit top_k values take priority over coverage_mode
        if coverage_mode and coverage_mode not in COVERAGE_MODES:
            return f"❌ Invalid coverage_mode: '{coverage_mode}'. Valid options: {list(COVERAGE_MODES.keys())}"
        elif coverage_mode in COVERAGE_MODES and top_k == 10:  # Only apply if top_k is default
            top_k = COVERAGE_MODES[coverage_mode]
            logger.info(f"Coverage mode '{coverage_mode}' applied: top_k={top_k} (top_k was default value)")
        elif coverage_mode in COVERAGE_MODES and top_k != 10:  # Explicit top_k provided
            logger.info(f"Explicit top_k={top_k} takes priority over coverage_mode='{coverage_mode}'")
        elif coverage_mode in COVERAGE_MODES:  # This shouldn't happen but just in case
            logger.info(f"Using explicit top_k={top_k}")

        # Validate inputs
        validated_query = InputValidator.validate_query(query)
        validated_top_k = InputValidator.validate_top_k(top_k)
        validated_collection = InputValidator.validate_collection_name(collection_name)

        # Check if collection exists
        if not vector_store.collection_exists(validated_collection):
            error_msg = f"❌ Collection '{validated_collection}' does not exist.\n\n"

            # Try to suggest relevant collections based on current directory
            try:
                import os
                current_dir = os.getcwd()
                suggestions = _suggest_collections_for_path(current_dir)

                if suggestions:
                    error_msg += "💡 Did you mean one of these collections?\n"
                    for coll_name in suggestions[:3]:  # Show max 3 suggestions
                        stats = vector_store.get_stats(coll_name)
                        error_msg += f"  • {coll_name} ({stats['count']} chunks)\n"
                    error_msg += "\n"
            except Exception:
                pass

            error_msg += "Use list_collections() to see all available collections."
            return error_msg

        # AUTO-DETECTION: Check if collection's embedding model matches server configuration
        searcher_to_use = semantic_searcher  # Default to global searcher
        try:
            collection = vector_store.get_or_create_collection(validated_collection)
            collection_metadata = collection.metadata or {}
            collection_embedding_model = collection_metadata.get("embedding_model")
            collection_dimensions = int(collection_metadata.get("embedding_dimensions", 0))

            # Get current server embedding provider info
            current_model = embedding_provider.get_model_name()
            current_dimensions = embedding_provider.get_dimensions()

            # Check for dimension mismatch
            if collection_dimensions > 0 and collection_dimensions != current_dimensions:
                logger.warning(
                    f"⚠️ Embedding dimension mismatch detected for collection '{validated_collection}': "
                    f"Collection expects {collection_dimensions} dims ({collection_embedding_model}) "
                    f"but server is configured for {current_dimensions} dims ({current_model}). "
                    "Attempting to create temporary embedding provider..."
                )

                # Create temporary provider matching collection's model
                temp_provider = _create_embedding_provider_for_model(
                    collection_embedding_model,
                    collection_dimensions,
                    config
                )

                # Create temporary query processor
                temp_query_processor = QueryProcessor(
                    embedding_provider=temp_provider,
                    enable_cache=True
                )

                # Create temporary semantic searcher with temp query processor
                searcher_to_use = SemanticSearcher(
                    vector_store=vector_store,
                    query_processor=temp_query_processor,
                    context_expander=context_expander
                )

                logger.info(
                    f"✓ Successfully created temporary embedding provider and searcher: "
                    f"{collection_embedding_model} ({collection_dimensions} dims)"
                )
            else:
                logger.debug(
                    f"✓ Embedding dimensions match: {current_dimensions} dims ({current_model})"
                )
        except Exception as e:
            logger.error(f"Error during embedding model auto-detection: {e}", exc_info=True)
            # Fall back to global searcher
            logger.warning("Falling back to global semantic searcher")

        # Perform search with expansion (NEW)
        logger.info(f"Performing semantic search with expansion_level={expansion_level}, exclude_test_files={exclude_test_files}, top_k={validated_top_k}...")
        results = searcher_to_use.search(
            query=validated_query,
            collection_name=validated_collection,
            top_k=validated_top_k,
            expansion_level=expansion_level,  # NEW
            exclude_test_files=exclude_test_files,  # NEW
        )

        # Format response
        if not results:
            return f"No results found for query: {validated_query}"

        response = f"🔍 Search Results for: \"{validated_query}\"\n"
        response += f"Collection: {validated_collection}\n"
        response += f"Found {len(results)} results:\n\n"

        for i, result in enumerate(results):
            response += f"{'=' * 60}\n"
            response += f"Result {i+1}/{len(results)} (Similarity: {result.similarity_score:.4f})\n"
            response += f"{'=' * 60}\n"
            response += f"📄 File: {result.file_path}\n"
            response += f"📍 Lines: {result.start_line}-{result.end_line} ({result.end_line - result.start_line + 1} lines)\n"
            response += f"🏷️  Type: {result.chunk_type}\n"
            response += f"💻 Language: {result.language}\n"

            # Add import context (NEW)
            imports = result.metadata.get("imports", [])
            if imports:
                response += f"📎 Imports: {', '.join([imp.get('statement', '') for imp in imports[:5]])}\n"
                if len(imports) > 5:
                    response += f"   ... and {len(imports) - 5} more imports\n"

            # Add reference context (NEW)
            references = result.metadata.get("references", [])
            if references:
                response += f"🔗 References: {', '.join(references[:5])}\n"
                if len(references) > 5:
                    response += f"   ... and {len(references) - 5} more\n"

            # Add expansion info (NEW)
            if result.expanded_from:
                response += f"📊 Expanded from {len(result.expanded_from)} chunks\n"

            response += "\n"

            # Show code with smart truncation (NEW: increased from 500 to max_result_length)
            code_content = result.content
            if len(code_content) > max_result_length:
                # Smart truncation at line boundary
                truncate_pos = code_content.rfind('\n', 0, max_result_length)
                if truncate_pos == -1:
                    truncate_pos = max_result_length
                response += f"Code:\n```{result.language}\n{code_content[:truncate_pos]}\n"
                response += f"... (truncated, {len(code_content)} chars total)\n```\n"
            else:
                response += f"Code:\n```{result.language}\n{code_content}\n```\n"

            response += "\n"

        logger.info(f"Search complete: {len(results)} results")
        return response

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return f"❌ Validation Error: {str(e)}"

    except Exception as e:
        logger.error(f"Error searching code: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_indexing_status(collection_name: str, show_current_config: bool = False) -> str:
    """
    Get indexing status and statistics for a codebase collection.

    Args:
        collection_name: Name of the collection to check
        show_current_config: If True, show current server embedding config alongside
                           stored collection metadata for comparison

    Returns:
        Human-readable statistics about the indexed codebase
    """
    logger.info(f"Tool called: get_indexing_status(collection={collection_name})")

    try:
        # Validate collection name
        validated_collection = InputValidator.validate_collection_name(collection_name)

        # Check if collection exists
        if not vector_store.collection_exists(validated_collection):
            return f"❌ Collection '{validated_collection}' does not exist. Use list_collections to see available collections."

        # Get stats
        stats = vector_store.get_stats(validated_collection)
        metadata = stats.get("metadata", {})

        # Format response
        response = f"""📊 Indexing Status for: {validated_collection}

Statistics:
  • Total chunks: {stats['count']}
  • Collection exists: Yes

"""

        # Show embedding model information
        if show_current_config and embedding_provider:
            try:
                current_model = embedding_provider.get_model_name()
                current_dims = embedding_provider.get_dimensions()
                response += f"Current server config: {current_model} ({current_dims} dims)\n"
            except Exception as e:
                logger.warning(f"Could not get current embedding info: {e}")
                response += "Current server config: Unable to retrieve\n"

        # Always show stored metadata for comparison
        stored_model = metadata.get("embedding_model", "unknown")
        stored_dims = metadata.get("embedding_dimensions", "unknown")
        response += f"Collection metadata: {stored_model} ({stored_dims} dims)\n"

        response += "\nUse search_code to query this collection."

        logger.info(f"Status retrieved for collection: {validated_collection}")
        return response

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return f"❌ Validation Error: {str(e)}"

    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


@mcp.tool()
def clear_index(collection_name: str) -> str:
    """
    Clear the index for a specific codebase collection.

    WARNING: This permanently deletes all indexed data for the collection.

    Args:
        collection_name: Name of the collection to delete

    Returns:
        Confirmation message
    """
    logger.info(f"Tool called: clear_index(collection={collection_name})")

    try:
        # Validate collection name
        validated_collection = InputValidator.validate_collection_name(collection_name)

        # Check if collection exists
        if not vector_store.collection_exists(validated_collection):
            return f"❌ Collection '{validated_collection}' does not exist. Nothing to clear."

        # Delete collection from vector store
        vector_store.delete_collection(validated_collection)

        # Delete associated files
        from semanticscout.paths import path_manager

        files_deleted = []

        # Delete symbol table
        symbol_table_path = path_manager.get_symbol_tables_dir() / f"{validated_collection}.db"
        if symbol_table_path.exists():
            try:
                symbol_table_path.unlink()
                files_deleted.append(f"symbol_table: {symbol_table_path}")
                logger.info(f"Deleted symbol table: {symbol_table_path}")
            except Exception as e:
                logger.warning(f"Failed to delete symbol table {symbol_table_path}: {e}")

        # Delete dependency graph
        dep_graph_path = path_manager.get_dependency_graphs_dir() / f"{validated_collection}.pkl"
        if dep_graph_path.exists():
            try:
                dep_graph_path.unlink()
                files_deleted.append(f"dependency_graph: {dep_graph_path}")
                logger.info(f"Deleted dependency graph: {dep_graph_path}")
            except Exception as e:
                logger.warning(f"Failed to delete dependency graph {dep_graph_path}: {e}")

        # Build response message
        response = f"✅ Successfully cleared index for collection: {validated_collection}\n"
        if files_deleted:
            response += f"\nDeleted associated files:\n"
            for file_info in files_deleted:
                response += f"  • {file_info}\n"
        else:
            response += "\nNo associated files found to delete."

        logger.info(f"Collection deleted: {validated_collection}, files deleted: {len(files_deleted)}")
        return response

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return f"❌ Validation Error: {str(e)}"

    except Exception as e:
        logger.error(f"Error clearing index: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


@mcp.tool()
def find_symbol(
    symbol_name: str,
    collection_name: str,
    symbol_type: str = None,
) -> str:
    """
    Find a specific symbol (function, class, interface, etc.) in the codebase.

    Args:
        symbol_name: Name of the symbol to find (e.g., "UserController", "authenticate")
        collection_name: Name of the collection to search
        symbol_type: Optional symbol type filter (function, class, interface, method, etc.)

    Returns:
        Symbol information including location, signature, and documentation
    """
    logger.info(f"Tool called: find_symbol(symbol={symbol_name}, collection={collection_name}, type={symbol_type})")

    try:
        # Check if enhancements are enabled
        if not symbol_table_manager:
            return "❌ Symbol search is not available. Enhancement features are disabled."

        # Validate inputs
        validated_symbol = InputValidator.validate_query(symbol_name)
        validated_collection = InputValidator.validate_collection_name(collection_name)

        # Check if collection exists
        if not vector_store.collection_exists(validated_collection):
            error_msg = f"❌ Collection '{validated_collection}' does not exist.\n\n"

            # Try to suggest relevant collections
            try:
                import os
                current_dir = os.getcwd()
                suggestions = _suggest_collections_for_path(current_dir)

                if suggestions:
                    error_msg += "💡 Did you mean one of these collections?\n"
                    for coll_name in suggestions[:3]:
                        stats = vector_store.get_stats(coll_name)
                        error_msg += f"  • {coll_name} ({stats['count']} chunks)\n"
                    error_msg += "\n"
            except Exception:
                pass

            error_msg += "Use list_collections() to see all available collections."
            return error_msg

        # Get collection-specific symbol table instance
        symbol_table = symbol_table_manager.get_table(validated_collection)

        # Search for symbol using exact lookup
        logger.info(f"Searching for symbol: {validated_symbol}")
        symbols = symbol_table.lookup_symbol(
            name=validated_symbol,
            symbol_type=symbol_type,
        )

        if not symbols:
            return f"No symbols found matching: {validated_symbol}"

        response = f"🔍 Symbol Search Results for: \"{validated_symbol}\"\n"
        response += f"Collection: {validated_collection}\n"
        response += f"Found {len(symbols)} symbols:\n\n"

        for i, symbol in enumerate(symbols[:10]):  # Limit to 10 results
            response += f"{'=' * 60}\n"
            response += f"Symbol {i+1}/{min(len(symbols), 10)}\n"
            response += f"{'=' * 60}\n"
            response += f"📛 Name: {symbol['name']}\n"
            response += f"🏷️  Type: {symbol['type']}\n"
            response += f"📄 File: {symbol['file_path']}\n"
            response += f"📍 Line: {symbol['line_number']}\n"

            if symbol.get('signature'):
                response += f"✍️  Signature: {symbol['signature']}\n"

            if symbol.get('documentation'):
                doc = symbol['documentation'][:200]
                response += f"📝 Documentation: {doc}...\n" if len(symbol['documentation']) > 200 else f"📝 Documentation: {doc}\n"

            if symbol.get('scope'):
                response += f"🔒 Scope: {symbol['scope']}\n"

            if symbol.get('is_exported'):
                response += f"📤 Exported: Yes\n"

            response += "\n"

        if len(symbols) > 10:
            response += f"... and {len(symbols) - 10} more symbols\n"

        logger.info(f"Symbol search complete: {len(symbols)} results")
        return response

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return f"❌ Validation Error: {str(e)}"

    except Exception as e:
        logger.error(f"Error finding symbol: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


@mcp.tool()
def find_callers(
    symbol_name: str,
    collection_name: str,
    max_results: int = 10,
) -> str:
    """
    Find all functions/methods that call a specific symbol.

    Args:
        symbol_name: Name of the symbol to find callers for
        collection_name: Name of the collection to search
        max_results: Maximum number of callers to return (default: 10)

    Returns:
        List of callers with their locations
    """
    logger.info(f"Tool called: find_callers(symbol={symbol_name}, collection={collection_name})")

    try:
        # Check if enhancements are enabled
        if not symbol_table_manager:
            return "❌ Caller search is not available. Enhancement features are disabled."

        # Validate inputs
        validated_symbol = InputValidator.validate_query(symbol_name)
        validated_collection = InputValidator.validate_collection_name(collection_name)

        # Get collection-specific symbol table instance
        symbol_table = symbol_table_manager.get_table(validated_collection)

        # Find callers
        logger.info(f"Finding callers of: {validated_symbol}")
        callers = symbol_table.find_callers(validated_symbol, max_results=max_results)

        if not callers:
            return f"No callers found for symbol: {validated_symbol}"

        response = f"📞 Callers of: \"{validated_symbol}\"\n"
        response += f"Collection: {validated_collection}\n"
        response += f"Found {len(callers)} callers:\n\n"

        for i, caller in enumerate(callers[:max_results]):
            response += f"{i+1}. {caller['name']} ({caller['type']})\n"
            response += f"   📄 {caller['file_path']}:{caller['line_number']}\n"
            if caller.get('signature'):
                response += f"   ✍️  {caller['signature']}\n"
            response += "\n"

        if len(callers) > max_results:
            response += f"... and {len(callers) - max_results} more callers\n"

        logger.info(f"Caller search complete: {len(callers)} results")
        return response

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return f"❌ Validation Error: {str(e)}"

    except Exception as e:
        logger.error(f"Error finding callers: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


@mcp.tool()
def trace_dependencies(
    file_path: str,
    collection_name: str,
    depth: int = 2,
) -> str:
    """
    Trace file dependencies (imports) for a specific file.

    Args:
        file_path: Path to the file to trace dependencies for
        collection_name: Name of the collection to search
        depth: Dependency depth to trace (default: 2, valid range: 1-5)
               - Must be an integer between 1 and 5 (inclusive)
               - Values outside this range will result in an error

    Returns:
        Dependency tree showing imports and their relationships

    Raises:
        ValidationError: If depth is not an integer or outside valid range (1-5)
    """
    logger.info(f"Tool called: trace_dependencies(file={file_path}, collection={collection_name}, depth={depth})")

    try:
        # Check if enhancements are enabled
        if not dependency_graph_manager or not symbol_table_manager:
            return "❌ Dependency tracing is not available. Enhancement features are disabled."

        # Validate inputs
        validated_collection = InputValidator.validate_collection_name(collection_name)

        # Validate depth parameter - explicit validation instead of silent clamping
        if not isinstance(depth, int):
            return f"❌ Invalid depth parameter: must be an integer, got {type(depth).__name__}"

        if depth < 1:
            return f"❌ Invalid depth parameter: must be >= 1, got {depth}"

        if depth > 5:
            return f"❌ Invalid depth parameter: must be <= 5, got {depth}"

        validated_depth = depth

        # Get collection-specific instances
        dependency_graph = dependency_graph_manager.get_graph(validated_collection)
        symbol_table = symbol_table_manager.get_table(validated_collection)

        # Get dependencies
        logger.info(f"Tracing dependencies for: {file_path}")
        dependencies = dependency_graph.get_file_dependencies(
            file_path,
            symbol_table,
            depth=validated_depth,
        )

        if not dependencies:
            return f"No dependencies found for file: {file_path}"

        response = f"🔗 Dependency Trace for: {file_path}\n"
        response += f"Collection: {validated_collection}\n"
        response += f"Depth: {validated_depth}\n"
        response += f"Found {len(dependencies)} dependencies:\n\n"

        # Group dependencies by level
        dep_levels = {}
        for dep in dependencies:
            level = dep.get('level', 1)
            if level not in dep_levels:
                dep_levels[level] = []
            dep_levels[level].append(dep)

        # Display dependencies by level
        for level in sorted(dep_levels.keys()):
            response += f"{'  ' * (level - 1)}Level {level}:\n"
            for dep in dep_levels[level]:
                indent = '  ' * level
                response += f"{indent}📦 {dep['to_file']}\n"
                if dep.get('imported_symbols'):
                    symbols = dep['imported_symbols'][:5]
                    response += f"{indent}   Imports: {', '.join(symbols)}\n"
                    if len(dep['imported_symbols']) > 5:
                        response += f"{indent}   ... and {len(dep['imported_symbols']) - 5} more\n"
            response += "\n"

        logger.info(f"Dependency trace complete: {len(dependencies)} dependencies")
        return response

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return f"❌ Validation Error: {str(e)}"

    except Exception as e:
        logger.error(f"Error tracing dependencies: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


@mcp.tool()
def process_file_changes(
    collection_name: str,
    changes: str,
    auto_update: bool = True,
) -> str:
    """
    Process file change events for incremental indexing.

    This tool accepts file change events from editors/MCP clients and performs
    incremental updates to the index, avoiding full re-indexing.

    Args:
        collection_name: Name of the collection to update
        changes: JSON string containing file change batch (FileChangeBatch schema)
        auto_update: If True, apply updates immediately; if False, return plan only (default: True)

    Returns:
        Human-readable summary of changes processed and updates applied

    Example changes JSON:
    {
        "events": [
            {
                "type": "modified",
                "path": "src/module.py",
                "timestamp": 1696800000000,
                "content_hash": "abc123..."
            }
        ],
        "workspace_root": "/path/to/project",
        "debounce_ms": 500
    }
    """
    logger.info(f"Tool called: process_file_changes(collection={collection_name}, auto_update={auto_update})")

    try:
        # Parse JSON changes
        try:
            batch: FileChangeBatch = json.loads(changes)
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON: {str(e)}"

        # Validate batch
        try:
            FileChangeEventValidator.validate_batch(batch)
        except EventValidationError as e:
            return f"❌ Validation Error: {str(e)}"

        # Check if collection exists
        try:
            collection = vector_store.get_or_create_collection(
                collection_name,
                embedding_dimension=embedding_provider.get_dimensions(),
                model_name=embedding_provider.get_model_name(),
            )
        except Exception as e:
            return f"❌ Collection Error: {str(e)}"

        workspace_root = Path(batch["workspace_root"])
        events = batch["events"]

        # Count event types
        added_count = sum(1 for e in events if e["type"] == "added")
        modified_count = sum(1 for e in events if e["type"] == "modified")
        deleted_count = sum(1 for e in events if e["type"] == "deleted")
        renamed_count = sum(1 for e in events if e["type"] == "renamed")

        if not auto_update:
            # Dry-run mode: return plan without executing
            response = f"""📋 File Change Plan (Dry-Run Mode)

Collection: {collection_name}
Workspace: {workspace_root}

📊 Changes to Process:
  • Files to add: {added_count}
  • Files to modify: {modified_count}
  • Files to delete: {deleted_count}
  • Files to rename: {renamed_count}
  • Total events: {len(events)}

⚠️ No updates applied (auto_update=False)

To apply these changes, call again with auto_update=True."""

            logger.info(f"Dry-run complete: {len(events)} events planned")
            return response

        # Apply updates
        logger.info(f"Processing {len(events)} file change events...")

        # For now, trigger a full re-index of changed files
        # TODO: Implement DeltaIndexer for more efficient updates
        changed_files = []
        for event in events:
            if event["type"] != "deleted":
                file_path = workspace_root / event["path"]
                if file_path.exists():
                    changed_files.append(file_path)

        if changed_files:
            # Re-index changed files
            stats = indexing_pipeline.index_codebase(
                root_path=str(workspace_root),
                collection_name=collection_name,
                incremental=True,
            )

            response = f"""✅ File Changes Processed

Collection: {collection_name}
Workspace: {workspace_root}

📊 Changes Applied:
  • Files added: {added_count}
  • Files modified: {modified_count}
  • Files deleted: {deleted_count}
  • Files renamed: {renamed_count}
  • Total events: {len(events)}

📈 Indexing Results:
  • Files indexed: {stats.files_indexed}
  • Chunks created: {stats.chunks_created}
  • Embeddings generated: {stats.embeddings_generated}
  • Time elapsed: {stats.time_elapsed:.2f}s

✓ Index updated successfully"""
        else:
            response = f"""✅ File Changes Processed

Collection: {collection_name}
Workspace: {workspace_root}

📊 Changes Applied:
  • Files deleted: {deleted_count}
  • Total events: {len(events)}

⚠️ No files to re-index (all deleted or not found)"""

        logger.info(f"File changes processed: {len(events)} events")
        return response

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return f"❌ Validation Error: {str(e)}"

    except Exception as e:
        logger.error(f"Error processing file changes: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


def main():
    """Main entry point for the MCP server."""
    import argparse
    from pathlib import Path

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="SemanticScout MCP Server")
    args = parser.parse_args()

    # Setup logging FIRST (before any other operations)
    # All data is stored in ~/semanticscout (cross-platform)
    log_file = path_manager.get_logs_dir() / "mcp_server.log"
    setup_logging(log_level="INFO", log_file=str(log_file))

    logger.info("=" * 60)
    logger.info("STARTING MCP SERVER")
    logger.info("=" * 60)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        # Initialize all components
        initialize_components()

        # Start the MCP server
        logger.info("Starting MCP server...")
        logger.info("Server is ready to accept connections")
        logger.info("=" * 60)

        # Start background model loading after server is ready
        start_background_model_loading()

        # Run the server
        mcp.run()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        shutdown_handler(signal.SIGINT, None)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


