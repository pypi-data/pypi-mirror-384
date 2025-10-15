"""
Memory chunker for splitting long messages into memory-sized units.

Chunks are limited to ~2K tokens with 10-15% overlap for context continuity.
"""

from typing import List, Dict, Any, Optional

import tiktoken

from config.loader import get_config


class MemoryChunker:
    """Chunk messages into memory-sized units with overlap."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        overlap_percent: Optional[float] = None,
        encoding_name: str = "cl100k_base",
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in tokens (defaults from pipeline.yaml)
            overlap_percent: Overlap between chunks as percentage (defaults from pipeline.yaml)
            encoding_name: Tokenizer encoding name
        """
        # Load from config if not provided
        if chunk_size is None or overlap_percent is None:
            _, config = get_config()
            chunk_size = chunk_size or config.ingestion.chunk_size_tokens
            overlap_percent = overlap_percent or config.ingestion.chunk_overlap_percent
        
        self.chunk_size = chunk_size
        self.overlap_tokens = int(chunk_size * overlap_percent)
        self.encoding = tiktoken.get_encoding(encoding_name)

    def chunk_message(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk a single message if it exceeds chunk_size.

        Args:
            message: Normalized message dict

        Returns:
            List of chunked messages with metadata
        """
        text = message["text"]
        tokens = self.encoding.encode(text)

        # If message fits in one chunk, return as-is
        if len(tokens) <= self.chunk_size:
            return [
                {
                    **message,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "token_count": len(tokens),
                }
            ]

        # Split into overlapping chunks
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)

            chunks.append(
                {
                    **message,
                    "text": chunk_text,
                    "chunk_index": chunk_index,
                    "total_chunks": None,  # Will be set after loop
                    "token_count": len(chunk_tokens),
                }
            )

            # Move forward, but overlap
            start = end - self.overlap_tokens if end < len(tokens) else end
            chunk_index += 1

        # Set total_chunks for all chunks
        total = len(chunks)
        for chunk in chunks:
            chunk["total_chunks"] = total

        return chunks

    def chunk_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk a list of messages.

        Args:
            messages: List of normalized messages

        Returns:
            Flat list of chunked messages
        """
        all_chunks = []
        for message in messages:
            chunks = self.chunk_message(message)
            all_chunks.extend(chunks)
        return all_chunks

