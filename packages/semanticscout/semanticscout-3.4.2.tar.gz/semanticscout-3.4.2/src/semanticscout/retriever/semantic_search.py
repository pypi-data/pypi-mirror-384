"""
Semantic search functionality for finding relevant code chunks.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..vector_store.chroma_store import ChromaVectorStore
from ..retriever.query_processor import QueryProcessor
from ..retriever.context_expander import ContextExpander, ExpandedResult

logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a single search result."""

    def __init__(
        self,
        content: str,
        file_path: str,
        start_line: int,
        end_line: int,
        chunk_type: str,
        language: str,
        similarity_score: float,
        metadata: Optional[Dict[str, Any]] = None,  # NEW
        expanded_from: Optional[List[str]] = None,  # NEW
    ):
        self.content = content
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.chunk_type = chunk_type
        self.language = language
        self.similarity_score = similarity_score
        self.metadata = metadata or {}  # NEW
        self.expanded_from = expanded_from or []  # NEW

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "content": self.content,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "chunk_type": self.chunk_type,
            "language": self.language,
            "similarity_score": self.similarity_score,
            "metadata": self.metadata,  # NEW
            "expanded_from": self.expanded_from,  # NEW
        }

    def __repr__(self) -> str:
        return (
            f"SearchResult(file={Path(self.file_path).name}, "
            f"lines={self.start_line}-{self.end_line}, "
            f"similarity={self.similarity_score:.4f})"
        )


class SemanticSearcher:
    """
    Semantic search for finding relevant code chunks using natural language queries.
    """

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        query_processor: QueryProcessor,
        context_expander: Optional[ContextExpander] = None,  # NEW
    ):
        """
        Initialize the semantic searcher.

        Args:
            vector_store: Vector store for similarity search
            query_processor: Query processor for converting queries to embeddings
            context_expander: Optional context expander for result enhancement
        """
        self.vector_store = vector_store
        self.query_processor = query_processor
        self.context_expander = context_expander  # NEW

        logger.info("Initialized semantic searcher")

    def search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        min_similarity: float = 0.0,
        file_pattern: Optional[str] = None,
        language: Optional[str] = None,
        expansion_level: str = "none",  # NEW: 'none', 'low', 'medium', 'high'
        exclude_test_files: bool = True,  # NEW: Filter out test files by default
    ) -> List[SearchResult]:
        """
        Search for code chunks relevant to the query.

        Args:
            query: Natural language query
            collection_name: Name of the collection to search
            top_k: Number of results to return (default: 5)
            min_similarity: Minimum similarity score (0-1, default: 0.0)
            file_pattern: Optional regex pattern to filter by file path
            language: Optional language filter (e.g., "python", "javascript")
            expansion_level: Context expansion level ('none', 'low', 'medium', 'high')
            exclude_test_files: If True (default), exclude test files from results

        Returns:
            List of SearchResult objects, sorted by similarity (highest first)

        Raises:
            ValueError: If query is invalid or collection doesn't exist
        """
        # Validate inputs
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if top_k < 1 or top_k > 100:
            raise ValueError("top_k must be between 1 and 100")

        if min_similarity < 0.0 or min_similarity > 1.0:
            raise ValueError("min_similarity must be between 0.0 and 1.0")

        # Check if collection exists
        if not self.vector_store.collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist")

        logger.info(
            f"Searching collection '{collection_name}' for: {query[:100]}..."
        )

        # Process query to get embedding
        try:
            query_result = self.query_processor.process_query(query)
            query_embedding = query_result.embedding
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise ValueError(f"Failed to process query: {str(e)}")

        # Build metadata filter
        metadata_filter = self._build_metadata_filter(language, exclude_test_files)

        # Log filtering status
        if exclude_test_files:
            logger.info("Filtering test files from results")
        else:
            logger.info("Including test files in results")

        # Search vector store
        raw_results = self.vector_store.search(
            collection_name=collection_name,
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more results for filtering
            filter_metadata=metadata_filter,
        )

        # Convert to SearchResult objects
        results = []
        for raw_result in raw_results:
            metadata = raw_result["metadata"]
            
            # Apply file pattern filter
            if file_pattern and not self._matches_file_pattern(
                metadata.get("file_path", ""), file_pattern
            ):
                continue

            # Apply minimum similarity filter
            similarity = raw_result["similarity"]
            if similarity < min_similarity:
                continue

            result = SearchResult(
                content=raw_result["content"],
                file_path=metadata.get("file_path", ""),
                start_line=int(metadata.get("start_line", 0)),
                end_line=int(metadata.get("end_line", 0)),
                chunk_type=metadata.get("chunk_type", ""),
                language=metadata.get("language", ""),
                similarity_score=similarity,
                metadata=metadata,  # NEW: Include full metadata
            )
            results.append(result)

            # Stop if we have enough results
            if len(results) >= top_k:
                break

        # Rank results (already sorted by similarity from vector store)
        ranked_results = self._rank_results(results)

        # Apply context expansion if enabled (NEW)
        if expansion_level != "none" and self.context_expander:
            expanded_results = self._expand_results(
                ranked_results, collection_name, expansion_level
            )
            logger.info(
                f"Found {len(ranked_results)} results, expanded to {len(expanded_results)} chunks"
            )

            # Apply deduplication AFTER expansion to remove duplicate files (NEW)
            final_results = self._deduplicate_results(expanded_results)
            if len(final_results) != len(expanded_results):
                logger.info(
                    f"Deduplicated {len(expanded_results)} expanded results to {len(final_results)} unique files"
                )

            return final_results

        # Apply deduplication for non-expanded results (NEW)
        deduplicated_results = self._deduplicate_results(ranked_results)
        if len(deduplicated_results) != len(ranked_results):
            logger.info(
                f"Deduplicated {len(ranked_results)} results to {len(deduplicated_results)} unique files"
            )

        logger.info(f"Found {len(deduplicated_results)} results")

        return deduplicated_results

    def _build_metadata_filter(
        self,
        language: Optional[str] = None,
        exclude_test_files: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Build metadata filter for vector store search.

        Args:
            language: Optional language filter
            exclude_test_files: If True, exclude test files

        Returns:
            Metadata filter dictionary or None
        """
        filters = {}

        if language:
            filters["language"] = language

        if exclude_test_files:
            # BUG FIX 251: ChromaDB where clause to exclude test files
            filters["file_type"] = {"$ne": "test"}
            logger.debug(f"Applying test file filter: file_type != 'test'")

        if filters:
            logger.debug(f"Metadata filter: {filters}")

        return filters if filters else None

    def _matches_file_pattern(self, file_path: str, pattern: str) -> bool:
        """
        Check if file path matches the given regex pattern.

        Args:
            file_path: File path to check
            pattern: Regex pattern

        Returns:
            True if matches, False otherwise
        """
        try:
            return bool(re.search(pattern, file_path))
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            return False

    def _rank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Rank and sort search results, applying test file penalty and DI config boost.

        Applies test_penalty to similarity scores for test files to ensure
        production code ranks higher than test code with similar relevance.

        Applies DI config boost to DI configuration files (Startup.cs, Program.cs, etc.)
        to ensure they rank higher in architectural queries.

        Args:
            results: List of search results

        Returns:
            Ranked list of search results, sorted by adjusted similarity
        """
        # Apply test file penalty and DI config boost to similarity scores
        for result in results:
            # Store original similarity score
            original_similarity = result.similarity_score
            result.metadata["original_similarity"] = original_similarity

            # Start with original score
            adjusted_similarity = original_similarity

            # Check if result has test_penalty metadata
            test_penalty = result.metadata.get("test_penalty")

            if test_penalty is not None and test_penalty < 1.0:
                # Apply penalty to similarity score
                adjusted_similarity = original_similarity * test_penalty
                result.metadata["test_penalty_applied"] = True

                logger.debug(
                    f"Applied test penalty {test_penalty} to {result.file_path}: "
                    f"{original_similarity:.4f} -> {adjusted_similarity:.4f}"
                )
            else:
                result.metadata["test_penalty_applied"] = False

            # Check if result is a DI configuration file (NEW)
            file_category = result.metadata.get("file_category")

            if file_category == "di_configuration":
                # Apply DI config boost (2.0x)
                DI_CONFIG_BOOST = 2.0
                adjusted_similarity = adjusted_similarity * DI_CONFIG_BOOST
                result.metadata["di_config_boost_applied"] = True

                logger.info(
                    f"Applied DI config boost {DI_CONFIG_BOOST} to {result.file_path}: "
                    f"{original_similarity:.4f} -> {adjusted_similarity:.4f}"
                )
            else:
                result.metadata["di_config_boost_applied"] = False

            # Store final adjusted similarity
            result.similarity_score = adjusted_similarity
            result.metadata["adjusted_similarity"] = adjusted_similarity

        # Sort by adjusted similarity (descending)
        ranked_results = sorted(
            results,
            key=lambda r: r.similarity_score,
            reverse=True
        )

        return ranked_results

    def _expand_results(
        self,
        results: List[SearchResult],
        collection_name: str,
        expansion_level: str,
    ) -> List[SearchResult]:
        """
        Expand search results with context.

        Args:
            results: Original search results
            collection_name: Collection name
            expansion_level: Expansion level ('low', 'medium', 'high')

        Returns:
            List of expanded search results
        """
        expanded_results = []

        for result in results:
            # Convert SearchResult to chunk dict for context expander
            chunk = {
                "content": result.content,
                "chunk_id": result.metadata.get("chunk_id", ""),
                "metadata": result.metadata,
            }

            # Expand chunk
            expanded = self.context_expander.expand_chunk(
                chunk, collection_name, expansion_level
            )

            # Convert merged chunks back to SearchResult objects
            for merged_chunk in expanded.merged_chunks:
                expanded_result = SearchResult(
                    content=merged_chunk.content,
                    file_path=merged_chunk.file_path,
                    start_line=merged_chunk.start_line,
                    end_line=merged_chunk.end_line,
                    chunk_type=merged_chunk.metadata.get("chunk_type", ""),
                    language=merged_chunk.language,
                    similarity_score=result.similarity_score,  # Keep original similarity
                    metadata=merged_chunk.metadata,
                    expanded_from=merged_chunk.source_chunk_ids,
                )
                expanded_results.append(expanded_result)

        return expanded_results

    def format_results(
        self, results: List[SearchResult], max_content_length: int = 200
    ) -> str:
        """
        Format search results as a human-readable string.

        Args:
            results: List of search results
            max_content_length: Maximum length of content preview

        Returns:
            Formatted string
        """
        if not results:
            return "No results found."

        output = []
        output.append(f"Found {len(results)} results:\n")

        for i, result in enumerate(results):
            output.append(f"\n{i+1}. {Path(result.file_path).name}")
            output.append(f"   Lines: {result.start_line}-{result.end_line}")
            output.append(f"   Type: {result.chunk_type}")
            output.append(f"   Language: {result.language}")
            output.append(f"   Similarity: {result.similarity_score:.4f}")

            # Content preview
            content_preview = result.content.strip()
            if len(content_preview) > max_content_length:
                content_preview = content_preview[:max_content_length] + "..."

            output.append(f"   Code:\n      {content_preview}")

        return "\n".join(output)

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Deduplicate search results to ensure each file appears only once.

        When multiple chunks from the same file are found, this method:
        1. Groups chunks by file path
        2. For each file, keeps only the highest-scoring chunk
        3. Merges metadata from all chunks of the same file

        Args:
            results: List of SearchResult objects to deduplicate

        Returns:
            List of deduplicated SearchResult objects, one per unique file
        """
        if not results:
            return results

        # Group results by file path
        file_groups = {}
        for result in results:
            file_path = result.file_path
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(result)

        # For each file, keep only the highest-scoring chunk
        deduplicated = []
        for file_path, chunks in file_groups.items():
            if len(chunks) == 1:
                # Single chunk, no deduplication needed
                deduplicated.append(chunks[0])
            else:
                # Multiple chunks from same file - keep the highest scoring one
                best_chunk = max(chunks, key=lambda c: c.similarity_score)

                # Add metadata about merged chunks
                best_chunk.metadata = best_chunk.metadata.copy() if best_chunk.metadata else {}
                best_chunk.metadata["chunks_merged"] = len(chunks)
                best_chunk.metadata["merged_line_ranges"] = [
                    f"{c.start_line}-{c.end_line}" for c in chunks
                ]

                logger.debug(
                    f"Deduplicated {len(chunks)} chunks from {file_path}, "
                    f"kept chunk with score {best_chunk.similarity_score:.4f}"
                )

                deduplicated.append(best_chunk)

        # Sort by similarity score (highest first) to maintain ranking
        deduplicated.sort(key=lambda r: r.similarity_score, reverse=True)

        return deduplicated


