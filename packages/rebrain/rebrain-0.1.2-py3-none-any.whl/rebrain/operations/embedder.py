"""
Unified embedding module using GenAIClient.

Generates vector representations for semantic search and clustering.
"""

import time
from typing import List, Optional

import numpy as np

from rebrain.core import GenAIClient
from config.settings import settings
from config.loader import get_config


class Embedder:
    """
    Unified embedder using GenAIClient for all embedding operations.
    
    Consolidates embedding logic with rate limiting, retry, and batch processing.
    """

    def __init__(self, batch_size: Optional[int] = None, rate_delay: Optional[float] = None):
        """
        Initialize embedder with unified GenAI client.
        
        Args:
            batch_size: Batch size (defaults from pipeline.yaml)
            rate_delay: Rate delay between batches (defaults from pipeline.yaml)
        """
        self.client = GenAIClient()
        self.model = settings.gemini_embedding_model
        self.dimension = settings.gemini_embedding_dimension
        
        # Load from config if not provided
        if batch_size is None or rate_delay is None:
            _, config = get_config()
            batch_size = batch_size or config.observation_embedding.batch_size
            rate_delay = rate_delay or config.observation_embedding.rate_delay
        
        self.batch_size = batch_size
        self.rate_delay = rate_delay

    def embed_texts(
        self,
        texts: List[str],
        show_progress: bool = True,
        retry_on_failure: bool = True
    ) -> np.ndarray:
        """
        Embed list of texts with rate limiting and retry.
        
        Args:
            texts: List of texts to embed
            show_progress: Print progress messages
            retry_on_failure: Retry failed batches with exponential backoff
        
        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        all_embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i+self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            if show_progress:
                print(f"Batch {batch_num}/{total_batches} ({len(batch_texts)} texts)...", end=" ", flush=True)
            
            # Retry logic
            max_retries = 2 if retry_on_failure else 0
            retry_delays = [20, 40]  # Seconds
            success = False
            
            for attempt in range(max_retries + 1):
                try:
                    # Use GenAIClient.embed() method
                    # Note: model and dimension come from settings inside GenAIClient
                    embeddings_batch = self.client.embed(
                        texts=batch_texts,
                        batch_size=len(batch_texts),  # Single API call per batch
                        rate_delay=0,  # We handle rate limiting here
                        verbose=False  # We handle progress here
                    )
                    
                    all_embeddings.extend(embeddings_batch)
                    
                    if show_progress:
                        print("✓")
                    
                    success = True
                    break
                    
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        # Rate limit error
                        if attempt < max_retries:
                            wait_time = retry_delays[attempt]
                            if show_progress:
                                print(f"⚠️  Rate limit, waiting {wait_time}s...", end=" ", flush=True)
                            time.sleep(wait_time)
                            if show_progress:
                                print(f"retrying...", end=" ", flush=True)
                        else:
                            if show_progress:
                                print(f"✗ Failed after {max_retries + 1} attempts")
                            raise RuntimeError(f"Rate limit exceeded after retries on batch {batch_num}")
                    else:
                        # Other error
                        if show_progress:
                            print(f"✗ Error: {e}")
                        raise
            
            if not success:
                # Should not reach here due to raises above, but safety net
                raise RuntimeError(f"Failed to embed batch {batch_num}")
            
            # Rate limiting between batches
            if i + self.batch_size < len(texts):
                time.sleep(self.rate_delay)
        
        # Convert to numpy array
        embeddings_array = np.array(all_embeddings, dtype=np.float32)
        return embeddings_array

    def embed_single(self, text: str) -> np.ndarray:
        """
        Embed a single text (convenience method).
        
        Args:
            text: Text to embed
        
        Returns:
            numpy array of shape (embedding_dim,)
        """
        result = self.embed_texts([text], show_progress=False)
        return result[0]

