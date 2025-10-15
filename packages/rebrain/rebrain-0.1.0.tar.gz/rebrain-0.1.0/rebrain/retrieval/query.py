"""
Memory query interface with reasoning hops.

Enables retrieval across multiple layers:
- Direct memory search (observation level)
- Learning retrieval (synthesized patterns)
- Cognition access (persona level)
"""

from typing import List, Dict, Any, Optional

from google import genai

from config.settings import settings


class MemoryQuery:
    """Query interface for memory retrieval with reasoning hops."""

    def __init__(self, memory_store=None):
        """
        Initialize query interface.

        Args:
            memory_store: memg-core storage instance (to be integrated)
        """
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.memory_store = memory_store
        self.embedding_model = settings.gemini_embedding_model

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        include_learnings: bool = True,
        include_cognitions: bool = True,
        max_hops: int = 2,
    ) -> Dict[str, Any]:
        """
        Query memory with optional reasoning hops.

        Args:
            query_text: Query text
            top_k: Number of top results to return
            include_learnings: Include related learnings
            include_cognitions: Include related cognitions
            max_hops: Maximum graph traversal hops

        Returns:
            Query results with memories, learnings, and cognitions
        """
        # Generate query embedding
        query_embedding = self._embed_query(query_text)

        # Vector search for direct memories
        memories = self._search_memories(query_embedding, top_k)

        results = {"query": query_text, "memories": memories, "learnings": [], "cognitions": []}

        # Optional: Traverse graph for learnings
        if include_learnings and memories:
            results["learnings"] = self._get_related_learnings(memories)

        # Optional: Get cognitions
        if include_cognitions and results["learnings"]:
            results["cognitions"] = self._get_related_cognitions(results["learnings"])

        return results

    def _embed_query(self, query_text: str) -> List[float]:
        """Generate embedding for query."""
        result = self.client.models.embed_content(
            model=self.embedding_model,
            content=query_text,
        )
        return result.embeddings[0].values

    def _search_memories(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """
        Vector search for memories.

        TODO: Integrate with memg-core Qdrant storage.
        """
        if self.memory_store is None:
            # Placeholder until memg-core is integrated
            return []

        # TODO: Implement actual vector search
        # memories = self.memory_store.search_memories(query_embedding, top_k)
        return []

    def _get_related_learnings(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get learnings related to retrieved memories via graph traversal.

        TODO: Integrate with memg-core Kuzu graph traversal.
        """
        if self.memory_store is None:
            return []

        # TODO: Implement graph traversal
        # Follow 'derived_from' relations from memories to learnings
        return []

    def _get_related_cognitions(self, learnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get cognitions related to learnings via graph traversal.

        TODO: Integrate with memg-core Kuzu graph traversal.
        """
        if self.memory_store is None:
            return []

        # TODO: Implement graph traversal
        # Follow 'synthesizes' relations from learnings to cognitions
        return []

    def get_context_for_prompt(self, query_text: str, max_tokens: int = 2000) -> str:
        """
        Get context for LLM prompt from query.

        Args:
            query_text: Query text
            max_tokens: Maximum context tokens

        Returns:
            Formatted context string
        """
        results = self.query(query_text, include_learnings=True, include_cognitions=True)

        context_parts = []

        # Add cognitions (persona level)
        if results["cognitions"]:
            context_parts.append("## Persona Cognitions:")
            for cog in results["cognitions"][:3]:
                context_parts.append(f"- {cog.get('statement')}")

        # Add learnings
        if results["learnings"]:
            context_parts.append("\n## Related Learnings:")
            for learning in results["learnings"][:5]:
                context_parts.append(f"- {learning.get('statement')}")

        # Add specific memories
        if results["memories"]:
            context_parts.append("\n## Relevant Memories:")
            for memory in results["memories"][:5]:
                context_parts.append(f"- {memory.get('text', '')[:200]}...")

        return "\n".join(context_parts)

