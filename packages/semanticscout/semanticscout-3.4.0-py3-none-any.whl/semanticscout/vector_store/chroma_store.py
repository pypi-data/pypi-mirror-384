"""
Chroma vector store integration for storing and retrieving code embeddings.
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """
    Vector store using ChromaDB for persistent storage of code embeddings.
    """

    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the Chroma vector store.

        Args:
            persist_directory: Directory to persist the database
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize Chroma client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
        )

        logger.info(f"Initialized Chroma vector store at: {self.persist_directory}")

    def get_or_create_collection(
        self,
        collection_name: str,
        embedding_dimension: Optional[int] = None,
        model_name: Optional[str] = None,
        processor_type: Optional[str] = None,
        codebase_path: Optional[str] = None,
    ):
        """
        Get or create a collection for a codebase.

        Args:
            collection_name: Name of the collection
            embedding_dimension: Dimension of embeddings (optional)
            model_name: Name of the embedding model (optional)
            processor_type: Type of AST processor used (e.g., "tree-sitter", "lsp-jedi", "lsp-omnisharp")
            codebase_path: Absolute path to the codebase directory (optional, for duplicate detection)

        Returns:
            Chroma collection object

        Raises:
            ValueError: If dimension mismatch detected with existing collection
        """
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=collection_name)
            logger.info(f"Retrieved existing collection: {collection_name}")

            # Validate dimensions if provided
            if embedding_dimension is not None:
                self._validate_dimensions(collection, embedding_dimension, model_name)

            # Update processor_type if provided and different
            if processor_type is not None:
                current_metadata = collection.metadata or {}
                if current_metadata.get("processor_type") != processor_type:
                    try:
                        current_metadata["processor_type"] = processor_type
                        collection.modify(metadata=current_metadata)
                        logger.info(f"Updated processor_type to: {processor_type}")
                    except Exception as e:
                        logger.warning(f"Could not update processor_type metadata: {e}")

            # Update codebase_path if provided and different
            if codebase_path is not None:
                current_metadata = collection.metadata or {}
                resolved_path = str(Path(codebase_path).resolve())
                if current_metadata.get("codebase_path") != resolved_path:
                    try:
                        current_metadata["codebase_path"] = resolved_path
                        collection.modify(metadata=current_metadata)
                        logger.info(f"Updated codebase_path to: {resolved_path}")
                    except Exception as e:
                        logger.warning(f"Could not update codebase_path metadata: {e}")

            return collection
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception:
            # Create new collection with metadata
            metadata = {"hnsw:space": "cosine"}  # Use cosine similarity

            # Add embedding model metadata if provided
            if model_name is not None:
                metadata["embedding_model"] = model_name
            if embedding_dimension is not None:
                metadata["embedding_dimensions"] = str(embedding_dimension)
            if processor_type is not None:
                metadata["processor_type"] = processor_type
            if codebase_path is not None:
                # Store absolute resolved path for consistency
                metadata["codebase_path"] = str(Path(codebase_path).resolve())
            metadata["created_at"] = datetime.utcnow().isoformat()

            collection = self.client.create_collection(
                name=collection_name,
                metadata=metadata,
            )
            logger.info(
                f"Created new collection: {collection_name} "
                f"(model: {model_name}, dimensions: {embedding_dimension}, processor: {processor_type}, path: {codebase_path})"
            )
            return collection

    def _validate_dimensions(
        self,
        collection,
        embedding_dimension: int,
        model_name: Optional[str] = None,
    ) -> None:
        """
        Validate that embedding dimensions match the collection's stored metadata.

        Args:
            collection: ChromaDB collection object
            embedding_dimension: Dimension of embeddings to validate
            model_name: Name of the embedding model (optional)

        Raises:
            ValueError: If dimension mismatch detected
        """
        metadata = collection.metadata or {}
        stored_dimensions = metadata.get("embedding_dimensions")
        stored_model = metadata.get("embedding_model")

        # Backward compatibility: if no metadata stored, add it now
        if stored_dimensions is None:
            logger.warning(
                f"Collection '{collection.name}' has no dimension metadata. "
                f"Adding current model info: {model_name} ({embedding_dimension} dims)"
            )
            # Update collection metadata
            try:
                metadata["embedding_dimensions"] = str(embedding_dimension)
                if model_name:
                    metadata["embedding_model"] = model_name
                if "created_at" not in metadata:
                    metadata["created_at"] = datetime.utcnow().isoformat()
                collection.modify(metadata=metadata)
            except Exception as e:
                logger.warning(f"Could not update collection metadata: {e}")
            return

        # Validate dimensions
        stored_dim_int = int(stored_dimensions)
        if stored_dim_int != embedding_dimension:
            error_msg = (
                f"Dimension mismatch for collection '{collection.name}'!\n"
                f"  Stored: {stored_dim_int} dimensions (model: {stored_model or 'unknown'})\n"
                f"  Current: {embedding_dimension} dimensions (model: {model_name or 'unknown'})\n"
                f"  → Cannot mix embeddings with different dimensions in the same collection.\n"
                f"  → Either use the same embedding model or create a new collection."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Warn if model changed but dimensions match
        if stored_model and model_name and stored_model != model_name:
            logger.warning(
                f"Model changed for collection '{collection.name}': "
                f"{stored_model} → {model_name} (dimensions match: {embedding_dimension}). "
                f"Embeddings from different models may not be directly comparable."
            )

    def generate_collection_name(self, codebase_path: str) -> str:
        """
        Generate a unique collection name from a codebase path using project name + UUID.

        Args:
            codebase_path: Path to the codebase

        Returns:
            Collection name (sanitized project name + UUID for uniqueness)
        """
        import uuid

        # Get the directory name (project name)
        path = Path(codebase_path).resolve()
        project_name = path.name

        # Sanitize the name to be ChromaDB-compatible
        # Must start with letter, contain only alphanumeric, underscores, and hyphens
        # Convert to lowercase and replace invalid characters
        sanitized = project_name.lower()
        sanitized = sanitized.replace(' ', '_')
        sanitized = sanitized.replace('.', '_')
        sanitized = ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in sanitized)

        # Add UUID for uniqueness (shortened to 8 chars for readability)
        unique_id = str(uuid.uuid4())[:8]
        sanitized = f"{sanitized}_{unique_id}"

        # Ensure it starts with a letter
        if not sanitized[0].isalpha():
            sanitized = f"codebase_{sanitized}"

        # Limit length to 63 characters (ChromaDB limit)
        if len(sanitized) > 63:
            sanitized = sanitized[:63]

        return sanitized

    def find_collections_by_path_and_model(
        self,
        codebase_path: str,
        embedding_model: str,
        processor_type: str = None
    ) -> List[str]:
        """
        Find collections for a specific codebase path, embedding model, and optionally processor type.

        Args:
            codebase_path: Absolute path to codebase
            embedding_model: Name of embedding model
            processor_type: Optional processor type (tree-sitter, lsp-jedi, etc.)
                          If None, only checks path and model

        Returns:
            List of collection names that match
        """
        # Normalize path for comparison
        normalized_path = str(Path(codebase_path).resolve())

        matching_collections = []

        for collection_name in self.list_collections():
            try:
                collection = self.client.get_collection(name=collection_name)
                metadata = collection.metadata or {}

                stored_path = metadata.get("codebase_path")
                stored_model = metadata.get("embedding_model")
                stored_processor = metadata.get("processor_type")

                if stored_path and stored_model:
                    # Normalize stored path for comparison
                    stored_path_normalized = str(Path(stored_path).resolve())

                    # Check path and model match
                    path_model_match = (
                        stored_path_normalized == normalized_path and
                        stored_model == embedding_model
                    )

                    # If processor_type specified, also check it matches
                    if processor_type is not None:
                        if path_model_match and stored_processor == processor_type:
                            matching_collections.append(collection_name)
                    else:
                        # No processor type specified, just check path and model
                        if path_model_match:
                            matching_collections.append(collection_name)
            except Exception as e:
                logger.warning(f"Error checking collection {collection_name}: {e}")
                continue

        return matching_collections

    def add_chunks(
        self,
        collection_name: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        model_name: Optional[str] = None,
    ) -> None:
        """
        Add code chunks with their embeddings to the vector store.

        Args:
            collection_name: Name of the collection
            chunks: List of chunk dictionaries with metadata
            embeddings: List of embedding vectors
            model_name: Name of the embedding model (optional)

        Raises:
            ValueError: If chunks and embeddings lengths don't match or dimension mismatch
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) must have same length"
            )

        if not chunks:
            logger.warning("No chunks to add")
            return

        collection = self.get_or_create_collection(
            collection_name,
            embedding_dimension=len(embeddings[0]),
            model_name=model_name,
        )

        # Prepare data for Chroma
        ids = []
        documents = []
        metadatas = []
        embedding_list = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Handle both CodeChunk objects and dictionaries
            if hasattr(chunk, 'metadata'):
                # CodeChunk object
                chunk_metadata = chunk.metadata
                chunk_content = chunk.content
                chunk_file_path = chunk.file_path
                chunk_start_line = chunk.start_line
            else:
                # Dictionary
                chunk_metadata = chunk.get("metadata", {})
                chunk_content = chunk.get("content", "")
                chunk_file_path = chunk.get("file_path", "unknown")
                chunk_start_line = chunk.get("start_line", 0)

            # Generate unique ID (use chunk_id from metadata if available)
            if "chunk_id" in chunk_metadata:
                chunk_id = chunk_metadata["chunk_id"]
            else:
                chunk_id = f"{chunk_file_path}_{chunk_start_line}_{i}"
                chunk_id = hashlib.sha256(chunk_id.encode()).hexdigest()

            ids.append(chunk_id)
            documents.append(chunk_content)

            # Prepare metadata with enhanced fields
            if hasattr(chunk, 'metadata'):
                # CodeChunk object
                metadata = {
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,  # Store as int, not string
                    "end_line": chunk.end_line,      # Store as int, not string
                    "chunk_type": chunk.chunk_type,
                    "language": chunk.language,
                    "chunk_id": chunk_id,  # NEW: Store chunk ID
                }
            else:
                # Dictionary
                metadata = {
                    "file_path": chunk.get("file_path", ""),
                    "start_line": chunk.get("start_line", 0),  # Store as int, not string
                    "end_line": chunk.get("end_line", 0),      # Store as int, not string
                    "chunk_type": chunk.get("chunk_type", ""),
                    "language": chunk.get("language", ""),
                    "chunk_id": chunk_id,  # NEW: Store chunk ID
                }

            # Add enhanced metadata fields (serialize lists/dicts to JSON)
            if chunk_metadata:
                # Serialize complex fields to JSON strings
                for key, value in chunk_metadata.items():
                    if key in ["imports", "exports", "file_imports", "file_exports",
                               "references", "referenced_by", "child_chunk_ids"]:
                        try:
                            metadata[key] = json.dumps(value) if value else "[]"
                        except Exception as e:
                            logger.warning(f"Failed to serialize {key}: {e}")
                            metadata[key] = "[]"
                    elif key in ["parent_chunk_id", "chunk_name", "nesting_level",
                                 "has_decorators", "has_error_handling", "has_type_hints",
                                 "has_docstring", "content_hash", "indexed_at",
                                 "file_type", "test_penalty", "file_category"]:  # NEW: Add test filtering metadata
                        metadata[key] = value

            metadatas.append(metadata)
            embedding_list.append(embedding)

        # BUG FIX 251: Validate file_type metadata exists
        missing_file_type = sum(1 for m in metadatas if "file_type" not in m)
        if missing_file_type > 0:
            logger.warning(f"{missing_file_type}/{len(metadatas)} chunks missing file_type metadata")

        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embedding_list,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"Added {len(chunks)} chunks to collection: {collection_name}")

    def delete_by_file_path(
        self, collection_name: str, file_path: str
    ) -> int:
        """
        Delete all chunks for a specific file.

        Args:
            collection_name: Name of the collection
            file_path: Relative file path to delete chunks for

        Returns:
            Number of chunks deleted
        """
        try:
            collection = self.client.get_collection(name=collection_name)

            # Query for all chunks with this file_path
            results = collection.get(
                where={"file_path": file_path},
                include=["metadatas"]
            )

            if not results or not results.get("ids"):
                # Try to get all chunks to debug
                all_results = collection.get(include=["metadatas"], limit=10)
                if all_results and all_results.get("metadatas"):
                    sample_paths = [m.get("file_path") for m in all_results["metadatas"][:3]]
                    logger.debug(f"Sample file_paths in collection: {sample_paths}")
                logger.info(f"No chunks found for file: {file_path}")
                return 0

            # Delete the chunks
            chunk_ids = results["ids"]
            collection.delete(ids=chunk_ids)

            logger.info(f"Deleted {len(chunk_ids)} chunks for file: {file_path}")
            return len(chunk_ids)

        except Exception as e:
            logger.error(f"Error deleting chunks for {file_path}: {e}")
            raise

    def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar code chunks using a query embedding.

        Args:
            collection_name: Name of the collection to search
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of search results with content, metadata, and similarity scores
        """
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Collection {collection_name} not found: {e}")
            return []

        # BUG FIX 251: Log filter being applied
        if filter_metadata:
            logger.info(f"Applying ChromaDB where clause: {filter_metadata}")
        else:
            logger.info("No metadata filter applied")

        # Perform search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
        )

        # BUG FIX 251: Log sample result metadata
        if results["metadatas"] and len(results["metadatas"][0]) > 0:
            sample_meta = results["metadatas"][0][0]
            logger.info(f"Sample result metadata keys: {list(sample_meta.keys())}")
            logger.info(f"Sample result file_type: {sample_meta.get('file_type', 'MISSING')}")

        # Format results
        formatted_results = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i]

                # Deserialize JSON fields back to lists/dicts
                deserialized_metadata = {}
                for key, value in metadata.items():
                    if key in ["imports", "exports", "file_imports", "file_exports",
                               "references", "referenced_by", "child_chunk_ids"]:
                        try:
                            deserialized_metadata[key] = json.loads(value) if value else []
                        except Exception as e:
                            logger.warning(f"Failed to deserialize {key}: {e}")
                            deserialized_metadata[key] = []
                    else:
                        deserialized_metadata[key] = value

                result = {
                    "content": results["documents"][0][i],
                    "metadata": deserialized_metadata,
                    "distance": results["distances"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "chunk_id": results["ids"][0][i],  # Include chunk ID
                }
                formatted_results.append(result)

        logger.info(
            f"Found {len(formatted_results)} results for query in collection: {collection_name}"
        )

        return formatted_results

    def get_chunk_by_id(
        self, collection_name: str, chunk_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific chunk by its ID.

        Args:
            collection_name: Name of the collection
            chunk_id: Unique chunk ID

        Returns:
            Chunk dictionary or None if not found
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            result = collection.get(ids=[chunk_id], include=["documents", "metadatas"])

            if result["ids"] and len(result["ids"]) > 0:
                metadata = result["metadatas"][0]

                # Deserialize JSON fields
                deserialized_metadata = {}
                for key, value in metadata.items():
                    if key in ["imports", "exports", "file_imports", "file_exports",
                               "references", "referenced_by", "child_chunk_ids"]:
                        try:
                            deserialized_metadata[key] = json.loads(value) if value else []
                        except Exception:
                            deserialized_metadata[key] = []
                    else:
                        deserialized_metadata[key] = value

                return {
                    "chunk_id": result["ids"][0],
                    "content": result["documents"][0],
                    "metadata": deserialized_metadata,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {e}")
            return None

    def get_chunks_by_file(
        self, collection_name: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks from a specific file.

        Args:
            collection_name: Name of the collection
            file_path: Path to the file

        Returns:
            List of chunk dictionaries
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            results = collection.get(
                where={"file_path": file_path},
                include=["documents", "metadatas"]
            )

            chunks = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"])):
                    metadata = results["metadatas"][i]

                    # Deserialize JSON fields
                    deserialized_metadata = {}
                    for key, value in metadata.items():
                        if key in ["imports", "exports", "file_imports", "file_exports",
                                   "references", "referenced_by", "child_chunk_ids"]:
                            try:
                                deserialized_metadata[key] = json.loads(value) if value else []
                            except Exception:
                                deserialized_metadata[key] = []
                        else:
                            deserialized_metadata[key] = value

                    chunks.append({
                        "chunk_id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": deserialized_metadata,
                    })

            return chunks
        except Exception as e:
            logger.error(f"Failed to get chunks for file {file_path}: {e}")
            return []

    def get_chunks_by_line_range(
        self, collection_name: str, file_path: str, start_line: int, end_line: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks within a specific line range in a file.

        Args:
            collection_name: Name of the collection
            file_path: Path to the file
            start_line: Start line number
            end_line: End line number

        Returns:
            List of chunk dictionaries
        """
        # Get all chunks from the file
        all_chunks = self.get_chunks_by_file(collection_name, file_path)

        # Filter by line range
        filtered_chunks = []
        for chunk in all_chunks:
            chunk_start = chunk["metadata"].get("start_line", 0)
            chunk_end = chunk["metadata"].get("end_line", 0)

            # Check if chunk overlaps with requested range
            if (chunk_start <= end_line and chunk_end >= start_line):
                filtered_chunks.append(chunk)

        # Sort by start_line
        filtered_chunks.sort(key=lambda x: x["metadata"].get("start_line", 0))

        return filtered_chunks

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.

        Args:
            collection_name: Name of the collection to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False

    def get_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics about a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()

            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata,
            }
        except Exception as e:
            logger.error(f"Failed to get stats for collection {collection_name}: {e}")
            return {
                "name": collection_name,
                "count": 0,
                "error": str(e),
            }

    def list_collections(self) -> List[str]:
        """
        List all collections in the vector store.

        Returns:
            List of collection names
        """
        collections = self.client.list_collections()
        return [c.name for c in collections]

    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists.

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists, False otherwise
        """
        try:
            self.client.get_collection(name=collection_name)
            return True
        except Exception:
            return False

    def upsert_chunks(
        self,
        collection_name: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        model_name: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Upsert code chunks (update if exists, insert if not).

        More efficient than delete + add for updates.

        Args:
            collection_name: Name of the collection
            chunks: List of chunk dictionaries with metadata
            embeddings: List of embedding vectors
            model_name: Name of the embedding model (optional)

        Returns:
            Dictionary with counts of inserted and updated chunks
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) must have same length"
            )

        if not chunks:
            return {"inserted": 0, "updated": 0}

        collection = self.get_or_create_collection(
            collection_name,
            embedding_dimension=len(embeddings[0]),
            model_name=model_name,
        )

        # Prepare data
        ids = []
        documents = []
        metadatas = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Extract chunk data
            if hasattr(chunk, 'metadata'):
                chunk_metadata = chunk.metadata
                chunk_content = chunk.content
                chunk_file_path = chunk.file_path
                chunk_start_line = chunk.start_line
            else:
                chunk_metadata = chunk.get("metadata", {})
                chunk_content = chunk.get("content", "")
                chunk_file_path = chunk.get("file_path", "unknown")
                chunk_start_line = chunk.get("start_line", 0)

            # Generate chunk ID
            if "chunk_id" in chunk_metadata:
                chunk_id = chunk_metadata["chunk_id"]
            else:
                chunk_id = f"{chunk_file_path}_{chunk_start_line}_{i}"
                chunk_id = hashlib.sha256(chunk_id.encode()).hexdigest()

            ids.append(chunk_id)
            documents.append(chunk_content)

            # Prepare metadata
            metadata = self._prepare_metadata(chunk, chunk_id)
            metadatas.append(metadata)

        # Upsert to ChromaDB (automatically handles insert/update)
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(f"Upserted {len(chunks)} chunks to collection {collection_name}")

        # Note: ChromaDB doesn't distinguish between insert/update in response
        # We return total count as "inserted" for simplicity
        return {"inserted": len(chunks), "updated": 0}

    def delete_batch(
        self,
        collection_name: str,
        chunk_ids: List[str],
    ) -> int:
        """
        Delete multiple chunks in a single batch operation.

        More efficient than individual deletes.

        Args:
            collection_name: Name of the collection
            chunk_ids: List of chunk IDs to delete

        Returns:
            Number of chunks deleted
        """
        if not chunk_ids:
            return 0

        try:
            collection = self.client.get_collection(name=collection_name)
            collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} chunks from {collection_name}")
            return len(chunk_ids)
        except Exception as e:
            logger.error(f"Failed to delete batch: {e}")
            return 0

    def compact_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        Compact/optimize a collection to reduce storage and improve performance.

        Note: ChromaDB handles compaction automatically, but this method
        can be used to trigger manual optimization if needed.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with compaction statistics
        """
        try:
            collection = self.client.get_collection(name=collection_name)

            # Get collection stats before
            count_before = collection.count()

            # ChromaDB doesn't expose manual compaction API
            # But we can get stats for monitoring

            return {
                "collection_name": collection_name,
                "chunk_count": count_before,
                "status": "ChromaDB handles compaction automatically",
            }
        except Exception as e:
            logger.error(f"Failed to compact collection: {e}")
            return {
                "collection_name": collection_name,
                "error": str(e),
            }

    def _prepare_metadata(self, chunk: Any, chunk_id: str) -> Dict[str, Any]:
        """Prepare metadata dictionary from chunk."""
        if hasattr(chunk, 'metadata'):
            # CodeChunk object
            metadata = {
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_type": chunk.chunk_type,
                "language": chunk.language,
                "chunk_id": chunk_id,
            }
            # Add any additional metadata
            for key, value in chunk.metadata.items():
                if key not in metadata:
                    metadata[key] = value
        else:
            # Dictionary
            metadata = {
                "file_path": chunk.get("file_path", "unknown"),
                "start_line": chunk.get("start_line", 0),
                "end_line": chunk.get("end_line", 0),
                "chunk_type": chunk.get("chunk_type", "unknown"),
                "language": chunk.get("language", "unknown"),
                "chunk_id": chunk_id,
            }
            # Add metadata from chunk
            chunk_metadata = chunk.get("metadata", {})
            for key, value in chunk_metadata.items():
                if key not in metadata:
                    metadata[key] = value

        # Serialize complex types
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                metadata[key] = json.dumps(value)

        return metadata


