"""
Base classes for embedding providers.
"""

from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""

    embedding: List[float]
    text: str
    model: str
    dimensions: int


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def generate_embedding(self, text: str) -> EmbeddingResult:
        """
        Generate an embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult containing the embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        pass

    @abstractmethod
    def generate_embeddings_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts in a batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of EmbeddingResult objects

        Raises:
            Exception: If embedding generation fails
        """
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """
        Get the dimensionality of embeddings produced by this provider.

        Returns:
            Number of dimensions in embedding vectors
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the embedding model.

        Returns:
            Model name string
        """
        pass


