"""
Pydantic models for normalized conversation data structures.

Provides clean, type-safe representations of chat exports without redundancy.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, computed_field


class Message(BaseModel):
    """Individual message within a conversation."""

    id: str = Field(..., description="Unique message identifier")
    timestamp: Optional[float] = Field(None, description="Unix timestamp")
    timestamp_formatted: Optional[str] = Field(None, description="Human-readable timestamp")
    role: str = Field(..., description="Message role: user, assistant, system, etc.")
    text: str = Field(..., description="Message content")
    token_count: int = Field(..., description="Number of tokens in message text")
    parent_id: Optional[str] = Field(None, description="Parent message ID for threading")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "timestamp": 1683420143.639263,
                "timestamp_formatted": "2023-05-06 20:42:23",
                "role": "user",
                "text": "How does semantic search work?",
                "parent_id": None,
            }
        }


class ConversationMetrics(BaseModel):
    """Statistical metrics for a conversation."""

    total_messages: int = Field(..., description="Total number of messages")
    user_messages: int = Field(0, description="Number of user messages")
    assistant_messages: int = Field(0, description="Number of assistant messages")
    total_tokens: int = Field(..., description="Total token count across all messages")
    user_tokens: int = Field(0, description="Total tokens in user messages")
    assistant_tokens: int = Field(0, description="Total tokens in assistant messages")
    avg_tokens_per_message: float = Field(..., description="Average tokens per message")
    median_tokens_per_message: float = Field(..., description="Median tokens per message")
    max_tokens_per_message: int = Field(..., description="Maximum tokens in a single message")
    min_tokens_per_message: int = Field(..., description="Minimum tokens in a single message")
    avg_user_tokens: float = Field(0, description="Average tokens per user message")
    avg_assistant_tokens: float = Field(0, description="Average tokens per assistant message")


class Conversation(BaseModel):
    """
    A conversation with metadata and messages.
    
    This structure eliminates redundancy by grouping messages under their conversation.
    """

    id: str = Field(..., description="Unique conversation identifier")
    title: str = Field(..., description="Conversation title")
    created_at: Optional[float] = Field(None, description="Conversation creation timestamp")
    updated_at: Optional[float] = Field(None, description="Last update timestamp")
    message_count: int = Field(..., description="Total number of messages")
    metrics: ConversationMetrics = Field(..., description="Statistical metrics for the conversation")
    messages: List[Message] = Field(default_factory=list, description="List of messages in chronological order")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "conv-123",
                "title": "Semantic Search Discussion",
                "created_at": 1683420143.0,
                "updated_at": 1683420200.0,
                "message_count": 5,
                "messages": [
                    {
                        "id": "msg-1",
                        "timestamp": 1683420143.639263,
                        "timestamp_formatted": "2023-05-06 20:42:23",
                        "role": "user",
                        "text": "How does semantic search work?",
                        "parent_id": None,
                    }
                ],
            }
        }


class ConversationExport(BaseModel):
    """
    Complete conversation export container.
    
    Root structure for the normalized JSON export.
    """

    export_date: str = Field(..., description="Date of export generation")
    total_conversations: int = Field(..., description="Total number of conversations")
    total_messages: int = Field(..., description="Total number of messages across all conversations")
    conversations: List[Conversation] = Field(default_factory=list, description="List of all conversations")

    class Config:
        json_schema_extra = {
            "example": {
                "export_date": "2024-10-11",
                "total_conversations": 2723,
                "total_messages": 39109,
                "conversations": [],
            }
        }


# Alternative flat structure with separated metadata (more database-friendly)
class ConversationMetadata(BaseModel):
    """Conversation metadata without messages (for lookups)."""

    id: str
    title: str
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    message_count: int = 0
    metrics: ConversationMetrics = Field(..., description="Statistical metrics for the conversation")


# For flat structure, we need to add conversation_id to Message
class MessageWithConversation(BaseModel):
    """Message that includes conversation reference (for flat exports)."""

    id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Reference to parent conversation")
    timestamp: Optional[float] = Field(None, description="Unix timestamp")
    timestamp_formatted: Optional[str] = Field(None, description="Human-readable timestamp")
    role: str = Field(..., description="Message role: user, assistant, system, etc.")
    text: str = Field(..., description="Message content")
    token_count: int = Field(..., description="Number of tokens in message text")
    parent_id: Optional[str] = Field(None, description="Parent message ID for threading")


class FlatExport(BaseModel):
    """
    Alternative flat export structure.
    
    Separates conversations and messages for easier database import or filtering.
    Conversations can be looked up by ID without loading all messages.
    """

    export_date: str
    conversations: List[ConversationMetadata] = Field(
        default_factory=list, description="Conversation metadata index"
    )
    messages: List[MessageWithConversation] = Field(
        default_factory=list, description="All messages with conversation_id references"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "export_date": "2024-10-11",
                "conversations": [
                    {
                        "id": "conv-123",
                        "title": "Semantic Search",
                        "created_at": 1683420143.0,
                        "updated_at": 1683420200.0,
                        "message_count": 5,
                    }
                ],
                "messages": [
                    {
                        "id": "msg-1",
                        "timestamp": 1683420143.0,
                        "timestamp_formatted": "2023-05-06 20:42:23",
                        "role": "user",
                        "text": "How does it work?",
                        "parent_id": None,
                    }
                ],
            }
        }

