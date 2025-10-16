"""
Complete indexing pipeline orchestrating file discovery, chunking, embedding, and storage.
Enhanced with AST processing, symbol table construction, and dependency graph building.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from ..indexer.file_discovery import FileDiscovery
from ..indexer.code_chunker import ASTCodeChunker
from ..indexer.file_classifier import FileClassifier  # NEW - Test file detection
from ..indexer.git_change_detector import IndexingMetadata  # NEW
from ..indexer.change_detector import UnifiedChangeDetector  # NEW
from ..embeddings.base import EmbeddingProvider
from ..vector_store.chroma_store import ChromaVectorStore
from ..ast_processing.ast_processor import ASTProcessor  # NEW
from ..symbol_table.symbol_table import SymbolTable  # NEW
from ..dependency_graph.dependency_graph import DependencyGraph  # NEW
from ..language_detection.project_language_detector import ProjectLanguageDetector, LanguageDetectionResult  # NEW
from ..dependency_analysis.dependency_router import DependencyAnalysisRouter  # NEW
from ..config import get_enhancement_config  # NEW
from ..utils.file_encoding import read_file_with_encoding_detection

logger = logging.getLogger(__name__)


class IndexingStats:
    """Statistics for an indexing operation."""

    def __init__(self):
        self.files_discovered = 0
        self.files_indexed = 0
        self.files_failed = 0
        self.chunks_created = 0
        self.embeddings_generated = 0
        self.symbols_extracted = 0  # NEW
        self.dependencies_tracked = 0  # NEW
        self.symbol_usage_tracked = 0  # NEW
        self.ast_parsing_time = 0.0  # NEW
        self.time_elapsed = 0.0
        self.errors: List[str] = []
        # Incremental indexing stats
        self.files_changed = 0  # NEW
        self.files_added = 0  # NEW
        self.files_deleted = 0  # NEW
        self.incremental_mode = False  # NEW

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        result = {
            "files_discovered": self.files_discovered,
            "files_indexed": self.files_indexed,
            "files_failed": self.files_failed,
            "chunks_created": self.chunks_created,
            "embeddings_generated": self.embeddings_generated,
            "symbols_extracted": self.symbols_extracted,
            "dependencies_tracked": self.dependencies_tracked,
            "symbol_usage_tracked": self.symbol_usage_tracked,
            "ast_parsing_time": self.ast_parsing_time,
            "time_elapsed": self.time_elapsed,
            "errors": self.errors,
        }
        # Add incremental stats if in incremental mode
        if self.incremental_mode:
            result.update({
                "files_changed": self.files_changed,
                "files_added": self.files_added,
                "files_deleted": self.files_deleted,
                "incremental_mode": True,
            })
        return result


class IndexingPipeline:
    """
    Complete indexing pipeline that orchestrates all components.
    Enhanced with AST processing, symbol table construction, and dependency graph building.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: ChromaVectorStore,
        batch_size: int = 100,
        symbol_table: Optional[SymbolTable] = None,  # NEW
        dependency_graph: Optional[DependencyGraph] = None,  # NEW
        change_detector: Optional[UnifiedChangeDetector] = None,  # NEW
        language_detector: Optional[ProjectLanguageDetector] = None,  # NEW
        dependency_router: Optional[DependencyAnalysisRouter] = None,  # NEW
    ):
        """
        Initialize the indexing pipeline.

        Args:
            embedding_provider: Provider for generating embeddings
            vector_store: Vector store for persisting embeddings
            batch_size: Number of files to process in each batch
            symbol_table: Optional symbol table for storing symbols
            dependency_graph: Optional dependency graph for tracking dependencies
            change_detector: Optional unified change detector for incremental indexing (auto-detects Git/hash)
            language_detector: Optional project language detector for language-aware processing
            dependency_router: Optional dependency analysis router for language-specific dependency analysis
        """
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.batch_size = batch_size
        self.symbol_table = symbol_table
        self.dependency_graph = dependency_graph
        self.change_detector = change_detector  # NEW
        self.language_detector = language_detector or ProjectLanguageDetector()  # NEW
        self.dependency_router = dependency_router or DependencyAnalysisRouter()  # NEW

        self.file_discovery = FileDiscovery()
        # CRITICAL: Disable file-level chunks to avoid import-only results
        # create_file_chunks=False ensures we only get function/class chunks with actual code
        # max_chunk_size=1500 (down from 3000) for better granularity
        self.code_chunker = ASTCodeChunker(
            max_chunk_size=1500,
            create_file_chunks=False
        )

        # Initialize enhancement components if enabled
        self.enhancement_config = get_enhancement_config()
        if self.enhancement_config.enabled and self.enhancement_config.ast_processing.enabled:
            # Initialize tree-sitter AST processor
            self.ast_processor = ASTProcessor()
            logger.info("Initialized indexing pipeline with AST processing enabled")
        else:
            self.ast_processor = None
            logger.info("Initialized indexing pipeline (AST processing disabled)")

    def index_codebase(
        self,
        root_path: str,
        collection_name: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        incremental: bool = False,  # NEW
    ) -> IndexingStats:
        """
        Index an entire codebase.

        Args:
            root_path: Root directory of the codebase
            collection_name: Name for the collection (auto-generated if None)
            progress_callback: Optional callback for progress updates (stage, current, total)
            incremental: If True, use Git to detect and index only changed files (default: False)

        Returns:
            IndexingStats object with statistics
        """
        stats = IndexingStats()
        stats.incremental_mode = incremental

        # Use tree-sitter processor (initialized in __init__)
        processor_type = "tree-sitter"
        logger.info("Using tree-sitter processor for AST parsing and symbol extraction")

        start_time = time.time()

        try:
            # Generate collection name if not provided
            if collection_name is None:
                collection_name = self.vector_store.generate_collection_name(root_path)

            logger.info(f"Starting indexing of codebase: {root_path}")
            logger.info(f"Collection name: {collection_name}")
            if incremental:
                logger.info("Incremental mode: ENABLED")

            # Stage 0: Detect project languages (NEW)
            logger.info("Stage 0: Detect project languages...")
            if progress_callback:
                progress_callback("Detecting project languages", 0, 1)

            detected_languages, processor_type = self._detect_project_languages(root_path, collection_name, processor_type)

            # Stage 1: Discover files
            logger.info("Stage 1: Discovering files...")
            if progress_callback:
                progress_callback("Discovering files", 0, 1)

            # Determine which files to index
            if incremental and self.change_detector:
                files = self._discover_changed_files(root_path, collection_name, stats)
            else:
                files = self._discover_files(root_path)

            stats.files_discovered = len(files)
            logger.info(f"Discovered {len(files)} files")

            if not files:
                logger.warning("No files found to index")
                stats.time_elapsed = time.time() - start_time
                return stats

            # Stage 2: Process files in batches
            logger.info(f"Stage 2: Processing files in batches of {self.batch_size}...")
            total_files = len(files)

            for batch_start in range(0, total_files, self.batch_size):
                batch_end = min(batch_start + self.batch_size, total_files)
                batch_files = files[batch_start:batch_end]

                if progress_callback:
                    progress_callback("Processing files", batch_end, total_files)

                # Process batch
                batch_stats = self._process_batch(
                    batch_files, collection_name, batch_start, total_files, root_path
                )

                # Update stats
                stats.files_indexed += batch_stats["files_indexed"]
                stats.files_failed += batch_stats["files_failed"]
                stats.chunks_created += batch_stats["chunks_created"]
                stats.embeddings_generated += batch_stats["embeddings_generated"]
                stats.symbols_extracted += batch_stats.get("symbols_extracted", 0)
                stats.dependencies_tracked += batch_stats.get("dependencies_tracked", 0)
                stats.symbol_usage_tracked += batch_stats.get("symbol_usage_tracked", 0)  # NEW
                stats.ast_parsing_time += batch_stats.get("ast_parsing_time", 0.0)
                stats.errors.extend(batch_stats["errors"])

            # Stage 3: Build dependency graph (NEW)
            if self.dependency_graph and self.enhancement_config.dependency_graph.enabled:
                logger.info("Stage 3: Building dependency graph...")
                if progress_callback:
                    progress_callback("Building dependency graph", 0, 1)

                try:
                    # Dependency graph is already populated during file processing
                    # Save it to disk for persistence
                    self.dependency_graph.save_to_file()
                    logger.info(f"Dependency graph built with {stats.dependencies_tracked} dependencies and saved to disk")
                except Exception as e:
                    logger.error(f"Error building dependency graph: {e}", exc_info=True)
                    stats.errors.append(f"Dependency graph error: {str(e)}")

            # Store last indexed reference if in incremental mode
            if incremental and self.change_detector:
                try:
                    current_ref = self.change_detector.get_current_ref()
                    metadata = IndexingMetadata.create_metadata(current_ref)

                    # Update collection metadata
                    collection = self.vector_store.get_or_create_collection(
                        collection_name,
                        embedding_dimension=self.embedding_provider.get_dimensions(),
                        model_name=self.embedding_provider.get_model_name(),
                        processor_type=processor_type,
                        codebase_path=root_path,
                    )
                    # Merge with existing metadata
                    existing_metadata = collection.metadata or {}
                    existing_metadata.update(metadata)
                    collection.modify(metadata=existing_metadata)

                    ref_type = "commit" if self.change_detector.is_git_based() else "timestamp"
                    logger.info(f"Stored last indexed {ref_type}: {current_ref}")
                except Exception as e:
                    logger.error(f"Failed to store indexing metadata: {e}")
                    stats.errors.append(f"Indexing metadata error: {str(e)}")

            # Final statistics
            stats.time_elapsed = time.time() - start_time

            # Resolve language-specific dependencies (NEW: Language-aware routing)
            if self.dependency_graph and self.symbol_table:
                try:
                    analysis_results = self.dependency_router.analyze_dependencies(
                        self.dependency_graph, self.symbol_table, detected_languages
                    )

                    if analysis_results["success"]:
                        total_resolved = analysis_results["total_resolved"]
                        if total_resolved > 0:
                            logger.info(f"✅ Resolved {total_resolved} dependencies across all languages")
                        else:
                            logger.info("No dependencies needed resolution")
                    else:
                        logger.warning("Some dependency analysis strategies failed")

                except Exception as e:
                    logger.warning(f"Error in dependency analysis routing: {e}")
                    import traceback
                    logger.debug(f"Traceback:\n{traceback.format_exc()}")

            logger.info("=" * 60)
            logger.info("Indexing complete!")
            logger.info(f"Files discovered: {stats.files_discovered}")
            logger.info(f"Files indexed: {stats.files_indexed}")
            logger.info(f"Files failed: {stats.files_failed}")
            logger.info(f"Chunks created: {stats.chunks_created}")
            logger.info(f"Embeddings generated: {stats.embeddings_generated}")
            if stats.symbols_extracted > 0:
                logger.info(f"Symbols extracted: {stats.symbols_extracted}")
            if stats.dependencies_tracked > 0:
                logger.info(f"Dependencies tracked: {stats.dependencies_tracked}")
            if stats.ast_parsing_time > 0:
                logger.info(f"AST parsing time: {stats.ast_parsing_time:.2f}s")
            if incremental:
                logger.info(f"Files changed: {stats.files_changed}")
                logger.info(f"Files added: {stats.files_added}")
                logger.info(f"Files deleted: {stats.files_deleted}")
            logger.info(f"Time elapsed: {stats.time_elapsed:.2f}s")
            logger.info("=" * 60)

            return stats

        except Exception as e:
            logger.error(f"Fatal error during indexing: {e}", exc_info=True)
            stats.errors.append(f"Fatal error: {str(e)}")
            stats.time_elapsed = time.time() - start_time
            return stats

    def _detect_project_languages(self, root_path: str, collection_name: str, processor_type: str) -> tuple[Optional[LanguageDetectionResult], str]:
        """
        Detect the primary language(s) of the project.

        Args:
            root_path: Root directory to analyze
            collection_name: Collection name for storing metadata
            processor_type: Initial processor type (may be refined based on detected language)

        Returns:
            Tuple of (LanguageDetectionResult or None if detection fails, refined processor_type)
        """
        try:
            root_path_obj = Path(root_path)
            result = self.language_detector.detect_languages(root_path_obj)

            logger.info(f"Language detection complete:")
            logger.info(f"  Primary language: {result.primary_language}")
            logger.info(f"  All languages: {result.languages}")
            logger.info(f"  Confidence: {result.confidence:.2f}")
            logger.info(f"  Config files found: {result.config_files_found}")

            # Store language detection results in collection metadata
            if self.vector_store:
                try:
                    collection = self.vector_store.get_or_create_collection(
                        collection_name,
                        embedding_dimension=self.embedding_provider.get_dimensions(),
                        model_name=self.embedding_provider.get_model_name(),
                        processor_type=processor_type,
                        codebase_path=root_path,
                    )

                    # Update metadata with language detection results
                    metadata = collection.metadata or {}
                    metadata.update({
                        "primary_language": result.primary_language,
                        "detected_languages": result.languages,
                        "language_confidence": result.confidence,
                        "config_files_found": result.config_files_found,
                        "language_detection_timestamp": time.time()
                    })

                    # Note: ChromaDB doesn't support direct metadata updates,
                    # but we'll store this for future use
                    logger.debug(f"Language detection metadata prepared for collection {collection_name}")

                except Exception as e:
                    logger.warning(f"Failed to store language detection metadata: {e}")

            return result, processor_type

        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            logger.debug(f"Language detection error details:", exc_info=True)
            return None, processor_type

    def _discover_files(self, root_path: str) -> List[Path]:
        """
        Discover all code files in the codebase with enhanced git filtering.

        Args:
            root_path: Root directory to search

        Returns:
            List of file paths
        """
        try:
            # Get untracked files if using Git-based change detection
            untracked_files = None
            if self.change_detector and self.change_detector.is_git_based():
                try:
                    # Get code file extensions for filtering
                    code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.rb', '.php'}
                    untracked_files = self.change_detector.strategy.detector.get_untracked_files(code_extensions)
                    logger.info(f"Found {len(untracked_files)} untracked files to filter")
                except Exception as e:
                    logger.warning(f"Failed to get untracked files, proceeding without filtering: {e}")
                    untracked_files = None

            # Discover files with untracked file filtering
            files = self.file_discovery.discover_files(root_path, untracked_files)
            return files
        except Exception as e:
            logger.error(f"Error discovering files: {e}", exc_info=True)
            return []

    def _discover_changed_files(
        self, root_path: str, collection_name: str, stats: IndexingStats
    ) -> List[Path]:
        """
        Discover changed files using unified change detector (Git or hash-based).

        Args:
            root_path: Root directory to search
            collection_name: Name of the collection
            stats: IndexingStats object to update

        Returns:
            List of changed file paths
        """
        try:
            # Get collection metadata to find last indexed reference
            # Note: processor_type not needed here, just retrieving metadata
            collection = self.vector_store.get_or_create_collection(
                collection_name,
                embedding_dimension=self.embedding_provider.get_dimensions(),
                model_name=self.embedding_provider.get_model_name(),
                processor_type=None,  # Not updating processor type here
                codebase_path=root_path,
            )

            last_ref = IndexingMetadata.get_last_indexed_commit(collection.metadata or {})

            if not last_ref:
                ref_type = "commit" if self.change_detector.is_git_based() else "timestamp"
                logger.info(f"No last indexed {ref_type} found - performing full indexing")
                return self._discover_files(root_path)

            ref_type = "commit" if self.change_detector.is_git_based() else "timestamp"
            logger.info(f"Last indexed {ref_type}: {last_ref}")

            # Get changed files using unified detector
            # Filter by code file extensions
            code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.rb', '.php'}
            changed_files_dict = self.change_detector.get_changed_files(
                last_ref, file_extensions=code_extensions
            )

            if not changed_files_dict:
                logger.info("No changes detected since last indexing")
                return []

            # Convert to Path objects and filter
            root = Path(root_path)
            changed_paths = []

            for file_path, change_type in changed_files_dict.items():
                full_path = root / file_path

                # Skip deleted files
                if change_type == "deleted":
                    stats.files_deleted += 1
                    logger.info(f"Skipping deleted file: {file_path}")
                    continue

                # Check if file exists
                if not full_path.exists():
                    logger.warning(f"Changed file not found: {full_path}")
                    continue

                changed_paths.append(full_path)

                # Update stats
                if change_type == "added":
                    stats.files_added += 1
                elif change_type in ("modified", "committed"):
                    stats.files_changed += 1

            logger.info(f"Changed files: {stats.files_changed}, Added: {stats.files_added}, Deleted: {stats.files_deleted}")

            return changed_paths

        except Exception as e:
            logger.error(f"Error discovering changed files: {e}", exc_info=True)
            logger.info("Falling back to full file discovery")
            return self._discover_files(root_path)

    def _process_batch(
        self,
        files: List[Path],
        collection_name: str,
        batch_start: int,
        total_files: int,
        root_path: str,  # NEW
    ) -> Dict[str, Any]:
        """
        Process a batch of files.

        Args:
            files: List of file paths to process
            collection_name: Name of the collection
            batch_start: Starting index of this batch
            total_files: Total number of files
            root_path: Root directory of the codebase

        Returns:
            Dictionary with batch statistics
        """
        batch_stats = {
            "files_indexed": 0,
            "files_failed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "symbols_extracted": 0,  # NEW
            "dependencies_tracked": 0,  # NEW
            "symbol_usage_tracked": 0,  # NEW
            "ast_parsing_time": 0.0,  # NEW
            "errors": [],
        }

        # Chunk files and process AST
        all_chunks = []
        for i, file_path in enumerate(files):
            try:
                logger.info(
                    f"Processing file {batch_start + i + 1}/{total_files}: {file_path}"
                )
                # Read file content with encoding detection
                content, encoding_used = read_file_with_encoding_detection(file_path)

                # Skip if file couldn't be read (binary or encoding error)
                if content is None:
                    logger.info(f"Skipping file {file_path}: binary or unreadable encoding")
                    batch_stats["files_failed"] += 1
                    batch_stats["errors"].append(
                        f"Skipped {file_path}: binary file or encoding error"
                    )
                    continue

                # Classify file as test, production, or DI configuration (NEW)
                file_type, test_penalty, file_category = FileClassifier.classify_file(str(file_path), content)
                file_metadata = {
                    "file_type": file_type,
                    "test_penalty": test_penalty,
                    "file_category": file_category  # NEW: di_configuration, test, or production
                }
                logger.info(f"Classified {file_path} as {file_type} (penalty={test_penalty}, category={file_category})")

                # Chunk file with file_metadata
                chunks = self.code_chunker.chunk_file(file_path, content, file_metadata)
                all_chunks.extend(chunks)
                batch_stats["files_indexed"] += 1
                batch_stats["chunks_created"] += len(chunks)

                # AST processing (NEW)
                if self.ast_processor and self.symbol_table:
                    ast_start = time.time()
                    try:
                        # Parse AST and extract symbols and dependencies
                        parse_result = self.ast_processor.parse_file(str(file_path), content)

                        if parse_result and parse_result.success:
                            # Make file path relative to root
                            relative_path = str(file_path).replace(str(root_path), "").lstrip("/\\")

                            # Update file_path in symbols to be relative
                            symbols_to_insert = []
                            for symbol in parse_result.symbols:
                                # Create a new Symbol with updated file_path
                                from ..ast_processing import Symbol
                                updated_symbol = Symbol(
                                    name=symbol.name,
                                    type=symbol.type,
                                    file_path=relative_path,
                                    line_number=symbol.line_number,
                                    column_number=symbol.column_number,
                                    end_line_number=symbol.end_line_number,
                                    end_column_number=symbol.end_column_number,
                                    signature=symbol.signature,
                                    documentation=symbol.documentation,
                                    scope=symbol.scope,
                                    is_exported=symbol.is_exported,
                                    parent_symbol=symbol.parent_symbol,
                                    metadata=symbol.metadata,
                                )
                                symbols_to_insert.append(updated_symbol)

                            # Batch insert symbols
                            if symbols_to_insert:
                                self.symbol_table.insert_symbols(symbols_to_insert)
                                batch_stats["symbols_extracted"] += len(symbols_to_insert)

                            # Update dependencies to use relative paths (FIXED: was using full paths)
                            dependencies_to_insert = []
                            if parse_result.dependencies:
                                from ..ast_processing import Dependency
                                for dep in parse_result.dependencies:
                                    # Create new Dependency with relative from_file path
                                    updated_dep = Dependency(
                                        from_file=relative_path,
                                        to_file=dep.to_file,
                                        imported_symbols=dep.imported_symbols,
                                        import_type=dep.import_type,
                                        line_number=dep.line_number,
                                        is_type_only=dep.is_type_only,
                                        metadata=dep.metadata,
                                    )
                                    dependencies_to_insert.append(updated_dep)

                            # Insert dependencies into symbol table (FIXED: was missing)
                            if dependencies_to_insert:
                                self.symbol_table.insert_dependencies(dependencies_to_insert)
                                logger.debug(f"Inserted {len(dependencies_to_insert)} dependencies into symbol table")

                            # Add dependencies to graph
                            if self.dependency_graph and dependencies_to_insert:
                                logger.info(f"Adding {len(dependencies_to_insert)} dependencies to graph for {relative_path}")
                                for dep in dependencies_to_insert:
                                    if dep.to_file.startswith("namespace:"):
                                        logger.info(f"  Adding NAMESPACE dependency: {dep.from_file} -> {dep.to_file}")
                                    self.dependency_graph.add_file_dependency(
                                        from_file=dep.from_file,
                                        to_file=dep.to_file,
                                        imported_symbols=dep.imported_symbols,
                                        import_type=dep.import_type,
                                        line_number=dep.line_number,
                                        is_type_only=dep.is_type_only,
                                        metadata=dep.metadata,  # Pass metadata for C# namespace resolution
                                    )

                                batch_stats["dependencies_tracked"] += len(dependencies_to_insert)

                            # Process symbol usage (NEW)
                            if hasattr(parse_result, 'symbol_usage') and parse_result.symbol_usage:
                                # Update symbol usage to use relative paths
                                usage_to_insert = []
                                from ..ast_processing.ast_processor import SymbolUsage
                                for usage in parse_result.symbol_usage:
                                    # Create new SymbolUsage with relative file paths
                                    updated_usage = SymbolUsage(
                                        from_symbol=usage.from_symbol,
                                        to_symbol=usage.to_symbol,
                                        usage_type=usage.usage_type,
                                        from_file=relative_path,
                                        to_file=relative_path,  # Assume same file for now
                                        line_number=usage.line_number,
                                        column_number=usage.column_number,
                                        metadata=usage.metadata,
                                    )
                                    usage_to_insert.append(updated_usage)

                                # Insert symbol usage into symbol table
                                if usage_to_insert:
                                    self.symbol_table.insert_symbol_usage(usage_to_insert)
                                    batch_stats["symbol_usage_tracked"] += len(usage_to_insert)
                                    logger.debug(f"Inserted {len(usage_to_insert)} symbol usage records into symbol table")

                                    # Add symbol usage to dependency graph
                                    if self.dependency_graph:
                                        usage_added = self.dependency_graph.add_symbol_usage_batch(usage_to_insert)
                                        logger.debug(f"Added {usage_added} symbol usage relationships to dependency graph")

                            # Update file metadata with embedding model info
                            model_name = self.embedding_provider.get_model_name()
                            dimensions = self.embedding_provider.get_dimensions()
                            self.symbol_table.update_file_metadata(
                                file_path=relative_path,
                                symbol_count=len(symbols_to_insert),
                                dependency_count=len(parse_result.dependencies),
                                embedding_model=model_name,
                                embedding_dimensions=dimensions,
                            )

                        batch_stats["ast_parsing_time"] += time.time() - ast_start

                    except Exception as e:
                        logger.warning(f"AST processing failed for {file_path}: {e}")
                        # Don't fail the entire file, just skip AST processing

            except Exception as e:
                logger.error(f"Error chunking file {file_path}: {e}")
                batch_stats["files_failed"] += 1
                batch_stats["errors"].append(f"Chunking error in {file_path}: {str(e)}")

        if not all_chunks:
            logger.warning("No chunks created from batch")
            return batch_stats

        # Generate embeddings
        try:
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
            chunk_texts = [chunk.content for chunk in all_chunks]
            embedding_results = self.embedding_provider.generate_embeddings_batch(
                chunk_texts
            )
            embeddings = [result.embedding for result in embedding_results]
            batch_stats["embeddings_generated"] = len(embeddings)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}", exc_info=True)
            batch_stats["errors"].append(f"Embedding error: {str(e)}")
            return batch_stats

        # Store in vector store
        try:
            logger.info(f"Storing {len(all_chunks)} chunks in vector store...")
            chunk_dicts = [
                {
                    "content": chunk.content,
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "chunk_type": chunk.chunk_type,
                    "language": chunk.language,
                    "metadata": chunk.metadata,  # BUG FIX 251: Include metadata (file_type, test_penalty, file_category)
                }
                for chunk in all_chunks
            ]

            # BUG FIX 251: Validate metadata exists and log sample for debugging
            if chunk_dicts:
                sample_metadata = chunk_dicts[0].get("metadata", {})
                file_type = sample_metadata.get("file_type", "MISSING")
                logger.debug(f"Sample chunk metadata - file_type: {file_type}, keys: {list(sample_metadata.keys())}")

                # Count test vs production files
                test_count = sum(1 for cd in chunk_dicts if cd.get("metadata", {}).get("file_type") == "test")
                prod_count = sum(1 for cd in chunk_dicts if cd.get("metadata", {}).get("file_type") == "production")
                logger.info(f"Indexing batch: {prod_count} production chunks, {test_count} test chunks")

            # Pass embedding model name for dimension tracking
            model_name = self.embedding_provider.get_model_name()
            self.vector_store.add_chunks(
                collection_name, chunk_dicts, embeddings, model_name=model_name
            )
        except Exception as e:
            logger.error(f"Error storing embeddings: {e}", exc_info=True)
            batch_stats["errors"].append(f"Storage error: {str(e)}")
            return batch_stats

        return batch_stats

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with collection statistics
        """
        return self.vector_store.get_stats(collection_name)

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            True if successful, False otherwise
        """
        return self.vector_store.delete_collection(collection_name)


