"""
Ollama embedding provider for local embedding generation.
"""

import asyncio
import logging
from typing import List
import httpx
from .base import EmbeddingProvider, EmbeddingResult

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider using Ollama for local embedding generation.
    
    Ollama provides local embedding models like nomic-embed-text.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: float = 30.0,
        max_concurrent: int = 10,
    ):
        """
        Initialize the Ollama embedding provider.

        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11434)
            model: Model name (default: nomic-embed-text)
            timeout: Request timeout in seconds
            max_concurrent: Maximum concurrent requests (default: 10)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self._dimensions = None  # Will be determined on first call

        logger.info(f"Initialized Ollama provider with model: {model} at {base_url} (max_concurrent: {max_concurrent})")

    def generate_embedding(self, text: str) -> EmbeddingResult:
        """
        Generate an embedding for a single text using Ollama.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult containing the embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        url = f"{self.base_url}/api/embeddings"
        
        payload = {
            "model": self.model,
            "prompt": text,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                embedding = data.get("embedding")
                
                if not embedding:
                    raise ValueError(f"No embedding returned from Ollama: {data}")
                
                # Cache dimensions on first call
                if self._dimensions is None:
                    self._dimensions = len(embedding)
                    logger.info(f"Ollama model {self.model} produces {self._dimensions}-dimensional embeddings")
                
                return EmbeddingResult(
                    embedding=embedding,
                    text=text,
                    model=self.model,
                    dimensions=len(embedding),
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Ollama API: {e}")
            raise Exception(f"Failed to generate embedding: {e}")
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def generate_embeddings_batch(self, texts: List[str], use_async: bool = True) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.

        By default uses async/parallel processing for better performance.
        Set use_async=False for sequential processing.

        Args:
            texts: List of texts to embed
            use_async: Use async parallel processing (default: True)

        Returns:
            List of EmbeddingResult objects

        Raises:
            Exception: If embedding generation fails
        """
        if use_async:
            # Use fast async method by default
            return self.generate_embeddings_batch_fast(texts)

        # Fallback to sequential processing
        results = []
        url = f"{self.base_url}/api/embeddings"

        # Use a single HTTP client for all requests to reuse connections
        with httpx.Client(timeout=self.timeout) as client:
            for i, text in enumerate(texts):
                try:
                    payload = {
                        "model": self.model,
                        "prompt": text,
                    }

                    response = client.post(url, json=payload)
                    response.raise_for_status()

                    data = response.json()
                    embedding = data.get("embedding")

                    if not embedding:
                        raise ValueError(f"No embedding returned from Ollama: {data}")

                    # Cache dimensions on first call
                    if self._dimensions is None:
                        self._dimensions = len(embedding)
                        logger.info(f"Ollama model {self.model} produces {self._dimensions}-dimensional embeddings")

                    results.append(EmbeddingResult(
                        embedding=embedding,
                        text=text,
                        model=self.model,
                        dimensions=len(embedding),
                    ))

                    if (i + 1) % 10 == 0:
                        logger.info(f"Generated {i + 1}/{len(texts)} embeddings")

                except httpx.HTTPError as e:
                    logger.error(f"HTTP error generating embedding for text {i}: {e}")
                    raise Exception(f"Failed to generate embedding: {e}")
                except Exception as e:
                    logger.error(f"Failed to generate embedding for text {i}: {e}")
                    raise

        logger.info(f"Successfully generated {len(results)} embeddings")
        return results

    async def _generate_embedding_async(self, client: httpx.AsyncClient, text: str, index: int) -> tuple[int, EmbeddingResult]:
        """
        Generate a single embedding asynchronously.

        Args:
            client: Async HTTP client
            text: Text to embed
            index: Index of this text in the batch

        Returns:
            Tuple of (index, EmbeddingResult)
        """
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text,
        }

        response = await client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        embedding = data.get("embedding")

        if not embedding:
            raise ValueError(f"No embedding returned from Ollama: {data}")

        # Cache dimensions on first call
        if self._dimensions is None:
            self._dimensions = len(embedding)

        return (index, EmbeddingResult(
            embedding=embedding,
            text=text,
            model=self.model,
            dimensions=len(embedding),
        ))

    async def _generate_embeddings_async(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings asynchronously with concurrency control.

        Args:
            texts: List of texts to embed

        Returns:
            List of EmbeddingResult objects in original order
        """
        results = [None] * len(texts)
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def bounded_generate(client, text, index):
            async with semaphore:
                return await self._generate_embedding_async(client, text, index)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [
                bounded_generate(client, text, i)
                for i, text in enumerate(texts)
            ]

            completed = 0
            for coro in asyncio.as_completed(tasks):
                try:
                    index, result = await coro
                    results[index] = result
                    completed += 1

                    if completed % 10 == 0:
                        logger.info(f"Generated {completed}/{len(texts)} embeddings")
                except Exception as e:
                    logger.error(f"Failed to generate embedding: {e}")
                    raise

        logger.info(f"Successfully generated {len(results)} embeddings (async)")
        return results

    def generate_embeddings_batch_fast(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts using async/parallel processing.

        This is significantly faster than the sequential batch method as it
        processes multiple requests concurrently.

        Args:
            texts: List of texts to embed

        Returns:
            List of EmbeddingResult objects

        Raises:
            Exception: If embedding generation fails
        """
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, need to run in a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._generate_embeddings_async(texts))
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(self._generate_embeddings_async(texts))

    def get_dimensions(self) -> int:
        """
        Get the dimensionality of embeddings.
        
        For nomic-embed-text, this is typically 768 dimensions.

        Returns:
            Number of dimensions in embedding vectors
        """
        if self._dimensions is None:
            # Generate a test embedding to determine dimensions
            test_result = self.generate_embedding("test")
            self._dimensions = test_result.dimensions
        
        return self._dimensions

    def get_model_name(self) -> str:
        """
        Get the name of the embedding model.

        Returns:
            Model name string
        """
        return self.model

    def check_health(self) -> bool:
        """
        Check if Ollama is running and the model is available.

        Returns:
            True if Ollama is healthy and model is available, False otherwise
        """
        try:
            # Check if Ollama is running
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                data = response.json()
                models = data.get("models", [])
                
                # Check if our model is available
                model_names = [m.get("name", "").split(":")[0] for m in models]
                
                if self.model in model_names or any(self.model in name for name in model_names):
                    logger.info(f"Ollama is healthy and model {self.model} is available")
                    return True
                else:
                    logger.warning(f"Model {self.model} not found in Ollama. Available models: {model_names}")
                    logger.info(f"You can pull the model with: ollama pull {self.model}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            logger.info("Make sure Ollama is running. Start it with: ollama serve")
            return False


