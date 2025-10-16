"""Embedding generation providers for converting code to vectors."""

from .base import EmbeddingProvider, EmbeddingResult
from .ollama_provider import OllamaEmbeddingProvider

try:
    from .sentence_transformer_provider import SentenceTransformerProvider
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformerProvider = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

__all__ = [
    "EmbeddingProvider",
    "EmbeddingResult",
    "OllamaEmbeddingProvider",
    "SentenceTransformerProvider",
    "SENTENCE_TRANSFORMERS_AVAILABLE",
]


