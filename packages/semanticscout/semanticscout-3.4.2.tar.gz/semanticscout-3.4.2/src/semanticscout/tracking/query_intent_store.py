"""
Dedicated ChromaDB store for query intents.

This module provides a specialized ChromaDB manager for query intents that operates
independently of the main vector store used for code collections.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import chromadb
from chromadb.api.models.Collection import Collection

from ..paths import get_path_manager
from .exceptions import StorageError

logger = logging.getLogger(__name__)


class QueryIntentStore:
    """
    Dedicated ChromaDB store for query intents.
    
    This class manages a separate ChromaDB instance specifically for storing
    query intents and user behavior data, independent of code collections.
    """
    
    COLLECTION_NAME = "query_intents"
    
    def __init__(self, persist_directory: Optional[str] = None,
                 embedding_model: Optional[str] = None,
                 embedding_dimensions: Optional[int] = None):
        """
        Initialize the query intent store.

        Args:
            persist_directory: Directory to persist the database. If None, uses
                             ~/semanticscout/data/query_intents_db
            embedding_model: Name of the embedding model to use. If None, defaults
                           to "all-MiniLM-L6-v2".
            embedding_dimensions: Dimension size of embeddings. If None, defaults
                                to 384.
        """
        if persist_directory is None:
            self.persist_directory = get_path_manager().get_query_intents_dir()
        else:
            self.persist_directory = Path(persist_directory)

        # Store embedding configuration
        self.embedding_model = embedding_model or "all-MiniLM-L6-v2"
        self.embedding_dimensions = embedding_dimensions or 384

        # Ensure directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize dedicated Chroma client for query intents
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
        )

        logger.info(f"Initialized QueryIntentStore at: {self.persist_directory} "
                   f"with model: {self.embedding_model} ({self.embedding_dimensions}D)")

    def close(self):
        """Close the ChromaDB client and clean up resources."""
        try:
            if hasattr(self, 'client') and self.client:
                # ChromaDB doesn't have an explicit close method, but we can reset the client
                self.client = None
                logger.debug("QueryIntentStore client closed")
        except Exception as e:
            logger.warning(f"Error closing QueryIntentStore client: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def get_or_create_collection(
        self,
        embedding_dimension: Optional[int] = None,
        model_name: Optional[str] = None
    ) -> Collection:
        """
        Get or create the query intents collection.

        Args:
            embedding_dimension: Dimension of embeddings. If None, uses instance default.
            model_name: Name of the embedding model. If None, uses instance default.
            
        Returns:
            ChromaDB collection for query intents
            
        Raises:
            StorageError: If collection cannot be created or accessed
        """
        # Use instance defaults if not provided
        if embedding_dimension is None:
            embedding_dimension = self.embedding_dimensions
        if model_name is None:
            model_name = self.embedding_model

        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.COLLECTION_NAME)
            logger.debug(f"Retrieved existing query intents collection")
            return collection

        except Exception:
            # Collection doesn't exist, create it
            try:
                metadata = {
                    "hnsw:space": "cosine",  # Use cosine similarity
                    "embedding_model": model_name,
                    "embedding_dimensions": str(embedding_dimension),
                    "processor_type": "query_intent_tracker",
                    "created_at": datetime.utcnow().isoformat(),
                    "schema_version": "1.0"
                }

                collection = self.client.create_collection(
                    name=self.COLLECTION_NAME,
                    metadata=metadata,
                )

                logger.info(f"Created new query intents collection with model: {model_name}")
                return collection

            except Exception as e:
                raise StorageError(f"Failed to create query intents collection: {str(e)}")
    
    def store_intent(
        self,
        intent_id: str,
        query_intent: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Store a query intent with its embedding and metadata.
        
        Args:
            intent_id: Unique identifier for the intent
            query_intent: The intent text (used as document)
            embedding: Vector embedding of the intent
            metadata: Additional metadata for the intent
            
        Raises:
            StorageError: If storage operation fails
        """
        try:
            # Get the collection (will be created if needed)
            collection = self.get_or_create_collection(
                embedding_dimension=len(embedding),
                model_name=metadata.get("embedding_model", "unknown")
            )
            
            # Store the intent
            collection.add(
                ids=[intent_id],
                documents=[query_intent],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            
            logger.debug(f"Stored query intent: {intent_id}")
            
        except Exception as e:
            raise StorageError(f"Failed to store query intent {intent_id}: {str(e)}")
    
    def find_similar_intents(
        self,
        query_embedding: List[float],
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar query intents using vector similarity search.
        
        Args:
            query_embedding: Vector embedding to search for
            similarity_threshold: Minimum similarity score (0.0-1.0)
            max_results: Maximum number of results to return
            where_filter: Optional metadata filter
            
        Returns:
            List of similar intents with metadata and similarity scores
            
        Raises:
            StorageError: If search operation fails
        """
        try:
            # Get the collection
            collection = self.get_or_create_collection(
                embedding_dimension=len(query_embedding),
                model_name="unknown"  # Will use existing collection if available
            )
            
            # Perform similarity search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results and filter by similarity threshold
            similar_intents = []
            if results["ids"] and results["ids"][0]:
                for i, intent_id in enumerate(results["ids"][0]):
                    # Convert distance to similarity (ChromaDB returns distances)
                    distance = results["distances"][0][i]
                    similarity = 1.0 - distance  # Cosine distance to similarity
                    
                    if similarity >= similarity_threshold:
                        similar_intents.append({
                            "intent_id": intent_id,
                            "query_intent": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "similarity_score": similarity
                        })
            
            logger.debug(f"Found {len(similar_intents)} similar intents above threshold {similarity_threshold}")
            return similar_intents
            
        except Exception as e:
            raise StorageError(f"Failed to search for similar intents: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the query intents collection.
        
        Returns:
            Dictionary with collection statistics
            
        Raises:
            StorageError: If stats retrieval fails
        """
        try:
            collection = self.client.get_collection(name=self.COLLECTION_NAME)
            count = collection.count()

            # Get collection metadata
            metadata = collection.metadata or {}

            return {
                "collection_name": self.COLLECTION_NAME,
                "intent_count": count,
                "embedding_model": metadata.get("embedding_model", "unknown"),
                "embedding_dimensions": metadata.get("embedding_dimensions", "unknown"),
                "created_at": metadata.get("created_at", "unknown"),
                "schema_version": metadata.get("schema_version", "unknown"),
                "store_location": str(self.persist_directory)
            }

        except Exception:
            # Collection doesn't exist yet (normal for new installations)
            return {
                "collection_name": self.COLLECTION_NAME,
                "intent_count": 0,
                "embedding_model": "none",
                "embedding_dimensions": "none",
                "created_at": "not_created",
                "schema_version": "1.0",
                "store_location": str(self.persist_directory)
            }
    
    def migrate_from_global_collection(
        self,
        source_vector_store,
        source_collection_name: str = "query_intents_global"
    ) -> Dict[str, int]:
        """
        Migrate query intents from the global collection in main vector store.
        
        Args:
            source_vector_store: The main ChromaVectorStore instance
            source_collection_name: Name of the source collection
            
        Returns:
            Dictionary with migration statistics
            
        Raises:
            StorageError: If migration fails
        """
        try:
            logger.info(f"Starting migration from {source_collection_name}")
            
            # Try to get the source collection
            try:
                source_collection = source_vector_store.client.get_collection(source_collection_name)
            except ValueError:
                logger.info(f"Source collection {source_collection_name} not found, no migration needed")
                return {"migrated": 0, "skipped": 0, "errors": 0}
            
            # Get all intents from source collection
            all_results = source_collection.get(
                include=["documents", "metadatas", "embeddings"]
            )
            
            if not all_results["ids"]:
                logger.info("Source collection is empty, no migration needed")
                return {"migrated": 0, "skipped": 0, "errors": 0}
            
            migrated_count = 0
            error_count = 0
            
            # Migrate each intent
            for i, intent_id in enumerate(all_results["ids"]):
                try:
                    document = all_results["documents"][i]
                    metadata = all_results["metadatas"][i]
                    embedding = all_results["embeddings"][i]
                    
                    # Store in new collection
                    self.store_intent(
                        intent_id=intent_id,
                        query_intent=document,
                        embedding=embedding,
                        metadata=metadata
                    )
                    
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to migrate intent {intent_id}: {e}")
                    error_count += 1
            
            logger.info(f"Migration completed: {migrated_count} migrated, {error_count} errors")
            
            return {
                "migrated": migrated_count,
                "skipped": 0,
                "errors": error_count
            }
            
        except Exception as e:
            raise StorageError(f"Migration failed: {str(e)}")
