"""
Sentence Transformers embedding provider for fast local embedding generation.

This provider uses sentence-transformers library directly, which is significantly
faster than calling Ollama API as it runs the model in-process without HTTP overhead.

GPU Support:
- Automatic GPU detection and optimization
- GPU-optimized batch processing
- Graceful fallback to CPU when GPU unavailable
- Device-specific performance tuning
"""

import logging
import os
import threading
from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .base import EmbeddingProvider, EmbeddingResult
from ..paths import path_manager
from ..utils.gpu_utils import (
    detect_optimal_device,
    get_optimal_batch_size,
    get_gpu_info,
    get_gpu_memory_info,
    validate_device_string,
    log_gpu_status,
    format_memory_size,
)

logger = logging.getLogger(__name__)


class SentenceTransformerProvider(EmbeddingProvider):
    """
    Embedding provider using sentence-transformers for fast local embedding generation.

    This is significantly faster than Ollama API as it runs the model in-process.

    GPU Support:
    - Automatic GPU detection and optimization
    - Device-specific batch size optimization
    - GPU memory monitoring and reporting
    - Graceful fallback to CPU when needed

    Recommended models:
    - all-MiniLM-L6-v2 (384 dims, very fast, good quality)
    - paraphrase-MiniLM-L6-v2 (384 dims, optimized for paraphrase)
    - all-mpnet-base-v2 (768 dims, higher quality, slower)
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "auto",
        batch_size: Optional[int] = None,
        lazy_loading: bool = False,
        gpu_memory_monitoring: bool = False,
    ):
        """
        Initialize the Sentence Transformer embedding provider.

        Args:
            model_name: Model name from sentence-transformers
                       (default: all-MiniLM-L6-v2)
            device: Device preference ('auto', 'cuda', 'cpu', 'cuda:0', etc.)
                   'auto' will automatically detect and use GPU if available
            batch_size: Batch size for encoding (None for auto-optimization)
            lazy_loading: If True, defer model loading until first use (default: False)
            gpu_memory_monitoring: If True, monitor and log GPU memory usage
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.device_preference = device or "auto"
        self.lazy_loading = lazy_loading
        self.gpu_memory_monitoring = gpu_memory_monitoring

        # Detect optimal device and batch size
        self.device = detect_optimal_device(self.device_preference)
        self.batch_size = batch_size or get_optimal_batch_size(self.device)

        # Model loading state
        self.model: Optional[SentenceTransformer] = None
        self._dimensions: Optional[int] = None
        self._model_loading = False
        self._model_load_lock = threading.Lock()

        # Log GPU status for debugging
        if self.device.startswith("cuda"):
            log_gpu_status()

        if not lazy_loading:
            # Load model immediately (original behavior)
            self._load_model()
        else:
            logger.info(f"SentenceTransformer provider initialized with lazy loading: {model_name}")
            logger.info(f"Device: {self.device}, Batch size: {self.batch_size}")
            logger.info("Model will be loaded on first use")

    def _load_model(self) -> None:
        """Load the SentenceTransformer model with GPU optimization."""
        # Use local cache directory for model storage
        cache_dir = str(path_manager.get_models_dir())

        # Set HuggingFace cache directory via environment variable
        # HF_HOME is the modern way to control where HuggingFace models are cached
        original_hf_home = os.environ.get('HF_HOME')
        os.environ['HF_HOME'] = cache_dir

        try:
            logger.info(f"Loading sentence-transformers model: {self.model_name}")
            logger.info(f"Target device: {self.device}, Cache: {cache_dir}")

            # Load model with specified device
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self._dimensions = self.model.get_sentence_embedding_dimension()

            # Log GPU memory usage if monitoring enabled
            if self.gpu_memory_monitoring and self.device.startswith("cuda"):
                memory_info = get_gpu_memory_info()
                allocated = format_memory_size(memory_info['allocated'])
                total = format_memory_size(memory_info['total'])
                logger.info(f"GPU memory after model loading: {allocated}/{total}")

        finally:
            # Restore original cache directory setting
            if original_hf_home is not None:
                os.environ['HF_HOME'] = original_hf_home
            else:
                os.environ.pop('HF_HOME', None)

        logger.info(
            f"✓ SentenceTransformer model loaded: {self.model_name} "
            f"({self._dimensions} dimensions, device: {self.model.device}, "
            f"batch_size: {self.batch_size})"
        )

    def _ensure_model_loaded(self) -> None:
        """Ensure the model is loaded, loading it if necessary."""
        if self.model is not None:
            return

        with self._model_load_lock:
            # Double-check pattern
            if self.model is not None:
                return

            if self._model_loading:
                # Another thread is loading, wait for it
                while self._model_loading and self.model is None:
                    threading.Event().wait(0.1)
                return

            self._model_loading = True
            try:
                self._load_model()
            finally:
                self._model_loading = False

    def load_model_async(self) -> None:
        """Load the model asynchronously in a background thread."""
        if self.model is not None or self._model_loading:
            return

        def _load_in_background():
            try:
                self._ensure_model_loaded()
            except Exception as e:
                logger.error(f"Failed to load model in background: {e}", exc_info=True)

        thread = threading.Thread(target=_load_in_background, daemon=True)
        thread.start()

    def generate_embedding(self, text: str) -> EmbeddingResult:
        """
        Generate an embedding for a single text with GPU optimization.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult containing the embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        # Ensure model is loaded
        self._ensure_model_loaded()

        try:
            # Use GPU-optimized parameters based on Milvus recommendations
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                convert_to_tensor=False,  # Keep as numpy for consistency
                batch_size=1,  # Single text
            )

            # Log GPU memory if monitoring enabled
            if self.gpu_memory_monitoring and self.device.startswith("cuda"):
                memory_info = get_gpu_memory_info()
                logger.debug(f"GPU memory after embedding: {format_memory_size(memory_info['allocated'])}")

            return EmbeddingResult(
                embedding=embedding.tolist(),
                text=text,
                model=self.model_name,
                dimensions=len(embedding),
            )
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def generate_embeddings_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts using GPU-optimized batch processing.

        This implementation follows Milvus best practices for GPU acceleration:
        - Uses optimal batch sizes for GPU vs CPU
        - Monitors GPU memory usage
        - Leverages GPU parallelism for maximum performance

        Args:
            texts: List of texts to embed

        Returns:
            List of EmbeddingResult objects

        Raises:
            Exception: If embedding generation fails
        """
        # Ensure model is loaded
        self._ensure_model_loaded()

        try:
            device_type = "GPU" if self.device.startswith("cuda") else "CPU"
            logger.info(f"Generating embeddings for {len(texts)} texts on {device_type} "
                       f"(batch_size: {self.batch_size})")

            # Log initial GPU memory if monitoring enabled
            if self.gpu_memory_monitoring and self.device.startswith("cuda"):
                memory_info = get_gpu_memory_info()
                initial_memory = format_memory_size(memory_info['allocated'])
                logger.info(f"GPU memory before batch processing: {initial_memory}")

            # GPU-optimized encoding with parameters from Milvus documentation
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=len(texts) > 100,  # Only show progress for large batches
                convert_to_numpy=True,
                convert_to_tensor=False,  # Keep as numpy for consistency
                normalize_embeddings=False,  # Let the model decide
            )

            # Log final GPU memory if monitoring enabled
            if self.gpu_memory_monitoring and self.device.startswith("cuda"):
                memory_info = get_gpu_memory_info()
                final_memory = format_memory_size(memory_info['allocated'])
                logger.info(f"GPU memory after batch processing: {final_memory}")

            # Convert to EmbeddingResult objects
            results = [
                EmbeddingResult(
                    embedding=embedding.tolist(),
                    text=text,
                    model=self.model_name,
                    dimensions=len(embedding),
                )
                for text, embedding in zip(texts, embeddings)
            ]

            logger.info(f"✓ Successfully generated {len(results)} embeddings on {device_type}")
            return results

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def get_dimensions(self) -> int:
        """
        Get the dimensionality of embeddings.

        Returns:
            Number of dimensions in embedding vectors
        """
        # For lazy loading, we need to load the model to get dimensions
        if self._dimensions is None:
            self._ensure_model_loaded()
        return self._dimensions

    def get_model_name(self) -> str:
        """
        Get the name of the embedding model.

        Returns:
            Model name string
        """
        return self.model_name

    def check_health(self) -> bool:
        """
        Check if the model is loaded and working, including GPU status.

        Returns:
            True if model is healthy, False otherwise
        """
        try:
            # Ensure model is loaded
            self._ensure_model_loaded()

            # Test with a simple embedding
            test_embedding = self.model.encode("test", convert_to_numpy=True)

            if test_embedding is not None and len(test_embedding) == self._dimensions:
                device_type = "GPU" if self.device.startswith("cuda") else "CPU"
                logger.info(f"✓ SentenceTransformer model {self.model_name} is healthy on {device_type}")

                # Log GPU status if using GPU
                if self.device.startswith("cuda"):
                    gpu_info = get_gpu_info()
                    if gpu_info['cuda_available']:
                        memory_info = get_gpu_memory_info()
                        allocated = format_memory_size(memory_info['allocated'])
                        total = format_memory_size(memory_info['total'])
                        logger.info(f"GPU memory usage: {allocated}/{total}")
                    else:
                        logger.warning("GPU was requested but CUDA is not available")

                return True
            else:
                logger.error("Model health check failed: unexpected embedding dimensions")
                return False

        except Exception as e:
            logger.error(f"Model health check failed: {e}")
            return False

    def get_device_info(self) -> dict:
        """
        Get detailed information about the current device configuration.

        Returns:
            Dictionary with device information
        """
        info = {
            "device_preference": self.device_preference,
            "actual_device": self.device,
            "batch_size": self.batch_size,
            "gpu_memory_monitoring": self.gpu_memory_monitoring,
            "model_loaded": self.model is not None,
        }

        if self.device.startswith("cuda"):
            gpu_info = get_gpu_info()
            info.update({
                "gpu_available": gpu_info['cuda_available'],
                "gpu_count": gpu_info['device_count'],
                "cuda_version": gpu_info['cuda_version'],
            })

            if gpu_info['cuda_available']:
                memory_info = get_gpu_memory_info()
                info.update({
                    "gpu_memory_total": memory_info['total'],
                    "gpu_memory_allocated": memory_info['allocated'],
                    "gpu_memory_free": memory_info['free'],
                })

        return info

