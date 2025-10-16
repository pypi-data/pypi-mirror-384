"""
Query Intent Tracker for SemanticScout.

This module provides functionality to track query intents and relevance feedback
to build a meta-learning system for improved search performance over time.
"""

import json
import logging
import uuid
import time
import functools
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass

from ..vector_store.chroma_store import ChromaVectorStore
from ..retriever.query_processor import QueryProcessor
from ..embeddings.base import EmbeddingProvider
from .exceptions import QueryTrackingError, ValidationError, StorageError

logger = logging.getLogger(__name__)


def retry_on_storage_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry operations on transient storage errors.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except StorageError as e:
                    last_exception = e
                    if attempt < max_retries:
                        # Check if this is a retryable error
                        error_msg = str(e).lower()
                        retryable_errors = [
                            'connection', 'timeout', 'temporary', 'transient',
                            'network', 'unavailable', 'busy'
                        ]

                        if any(retryable in error_msg for retryable in retryable_errors):
                            logger.warning(
                                f"Retryable storage error in {func.__name__} (attempt {attempt + 1}/{max_retries}): {e}"
                            )
                            time.sleep(current_delay)
                            current_delay *= backoff
                            continue

                    # Non-retryable error or max retries exceeded
                    logger.error(f"Storage error in {func.__name__} after {attempt + 1} attempts: {e}")
                    raise
                except ValidationError:
                    # Don't retry validation errors
                    raise
                except Exception as e:
                    # Don't retry unexpected errors
                    logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                    raise

            # This should never be reached, but just in case
            raise last_exception

        return wrapper
    return decorator


@dataclass
class QueryIntentResult:
    """Result of storing a query intent."""
    intent_id: str
    query_intent: str
    relevance_score: float
    timestamp: str
    collection_name: Optional[str] = None
    file_change_count: int = 0
    query_type: str = "search"


@dataclass
class SimilarIntent:
    """A similar intent found in historical data."""
    intent_id: str
    query_intent: str
    relevance_score: float
    similarity_score: float
    file_changes: List[str]
    timestamp: str
    collection_name: Optional[str] = None
    query_type: str = "search"

    @property
    def file_change_count(self) -> int:
        """Get the number of file changes."""
        return len(self.file_changes)


class QueryIntentValidator:
    """Validator for query intent parameters."""
    
    @staticmethod
    def validate_query_intent(query_intent: str) -> str:
        """Validate and normalize query intent with comprehensive checks."""
        if not isinstance(query_intent, str):
            raise ValidationError(f"query_intent must be a string, got {type(query_intent).__name__}")

        if not query_intent or not query_intent.strip():
            raise ValidationError("query_intent cannot be empty")

        normalized = query_intent.strip()

        # Length validation
        if len(normalized) < 3:
            raise ValidationError(f"query_intent too short: {len(normalized)} chars (min: 3)")

        if len(normalized) > 1000:
            raise ValidationError(f"query_intent too long: {len(normalized)} chars (max: 1000)")

        # Check for potentially malicious content
        if any(char in normalized for char in ['\x00', '\x01', '\x02']):
            raise ValidationError("query_intent contains invalid control characters")

        return normalized
    
    @staticmethod
    def validate_relevance_score(score: float) -> float:
        """Validate relevance score with comprehensive checks."""
        if not isinstance(score, (int, float)):
            raise ValidationError(f"relevance_score must be a number, got {type(score).__name__}")

        score_float = float(score)

        # Check for NaN or infinity
        if not (score_float == score_float):  # NaN check
            raise ValidationError("relevance_score cannot be NaN")

        if score_float == float('inf') or score_float == float('-inf'):
            raise ValidationError("relevance_score cannot be infinity")

        if not (0.0 <= score_float <= 1.0):
            raise ValidationError(f"relevance_score must be between 0.0 and 1.0, got {score_float}")

        return score_float
    
    @staticmethod
    def validate_file_change_list(file_list: Optional[List[str]]) -> List[str]:
        """Validate file change list with comprehensive checks."""
        if file_list is None:
            return []

        if not isinstance(file_list, list):
            raise ValidationError(f"file_change_list must be a list, got {type(file_list).__name__}")

        # Check list size limit
        if len(file_list) > 100:
            raise ValidationError(f"file_change_list too large: {len(file_list)} files (max: 100)")

        validated_files = []
        seen_files = set()

        for i, file_path in enumerate(file_list):
            if not isinstance(file_path, str):
                raise ValidationError(f"file_change_list[{i}] must be a string, got {type(file_path).__name__}")

            cleaned_path = file_path.strip()
            if not cleaned_path:
                raise ValidationError(f"file_change_list[{i}] cannot be empty")

            # Check path length
            if len(cleaned_path) > 500:
                raise ValidationError(f"file_change_list[{i}] too long: {len(cleaned_path)} chars (max: 500)")

            # Check for potentially dangerous paths
            if any(dangerous in cleaned_path for dangerous in ['../', '..\\', '/etc/', 'C:\\Windows\\']):
                raise ValidationError(f"file_change_list[{i}] contains potentially dangerous path: {cleaned_path}")

            # Normalize path separators and remove leading slashes
            normalized_path = cleaned_path.replace('\\', '/').lstrip('/')

            # Check for duplicates
            if normalized_path in seen_files:
                logger.warning(f"Duplicate file path in file_change_list: {normalized_path}")
                continue

            seen_files.add(normalized_path)
            validated_files.append(normalized_path)

        return validated_files
    
    @staticmethod
    def validate_query_type(query_type: str) -> str:
        """Validate query type with comprehensive checks."""
        if not isinstance(query_type, str):
            raise ValidationError(f"query_type must be a string, got {type(query_type).__name__}")

        cleaned = query_type.strip().lower()
        if not cleaned:
            raise ValidationError("query_type cannot be empty")

        valid_types = {"search", "modification", "analysis", "debugging"}
        if cleaned not in valid_types:
            raise ValidationError(f"query_type must be one of {valid_types}, got '{cleaned}'")

        return cleaned

    @staticmethod
    def validate_collection_name(collection_name: Optional[str]) -> Optional[str]:
        """Validate collection name with comprehensive checks."""
        if collection_name is None:
            return None

        if not isinstance(collection_name, str):
            raise ValidationError(f"collection_name must be a string, got {type(collection_name).__name__}")

        cleaned = collection_name.strip()
        if not cleaned:
            return None

        if len(cleaned) > 100:
            raise ValidationError(f"collection_name too long: {len(cleaned)} chars (max: 100)")

        # Check for valid collection name format (alphanumeric, underscore, hyphen)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', cleaned):
            raise ValidationError(
                f"collection_name contains invalid characters: {cleaned}. "
                "Only alphanumeric, underscore, and hyphen are allowed."
            )

        return cleaned


class QueryIntentTracker:
    """
    Tracks query intents and relevance feedback for meta-learning.

    This class manages the storage and retrieval of query intents as vectors
    in ChromaDB to enable similarity search and pattern analysis.
    """

    COLLECTION_NAME = "query_intents_global"

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        query_processor: QueryProcessor,
        embedding_provider: EmbeddingProvider
    ):
        """
        Initialize the query intent tracker.

        Args:
            vector_store: ChromaDB vector store instance
            query_processor: Query processor for generating embeddings
            embedding_provider: Embedding provider for model info
        """
        self.vector_store = vector_store
        self.query_processor = query_processor
        self.embedding_provider = embedding_provider

        # Cache for frequently accessed intent patterns
        self._recommendation_cache: Dict[str, List[SimilarIntent]] = {}
        self._cache_max_size = 100

        logger.info("Initialized QueryIntentTracker")

    @retry_on_storage_error(max_retries=3, delay=1.0, backoff=2.0)
    def store_query_intent(
        self,
        query_intent: str,
        relevance_score: float,
        file_change_list: Optional[List[str]] = None,
        collection_name: Optional[str] = None,
        query_type: str = "search"
    ) -> QueryIntentResult:
        """
        Store a query intent with relevance feedback.
        
        Args:
            query_intent: Semantic description of the search intent
            relevance_score: Agent-assessed relevance (0.0-1.0)
            file_change_list: Files modified as result of search
            collection_name: Which collection was searched
            query_type: Type of intent (search, modification, analysis, debugging)
            
        Returns:
            QueryIntentResult with storage details
            
        Raises:
            ValidationError: If input validation fails
            StorageError: If vector storage fails
        """
        try:
            # Validate inputs
            validated_intent = QueryIntentValidator.validate_query_intent(query_intent)
            validated_score = QueryIntentValidator.validate_relevance_score(relevance_score)
            validated_files = QueryIntentValidator.validate_file_change_list(file_change_list)
            validated_type = QueryIntentValidator.validate_query_type(query_type)
            
            # Generate unique intent ID
            timestamp = datetime.utcnow()
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            random_suffix = str(uuid.uuid4())[:8]
            intent_id = f"intent_{timestamp_str}_{random_suffix}"
            
            # Generate embedding for the intent
            logger.debug(f"Generating embedding for intent: {validated_intent[:50]}...")
            embedding_result = self.query_processor.process_query(validated_intent)
            
            # Prepare metadata
            metadata = {
                "intent_id": intent_id,
                "query_intent": validated_intent,
                "relevance_score": str(validated_score),
                "timestamp": timestamp.isoformat() + "Z",
                "query_type": validated_type,
                "file_change_list": json.dumps(validated_files),
                "file_change_count": str(len(validated_files))
            }
            
            if collection_name:
                metadata["collection_name"] = collection_name
            
            # Get or create the intent collection
            collection = self._get_or_create_intent_collection()

            # Store the intent vector directly using ChromaDB collection
            collection.add(
                ids=[intent_id],
                documents=[validated_intent],
                embeddings=[embedding_result.embedding],
                metadatas=[metadata]
            )
            
            logger.info(f"Stored query intent: '{validated_intent[:50]}...' (relevance: {validated_score})")
            
            return QueryIntentResult(
                intent_id=intent_id,
                query_intent=validated_intent,
                relevance_score=validated_score,
                timestamp=metadata["timestamp"],
                collection_name=collection_name,
                file_change_count=len(validated_files),
                query_type=validated_type
            )
            
        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Failed to store query intent: {e}", exc_info=True)
            raise StorageError(f"Failed to store intent vector: {str(e)}")

    @retry_on_storage_error(max_retries=2, delay=0.5, backoff=2.0)
    def find_similar_intents(
        self,
        query_intent: str,
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        collection_filter: Optional[str] = None,
        query_type_filter: Optional[str] = None
    ) -> List[SimilarIntent]:
        """
        Find historically similar query intents.

        Args:
            query_intent: Intent to find similar matches for
            similarity_threshold: Minimum similarity score (0.0-1.0)
            max_results: Maximum number of results to return
            collection_filter: Filter by specific collection name
            query_type_filter: Filter by specific query type

        Returns:
            List of SimilarIntent objects sorted by similarity

        Raises:
            ValidationError: If input validation fails
            StorageError: If search fails
        """
        try:
            # Validate inputs
            validated_intent = QueryIntentValidator.validate_query_intent(query_intent)

            if not (0.0 <= similarity_threshold <= 1.0):
                raise ValidationError(f"similarity_threshold must be between 0.0 and 1.0, got {similarity_threshold}")

            if max_results <= 0:
                raise ValidationError(f"max_results must be positive, got {max_results}")

            # Generate embedding for the query intent
            embedding_result = self.query_processor.process_query(validated_intent)

            # Build metadata filter
            metadata_filter = {}
            if collection_filter:
                metadata_filter["collection_name"] = collection_filter
            if query_type_filter:
                metadata_filter["query_type"] = query_type_filter

            # Search for similar intents
            search_results = self.vector_store.search(
                collection_name=self.COLLECTION_NAME,
                query_embedding=embedding_result.embedding,
                top_k=max_results * 2,  # Get more results for filtering
                filter_metadata=metadata_filter if metadata_filter else None
            )

            # Process and filter results
            similar_intents = []
            for result in search_results:
                similarity_score = result.get("similarity", 0.0)

                # Apply similarity threshold
                if similarity_score < similarity_threshold:
                    continue

                metadata = result.get("metadata", {})

                # Parse file changes
                file_changes_json = metadata.get("file_change_list", "[]")
                try:
                    file_changes = json.loads(file_changes_json)
                except json.JSONDecodeError:
                    file_changes = []

                # Parse relevance score
                try:
                    relevance_score = float(metadata.get("relevance_score", "0.0"))
                except ValueError:
                    relevance_score = 0.0

                similar_intent = SimilarIntent(
                    intent_id=metadata.get("intent_id", "unknown"),
                    query_intent=metadata.get("query_intent", ""),
                    relevance_score=relevance_score,
                    similarity_score=similarity_score,
                    file_changes=file_changes,
                    timestamp=metadata.get("timestamp", ""),
                    collection_name=metadata.get("collection_name"),
                    query_type=metadata.get("query_type", "search")
                )

                similar_intents.append(similar_intent)

            # Sort by similarity score (highest first) and limit results
            similar_intents.sort(key=lambda x: x.similarity_score, reverse=True)
            similar_intents = similar_intents[:max_results]

            logger.debug(f"Found {len(similar_intents)} similar intents for: {validated_intent[:50]}...")
            return similar_intents

        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Failed to find similar intents: {e}", exc_info=True)
            raise StorageError(f"Failed to search intent vectors: {str(e)}")

    def get_intent_recommendations(
        self,
        query_intent: str,
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        collection_filter: Optional[str] = None,
        query_type_filter: Optional[str] = None,
        relevance_weight: float = 0.3
    ) -> List[SimilarIntent]:
        """
        Get intelligent intent recommendations with enhanced ranking.

        This method combines vector similarity with historical relevance scores
        to provide better recommendations for similar query intents.

        Args:
            query_intent: Intent to find recommendations for
            similarity_threshold: Minimum similarity score (0.0-1.0)
            max_results: Maximum number of recommendations
            collection_filter: Filter by specific collection name
            query_type_filter: Filter by specific query type
            relevance_weight: Weight for relevance score in ranking (0.0-1.0)

        Returns:
            List of SimilarIntent objects ranked by combined score

        Raises:
            ValidationError: If input validation fails
            StorageError: If search fails
        """
        try:
            # Validate inputs
            validated_intent = QueryIntentValidator.validate_query_intent(query_intent)

            if not (0.0 <= similarity_threshold <= 1.0):
                raise ValidationError(f"similarity_threshold must be between 0.0 and 1.0, got {similarity_threshold}")

            if not (0.0 <= relevance_weight <= 1.0):
                raise ValidationError(f"relevance_weight must be between 0.0 and 1.0, got {relevance_weight}")

            if max_results <= 0:
                raise ValidationError(f"max_results must be positive, got {max_results}")

            # Check cache first
            cache_key = self._get_cache_key(validated_intent, similarity_threshold, collection_filter, query_type_filter)
            if cache_key in self._recommendation_cache:
                logger.debug(f"Cache hit for intent recommendations: {validated_intent[:30]}...")
                cached_results = self._recommendation_cache[cache_key]
                return cached_results[:max_results]

            # Get similar intents using existing method
            similar_intents = self.find_similar_intents(
                query_intent=validated_intent,
                similarity_threshold=similarity_threshold,
                max_results=max_results * 2,  # Get more for better ranking
                collection_filter=collection_filter,
                query_type_filter=query_type_filter
            )

            # Apply enhanced ranking algorithm
            ranked_intents = self._rank_intents_by_combined_score(
                similar_intents,
                relevance_weight=relevance_weight
            )

            # Limit results
            final_results = ranked_intents[:max_results]

            # Cache results (manage cache size)
            self._cache_recommendations(cache_key, final_results)

            logger.debug(f"Generated {len(final_results)} intent recommendations for: {validated_intent[:50]}...")
            return final_results

        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Failed to get intent recommendations: {e}", exc_info=True)
            raise StorageError(f"Failed to generate recommendations: {str(e)}")

    def _rank_intents_by_combined_score(
        self,
        intents: List[SimilarIntent],
        relevance_weight: float = 0.3
    ) -> List[SimilarIntent]:
        """
        Rank intents by combined similarity and relevance scores.

        Args:
            intents: List of similar intents to rank
            relevance_weight: Weight for relevance score (0.0-1.0)

        Returns:
            List of intents sorted by combined score (highest first)
        """
        similarity_weight = 1.0 - relevance_weight

        for intent in intents:
            # Calculate combined score: weighted average of similarity and relevance
            combined_score = (
                similarity_weight * intent.similarity_score +
                relevance_weight * intent.relevance_score
            )

            # Store combined score in a custom attribute for sorting
            intent._combined_score = combined_score

        # Sort by combined score (highest first)
        ranked_intents = sorted(intents, key=lambda x: x._combined_score, reverse=True)

        return ranked_intents

    def _get_cache_key(
        self,
        query_intent: str,
        similarity_threshold: float,
        collection_filter: Optional[str] = None,
        query_type_filter: Optional[str] = None
    ) -> str:
        """Generate cache key for recommendations."""
        import hashlib

        key_parts = [
            query_intent,
            str(similarity_threshold),
            collection_filter or "",
            query_type_filter or ""
        ]

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    def _cache_recommendations(self, cache_key: str, results: List[SimilarIntent]) -> None:
        """Cache recommendations with size management."""
        # Remove oldest entries if cache is full
        if len(self._recommendation_cache) >= self._cache_max_size:
            # Remove the first (oldest) entry
            oldest_key = next(iter(self._recommendation_cache))
            del self._recommendation_cache[oldest_key]

        # Add new entry
        self._recommendation_cache[cache_key] = results.copy()

    def clear_recommendation_cache(self) -> None:
        """Clear the recommendation cache."""
        self._recommendation_cache.clear()
        logger.debug("Cleared intent recommendation cache")

    def _get_or_create_intent_collection(self):
        """Get or create the global intent collection."""
        try:
            return self.vector_store.get_or_create_collection(
                collection_name=self.COLLECTION_NAME,
                embedding_dimension=self.embedding_provider.get_dimensions(),
                model_name=self.embedding_provider.get_model_name(),
                processor_type="query_intent_tracker"
            )
        except Exception as e:
            raise StorageError(f"Failed to create intent collection: {str(e)}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the intent collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            stats = self.vector_store.get_stats(self.COLLECTION_NAME)
            return {
                "collection_name": self.COLLECTION_NAME,
                "intent_count": stats.get("count", 0),
                "metadata": stats.get("metadata", {}),
                "status": "active" if stats.get("count", 0) > 0 else "empty"
            }
        except Exception as e:
            logger.warning(f"Failed to get intent collection stats: {e}")
            return {
                "collection_name": self.COLLECTION_NAME,
                "intent_count": 0,
                "status": "error",
                "error": str(e)
            }
