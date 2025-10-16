"""
Query processing for converting natural language queries into embeddings.
"""

import logging
import hashlib
from typing import Dict, Optional
from ..embeddings.base import EmbeddingProvider, EmbeddingResult

logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Process natural language queries and convert them to embeddings for semantic search.
    """

    def __init__(self, embedding_provider: EmbeddingProvider, enable_cache: bool = True):
        """
        Initialize the query processor.

        Args:
            embedding_provider: Provider for generating embeddings
            enable_cache: Whether to cache query embeddings
        """
        self.embedding_provider = embedding_provider
        self.enable_cache = enable_cache
        self._cache: Dict[str, EmbeddingResult] = {}

        logger.info("Initialized query processor")

    def process_query(self, query: str) -> EmbeddingResult:
        """
        Process a query and convert it to an embedding.

        Args:
            query: Natural language query string

        Returns:
            EmbeddingResult with the query embedding

        Raises:
            ValueError: If query is empty or invalid
        """
        # Validate query
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Preprocess query
        processed_query = self._preprocess_query(query)

        # Check cache
        if self.enable_cache:
            cache_key = self._get_cache_key(processed_query)
            if cache_key in self._cache:
                logger.debug(f"Cache hit for query: {processed_query[:50]}...")
                return self._cache[cache_key]

        # Generate embedding
        logger.info(f"Processing query: {processed_query[:100]}...")
        try:
            result = self.embedding_provider.generate_embedding(processed_query)

            # Cache result
            if self.enable_cache:
                cache_key = self._get_cache_key(processed_query)
                self._cache[cache_key] = result
                logger.debug(f"Cached query embedding (cache size: {len(self._cache)})")

            return result

        except Exception as e:
            logger.error(f"Failed to process query: {e}", exc_info=True)
            raise ValueError(f"Failed to generate embedding for query: {str(e)}")

    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess the query text.

        Args:
            query: Raw query string

        Returns:
            Preprocessed query string
        """
        # Strip whitespace
        processed = query.strip()

        # Normalize whitespace (replace multiple spaces with single space)
        processed = " ".join(processed.split())

        # Note: We don't lowercase or remove special characters because
        # modern embedding models are case-sensitive and handle punctuation well

        return processed

    def _get_cache_key(self, query: str) -> str:
        """
        Generate a cache key for a query.

        Args:
            query: Preprocessed query string

        Returns:
            Cache key (hash of query)
        """
        return hashlib.sha256(query.encode()).hexdigest()

    def clear_cache(self) -> None:
        """Clear the query cache."""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared query cache ({cache_size} entries)")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self._cache),
            "enabled": self.enable_cache,
        }

    def expand_query(self, query: str) -> str:
        """
        Optionally expand the query with synonyms or related terms.

        This is a placeholder for future query expansion functionality.
        Currently just returns the original query.

        Args:
            query: Original query string

        Returns:
            Expanded query string
        """
        # Future enhancement: Add query expansion logic
        # - Add programming language synonyms (e.g., "function" -> "method", "def")
        # - Add common abbreviations (e.g., "API" -> "Application Programming Interface")
        # - Add related terms based on context

        return query


