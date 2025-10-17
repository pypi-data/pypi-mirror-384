"""
Pydantic models for normalized conversation data structures.

Provides clean, type-safe representations of chat exports without redundancy.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Individual message within a conversation."""

    id: str = Field(..., description="Unique message identifier")
    timestamp: Optional[float] = Field(None, description="Unix timestamp")
    timestamp_formatted: Optional[str] = Field(None, description="Human-readable timestamp")
    role: str = Field(..., description="Message role: user, assistant, system, etc.")
    text: str = Field(..., description="Message content")
    token_count: int = Field(..., description="Number of tokens in message text")
    parent_id: Optional[str] = Field(None, description="Parent message ID for threading")


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

