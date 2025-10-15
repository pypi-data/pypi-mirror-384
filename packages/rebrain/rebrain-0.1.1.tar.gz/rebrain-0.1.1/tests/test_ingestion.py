"""Tests for ingestion module."""

import pytest
from rebrain.ingestion.chunkers import MemoryChunker
from rebrain.ingestion.annotators import MemoryAnnotator


def test_memory_chunker_single_chunk():
    """Test chunking of message that fits in one chunk."""
    chunker = MemoryChunker(chunk_size=100)
    message = {
        "text": "Short message",
        "timestamp": "2024-01-01T00:00:00",
        "role": "user",
    }

    chunks = chunker.chunk_message(message)

    assert len(chunks) == 1
    assert chunks[0]["text"] == "Short message"
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["total_chunks"] == 1


def test_memory_annotator():
    """Test memory annotation."""
    annotator = MemoryAnnotator()
    chunk = {
        "text": "I need to fix a bug in my Python code",
        "timestamp": "2024-01-01T00:00:00",
        "role": "user",
    }

    annotated = annotator.annotate(chunk)

    assert "domain" in annotated
    assert annotated["domain"] == "technical"


# TODO: Add more tests as implementation progresses

