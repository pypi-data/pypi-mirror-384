"""Parsers for converting external conversation formats."""

from datetime import datetime
from statistics import mean, median
from typing import Optional, Callable

import tiktoken

from rebrain.ingestion.models import Conversation, Message, ConversationMetrics


def parse_chatgpt_conversation(
    raw_conv: dict,
    encoding: tiktoken.Encoding,
    text_cleaner: Optional[Callable[[str], str]] = None
) -> Conversation:
    """
    Parse raw ChatGPT conversation to clean Conversation object.
    
    Extracts messages from mapping structure, filters by role, counts tokens.
    
    Args:
        raw_conv: Raw conversation dict from ChatGPT export
        encoding: tiktoken encoding for token counting
        text_cleaner: Optional function to clean text (e.g., remove code blocks)
        
    Returns:
        Conversation object with parsed messages and metrics
    """
    exclude_content_types = {
        "code", "thoughts", "reasoning_recap",
        "user_editable_context", "system_error",
    }
    
    conv_id = raw_conv.get("id")
    title = raw_conv.get("title", "Untitled")
    created_at = raw_conv.get("create_time")
    updated_at = raw_conv.get("update_time")
    mapping = raw_conv.get("mapping", {})
    
    messages = []
    
    # Parse mapping structure
    for node_id, node in mapping.items():
        message = node.get("message")
        if not message:
            continue
        
        # Filter by role (only user and assistant)
        role = message.get("author", {}).get("role")
        if role not in ["user", "assistant"]:
            continue
        
        # Filter by content type
        content = message.get("content", {})
        content_type = content.get("content_type", "text")
        if content_type in exclude_content_types:
            continue
        
        # Extract text from parts
        parts = content.get("parts", [])
        if not parts:
            continue
        
        text_parts = [str(p) for p in parts if p and isinstance(p, str)]
        if not text_parts:
            continue
        
        text = "\n".join(text_parts).strip()
        if not text:
            continue
        
        # Clean text if cleaner provided
        if text_cleaner:
            text = text_cleaner(text)
        
        # Count tokens
        token_count = len(encoding.encode(text))
        
        # Create message object
        timestamp = message.get("create_time")
        msg = Message(
            id=node_id,
            timestamp=timestamp,
            timestamp_formatted=datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else None,
            role=role,
            text=text,
            token_count=token_count,
            parent_id=node.get("parent"),
        )
        messages.append(msg)
    
    # Sort messages by timestamp
    messages.sort(key=lambda x: x.timestamp if x.timestamp else float("inf"))
    
    # Calculate metrics
    if messages:
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        all_tokens = [m.token_count for m in messages]
        user_tokens_list = [m.token_count for m in user_messages]
        assistant_tokens_list = [m.token_count for m in assistant_messages]
        
        metrics = ConversationMetrics(
            total_messages=len(messages),
            user_messages=len(user_messages),
            assistant_messages=len(assistant_messages),
            total_tokens=sum(all_tokens),
            user_tokens=sum(user_tokens_list) if user_tokens_list else 0,
            assistant_tokens=sum(assistant_tokens_list) if assistant_tokens_list else 0,
            avg_tokens_per_message=mean(all_tokens),
            median_tokens_per_message=median(all_tokens),
            max_tokens_per_message=max(all_tokens),
            min_tokens_per_message=min(all_tokens),
            avg_user_tokens=mean(user_tokens_list) if user_tokens_list else 0,
            avg_assistant_tokens=mean(assistant_tokens_list) if assistant_tokens_list else 0,
        )
    else:
        metrics = ConversationMetrics(
            total_messages=0,
            total_tokens=0,
            avg_tokens_per_message=0,
            median_tokens_per_message=0,
            max_tokens_per_message=0,
            min_tokens_per_message=0,
        )
    
    # Create conversation object
    conversation = Conversation(
        id=conv_id,
        title=title,
        created_at=created_at,
        updated_at=updated_at,
        message_count=len(messages),
        metrics=metrics,
        messages=messages,
    )
    
    return conversation

