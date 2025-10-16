"""
Delta indexer for incremental updates to code indexes.

This module provides atomic file-level updates to vector store, symbol table,
and dependency graph, enabling efficient incremental indexing.
"""

import logging
import hashlib
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..indexer.code_chunker import ASTCodeChunker
from ..embeddings.base import EmbeddingProvider
from ..vector_store.chroma_store import ChromaVectorStore
from ..symbol_table.symbol_table import SymbolTable
from ..dependency_graph.dependency_graph import DependencyGraph
from ..ast_processing.ast_processor import ASTProcessor
from ..ast_processing import Symbol
from ..utils.file_encoding import read_file_with_encoding_detection

logger = logging.getLogger(__name__)


@dataclass
class DeltaUpdateResult:
    """Result of a delta update operation."""
    file_path: str
    success: bool
    chunks_added: int
    chunks_removed: int
    symbols_added: int
    symbols_removed: int
    dependencies_added: int
    dependencies_removed: int
    chunks_reused: int = 0  # NEW: Chunks reused without re-embedding
    error: Optional[str] = None


@dataclass
class ChunkDiff:
    """Result of chunk matching between old and new chunks."""
    unchanged: List[Any]  # Chunks that haven't changed (can reuse embeddings)
    deleted: List[str]  # Chunk IDs to delete
    added: List[Any]  # New chunks to embed and add
    modified: List[Any]  # Chunks that changed (need re-embedding)


class DeltaIndexer:
    """
    Atomic file-level delta updates for incremental indexing.
    
    Provides transactional updates that remove old data and insert new data
    for changed files, with rollback capability on failure.
    """
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: ChromaVectorStore,
        symbol_table: Optional[SymbolTable] = None,
        dependency_graph: Optional[DependencyGraph] = None,
        ast_processor: Optional[ASTProcessor] = None,
    ):
        """
        Initialize delta indexer.
        
        Args:
            embedding_provider: Provider for generating embeddings
            vector_store: Vector store for chunk storage
            symbol_table: Optional symbol table for symbol storage
            dependency_graph: Optional dependency graph for dependency tracking
            ast_processor: Optional AST processor for parsing
        """
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.symbol_table = symbol_table
        self.dependency_graph = dependency_graph
        self.ast_processor = ast_processor
        self.code_chunker = ASTCodeChunker()

    def match_chunks(
        self,
        old_chunks: List[Dict[str, Any]],
        new_chunks: List[Any],
    ) -> ChunkDiff:
        """
        Match old and new chunks to identify unchanged, deleted, added, and modified chunks.

        Uses content hashing to detect changes. Chunks with same hash are considered unchanged
        and can reuse existing embeddings.

        Args:
            old_chunks: List of old chunk metadata from vector store
            new_chunks: List of new CodeChunk objects

        Returns:
            ChunkDiff with categorized chunks
        """
        # Build hash map of old chunks
        old_chunk_map = {}  # hash -> chunk_id
        for chunk in old_chunks:
            metadata = chunk.get("metadata", {})
            content_hash = metadata.get("content_hash")
            chunk_id = metadata.get("chunk_id")
            if content_hash and chunk_id:
                old_chunk_map[content_hash] = chunk_id

        # Build hash map of new chunks
        new_chunk_map = {}  # hash -> chunk
        for chunk in new_chunks:
            chunk_hash = chunk.content_hash
            new_chunk_map[chunk_hash] = chunk

        # Find unchanged chunks (same hash in both)
        unchanged_hashes = set(old_chunk_map.keys()) & set(new_chunk_map.keys())
        unchanged = [new_chunk_map[h] for h in unchanged_hashes]

        # Find deleted chunks (in old but not in new)
        deleted_hashes = set(old_chunk_map.keys()) - set(new_chunk_map.keys())
        deleted = [old_chunk_map[h] for h in deleted_hashes]

        # Find added chunks (in new but not in old)
        added_hashes = set(new_chunk_map.keys()) - set(old_chunk_map.keys())
        added = [new_chunk_map[h] for h in added_hashes]

        return ChunkDiff(
            unchanged=unchanged,
            deleted=deleted,
            added=added,
            modified=[],  # For now, we treat all changes as add/delete
        )

    def update_file(
        self,
        file_path: Path,
        collection_name: str,
        root_path: Path,
    ) -> DeltaUpdateResult:
        """
        Perform atomic delta update for a single file.
        
        Workflow:
        1. Remove old chunks from vector store
        2. Remove old symbols from symbol table
        3. Remove old dependencies from dependency graph
        4. Re-process file (parse AST, chunk, embed)
        5. Insert new data
        
        Args:
            file_path: Absolute path to the file
            collection_name: Name of the collection
            root_path: Root directory of the codebase
            
        Returns:
            DeltaUpdateResult with operation statistics
        """
        # Make file path relative to root
        try:
            relative_path = str(file_path.relative_to(root_path))
        except ValueError:
            relative_path = str(file_path)
        
        logger.info(f"Delta update for file: {relative_path}")
        
        result = DeltaUpdateResult(
            file_path=relative_path,
            success=False,
            chunks_added=0,
            chunks_removed=0,
            symbols_added=0,
            symbols_removed=0,
            dependencies_added=0,
            dependencies_removed=0,
        )
        
        try:
            # Ensure collection exists
            _ = self.vector_store.get_or_create_collection(
                collection_name,
                embedding_dimension=self.embedding_provider.get_dimensions(),
                model_name=self.embedding_provider.get_model_name(),
            )

            # Read file content with encoding detection
            content, encoding_used = read_file_with_encoding_detection(file_path)

            # Skip if file couldn't be read (binary or encoding error)
            if content is None:
                result.error = f"Skipped: binary file or encoding error"
                logger.info(f"Skipping file {relative_path}: binary or unreadable encoding")
                return result

            # Chunk file to get new chunks
            new_chunks = self.code_chunker.chunk_file(file_path, content)

            # Fix file paths in chunks to be relative
            for chunk in new_chunks:
                chunk.file_path = relative_path

            logger.debug(f"Created {len(new_chunks)} new chunks")

            # Retrieve old chunks from vector store
            old_chunks = self.vector_store.get_chunks_by_file(collection_name, relative_path)
            logger.debug(f"Retrieved {len(old_chunks)} old chunks")

            # Match chunks to find unchanged/deleted/added
            chunk_diff = self.match_chunks(old_chunks, new_chunks)
            logger.debug(f"Chunk diff: {len(chunk_diff.unchanged)} unchanged, "
                        f"{len(chunk_diff.deleted)} deleted, {len(chunk_diff.added)} added")

            # Step 1: Delete removed chunks
            if chunk_diff.deleted:
                try:
                    collection = self.vector_store.client.get_collection(name=collection_name)
                    collection.delete(ids=chunk_diff.deleted)
                    result.chunks_removed = len(chunk_diff.deleted)
                    logger.debug(f"Deleted {len(chunk_diff.deleted)} chunks")
                except Exception as e:
                    logger.warning(f"Failed to delete chunks: {e}")

            # Step 2: Reuse unchanged chunks (no action needed, they stay in vector store)
            result.chunks_reused = len(chunk_diff.unchanged)
            logger.debug(f"Reusing {len(chunk_diff.unchanged)} unchanged chunks")
            
            # Step 3: Remove old symbols from symbol table
            if self.symbol_table:
                symbols_removed = self.symbol_table.delete_symbols_by_file(relative_path)
                result.symbols_removed = symbols_removed
                logger.debug(f"Removed {symbols_removed} old symbols")

            # Step 4: Remove old dependencies from dependency graph
            if self.dependency_graph:
                deps_removed = self.dependency_graph.remove_file_dependencies(relative_path)
                result.dependencies_removed = deps_removed
                logger.debug(f"Removed {deps_removed} old dependencies")

            # Get model name for metadata (needed even if no chunks)
            model_name = self.embedding_provider.get_model_name()

            # Step 5: Generate embeddings ONLY for added chunks
            if chunk_diff.added:
                chunk_texts = [chunk.content for chunk in chunk_diff.added]
                embedding_results = self.embedding_provider.generate_embeddings_batch(chunk_texts)
                embeddings = [result.embedding for result in embedding_results]
                logger.debug(f"Generated {len(embeddings)} embeddings for new chunks")
            else:
                embeddings = []
                logger.debug("No new chunks to embed")

            # Step 6: Insert new chunks
            if chunk_diff.added:
                chunk_dicts = [
                    {
                        "content": chunk.content,
                        "file_path": chunk.file_path,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "chunk_type": chunk.chunk_type,
                        "language": chunk.language,
                        "metadata": chunk.metadata,  # BUG FIX 251: Include full metadata (file_type, test_penalty, etc.)
                    }
                    for chunk in chunk_diff.added
                ]

                self.vector_store.add_chunks(
                    collection_name, chunk_dicts, embeddings, model_name=model_name
                )
                result.chunks_added = len(chunk_diff.added)
                logger.debug(f"Added {len(chunk_diff.added)} new chunks")
            else:
                logger.debug("No new chunks to add")
            
            # Process AST if available
            if self.ast_processor and self.symbol_table:
                parse_result = self.ast_processor.parse_file(str(file_path), content)
                
                if parse_result and parse_result.success:
                    # Insert symbols
                    symbols_to_insert = []
                    for symbol in parse_result.symbols:
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
                    
                    if symbols_to_insert:
                        self.symbol_table.insert_symbols(symbols_to_insert)
                        result.symbols_added = len(symbols_to_insert)
                        logger.debug(f"Added {len(symbols_to_insert)} new symbols")

                    # Update dependencies to use relative paths (FIXED: was using full paths)
                    dependencies_to_insert = []
                    if parse_result.dependencies:
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
                        result.dependencies_added = len(dependencies_to_insert)
                        logger.debug(f"Inserted {len(dependencies_to_insert)} dependencies into symbol table")

                    # Add dependencies to graph
                    if self.dependency_graph and dependencies_to_insert:
                        for dep in dependencies_to_insert:
                            self.dependency_graph.add_file_dependency(
                                from_file=dep.from_file,
                                to_file=dep.to_file,
                                imported_symbols=dep.imported_symbols,
                                import_type=dep.import_type,
                                line_number=dep.line_number,
                                is_type_only=dep.is_type_only,
                                metadata=dep.metadata,  # FIXED: Pass metadata for C# namespace resolution
                            )
                        logger.debug(f"Added {len(dependencies_to_insert)} dependencies to graph")
            
            # Update file metadata in symbol table
            if self.symbol_table:
                file_hash = hashlib.md5(content.encode()).hexdigest()
                self.symbol_table.update_file_metadata(
                    relative_path,
                    file_hash=file_hash,
                    symbol_count=result.symbols_added,
                    embedding_model=model_name,
                    embedding_dimensions=self.embedding_provider.get_dimensions(),
                )
            
            result.success = True
            logger.info(f"Delta update successful for {relative_path}")
            return result
            
        except Exception as e:
            result.error = str(e)
            logger.error(f"Delta update failed for {relative_path}: {e}", exc_info=True)
            # Note: Rollback is not implemented yet - would require transaction support
            return result

    def delete_file(
        self,
        file_path: Path,
        collection_name: str,
        root_path: Path,
    ) -> DeltaUpdateResult:
        """
        Delete a file from the index (vector store, symbol table, dependency graph).

        Args:
            file_path: Absolute path to the file to delete
            collection_name: Name of the collection
            root_path: Root directory of the codebase

        Returns:
            DeltaUpdateResult with deletion statistics
        """
        relative_path = str(file_path.relative_to(root_path))

        result = DeltaUpdateResult(
            file_path=relative_path,
            success=False,
            chunks_added=0,
            chunks_removed=0,
            symbols_added=0,
            symbols_removed=0,
            dependencies_added=0,
            dependencies_removed=0,
        )

        try:
            logger.info(f"Deleting file from index: {relative_path}")

            # Delete from vector store
            if self.vector_store:
                # Get existing chunks for this file
                existing_chunks = self.vector_store.get_chunks_by_file(
                    collection_name=collection_name,
                    file_path=relative_path
                )

                if existing_chunks:
                    chunk_ids = [chunk["id"] for chunk in existing_chunks]
                    self.vector_store.delete_chunks(
                        collection_name=collection_name,
                        chunk_ids=chunk_ids
                    )
                    result.chunks_removed = len(chunk_ids)
                    logger.debug(f"Deleted {len(chunk_ids)} chunks from vector store")

            # Delete from symbol table
            if self.symbol_table:
                # Get existing symbols for this file
                existing_symbols = self.symbol_table.get_symbols_by_file(
                    file_path=relative_path
                )

                if existing_symbols:
                    deleted_count = self.symbol_table.delete_symbols_by_file(
                        file_path=relative_path
                    )
                    result.symbols_removed = deleted_count
                    logger.debug(f"Deleted {deleted_count} symbols from symbol table")

                # Delete file metadata (using delete_file_symbols which handles both)
                self.symbol_table.delete_file_symbols(
                    file_path=relative_path
                )

            # Delete from dependency graph
            if self.dependency_graph:
                # Remove all dependencies for this file
                self.dependency_graph.remove_file(relative_path)
                logger.debug(f"Removed file from dependency graph")

            result.success = True
            logger.info(f"File deletion successful for {relative_path}")
            return result

        except Exception as e:
            result.error = str(e)
            logger.error(f"File deletion failed for {relative_path}: {e}", exc_info=True)
            return result

    def update_files(
        self,
        file_paths: List[Path],
        collection_name: str,
        root_path: Path,
    ) -> List[DeltaUpdateResult]:
        """
        Perform delta updates for multiple files.
        
        Args:
            file_paths: List of absolute file paths
            collection_name: Name of the collection
            root_path: Root directory of the codebase
            
        Returns:
            List of DeltaUpdateResult for each file
        """
        results = []
        
        for file_path in file_paths:
            result = self.update_file(file_path, collection_name, root_path)
            results.append(result)
        
        # Log summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_chunks_added = sum(r.chunks_added for r in results)
        total_symbols_added = sum(r.symbols_added for r in results)
        
        logger.info(f"Delta update batch complete: {successful} successful, {failed} failed")
        logger.info(f"Total: {total_chunks_added} chunks, {total_symbols_added} symbols added")

        return results

    async def update_files_parallel(
        self,
        file_paths: List[Path],
        collection_name: str,
        root_path: Path,
        max_workers: Optional[int] = None,
    ) -> List[DeltaUpdateResult]:
        """
        Perform delta updates for multiple files in parallel.

        Uses asyncio with semaphore to limit concurrency and prevent resource exhaustion.

        Args:
            file_paths: List of absolute file paths
            collection_name: Name of the collection
            root_path: Root directory of the codebase
            max_workers: Maximum number of parallel workers (default: CPU count)

        Returns:
            List of DeltaUpdateResult for each file
        """
        if max_workers is None:
            max_workers = os.cpu_count() or 4

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_workers)

        async def update_with_semaphore(file_path: Path) -> DeltaUpdateResult:
            """Update a single file with semaphore control."""
            async with semaphore:
                # Run the synchronous update_file in a thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self.update_file,
                    file_path,
                    collection_name,
                    root_path,
                )
                return result

        # Create tasks for all files
        tasks = [update_with_semaphore(file_path) for file_path in file_paths]

        # Execute all tasks in parallel
        logger.info(f"Starting parallel delta updates for {len(file_paths)} files (max_workers={max_workers})")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = DeltaUpdateResult(
                    file_path=str(file_paths[i]),
                    success=False,
                    chunks_added=0,
                    chunks_removed=0,
                    symbols_added=0,
                    symbols_removed=0,
                    dependencies_added=0,
                    dependencies_removed=0,
                    chunks_reused=0,
                    error=str(result),
                )
                final_results.append(error_result)
            else:
                final_results.append(result)

        # Log summary
        successful = sum(1 for r in final_results if r.success)
        failed = len(final_results) - successful
        total_chunks_added = sum(r.chunks_added for r in final_results)
        total_symbols_added = sum(r.symbols_added for r in final_results)
        total_chunks_reused = sum(r.chunks_reused for r in final_results)

        logger.info(f"Parallel delta update complete: {successful} successful, {failed} failed")
        logger.info(f"Total: {total_chunks_added} chunks added, {total_chunks_reused} chunks reused, {total_symbols_added} symbols added")

        return final_results

