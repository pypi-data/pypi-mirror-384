"""
Stage 1: Ingestion

Load, normalize, chunk, and annotate chat exports into memory-sized units.
"""

from rebrain.ingestion.loaders import ChatLoader, ChatGPTJSONLoader
from rebrain.ingestion.chunkers import MemoryChunker
from rebrain.ingestion.parsers import parse_chatgpt_conversation
from rebrain.ingestion.models import (
    Conversation,
    ConversationExport,
    ConversationMetadata,
    ConversationMetrics,
    FlatExport,
    Message,
    MessageWithConversation,
)

__all__ = [
    "ChatLoader",
    "ChatGPTJSONLoader",
    "MemoryChunker",
    "parse_chatgpt_conversation",
    "Conversation",
    "ConversationExport",
    "ConversationMetadata",
    "ConversationMetrics",
    "FlatExport",
    "Message",
    "MessageWithConversation",
]

