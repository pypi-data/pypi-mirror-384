"""Tests for retrieval module."""

import pytest
from rebrain.retrieval.query import MemoryQuery


def test_memory_query_init():
    """Test query interface initialization."""
    query = MemoryQuery()
    assert query.embedding_model is not None


# TODO: Add more tests as implementation progresses
# - Test query with mock memory store
# - Test reasoning hops
# - Test context generation

