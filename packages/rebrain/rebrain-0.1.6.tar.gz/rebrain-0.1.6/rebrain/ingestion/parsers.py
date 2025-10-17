"""Parsers for converting external conversation formats."""

from datetime import datetime
from statistics import mean, median
from typing import Optional, Callable, Dict, Any, List

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


def truncate_conversation(
    conversation: Dict[str, Any],
    max_tokens: int = 5000,
    head_tokens: int = 2000,
    tail_tokens: int = 3000
) -> Dict[str, Any]:
    """
    Truncate long conversations using head+tail strategy.
    
    Keeps first N tokens and last M tokens, removing middle messages if needed.
    Adds clear truncation marker between head and tail.
    
    Args:
        conversation: Conversation dict with messages
        max_tokens: Threshold to trigger truncation (default: 5000)
        head_tokens: Tokens to keep from start (default: 2000)
        tail_tokens: Tokens to keep from end (default: 3000)
        
    Returns:
        Truncated conversation dict (or original if below threshold)
    """
    total_tokens = conversation.get("metrics", {}).get("total_tokens", 0)
    
    # No truncation needed
    if total_tokens <= max_tokens:
        return conversation
    
    messages = conversation.get("messages", [])
    if not messages:
        return conversation
    
    # Build head (first messages up to head_tokens)
    head_messages = []
    head_token_count = 0
    head_idx = 0
    
    for idx, msg in enumerate(messages):
        msg_tokens = msg.get("token_count", 0)
        if head_token_count + msg_tokens <= head_tokens:
            head_messages.append(msg)
            head_token_count += msg_tokens
            head_idx = idx
        else:
            break
    
    # Build tail (last messages up to tail_tokens, working backwards)
    tail_messages = []
    tail_token_count = 0
    tail_idx = len(messages)
    
    for idx in range(len(messages) - 1, head_idx, -1):
        msg = messages[idx]
        msg_tokens = msg.get("token_count", 0)
        if tail_token_count + msg_tokens <= tail_tokens:
            tail_messages.insert(0, msg)  # Insert at start to maintain order
            tail_token_count += msg_tokens
            tail_idx = idx
        else:
            break
    
    # Calculate how many messages were truncated
    truncated_count = tail_idx - head_idx - 1
    
    # If no messages were truncated (overlap), return original
    if truncated_count <= 0:
        return conversation
    
    # Create truncation marker as a fake "system" message
    truncation_marker = {
        "id": "truncation_marker",
        "timestamp": None,
        "timestamp_formatted": None,
        "role": "system",
        "text": f"[{truncated_count} MESSAGES TRUNCATED FOR BREVITY]",
        "token_count": 10,  # Approximate
        "parent_id": None
    }
    
    # Combine: head + marker + tail
    truncated_messages = head_messages + [truncation_marker] + tail_messages
    
    # Update conversation
    truncated_conversation = conversation.copy()
    truncated_conversation["messages"] = truncated_messages
    truncated_conversation["message_count"] = len(truncated_messages)
    truncated_conversation["truncated"] = True
    truncated_conversation["original_message_count"] = len(messages)
    truncated_conversation["truncated_message_count"] = truncated_count
    
    # Recalculate metrics
    new_total_tokens = head_token_count + tail_token_count + 10  # +10 for marker
    old_metrics = conversation["metrics"]
    truncated_conversation["metrics"] = {
        **old_metrics,
        "total_tokens": new_total_tokens,
        "original_total_tokens": total_tokens,
    }
    
    return truncated_conversation


def format_conversation_for_llm(conversation: Dict[str, Any]) -> str:
    """
    Format conversation for LLM input using clean plain text format.
    
    Converts conversation dict to human-readable format with:
    - Header with title, date range, message count
    - USER/ASSISTANT message pairs
    - Clear truncation markers if present
    
    Args:
        conversation: Conversation dict with messages and metadata
        
    Returns:
        Formatted string ready for LLM input
    """
    lines = []
    
    # Header with metadata
    title = conversation.get("title", "Untitled")
    
    # Format dates if available
    created_at = conversation.get("created_at")
    updated_at = conversation.get("updated_at")
    
    if created_at and updated_at:
        start_date = datetime.fromtimestamp(created_at).strftime("%b %d, %Y")
        end_date = datetime.fromtimestamp(updated_at).strftime("%b %d, %Y")
        date_range = f"{start_date} → {end_date}" if start_date != end_date else start_date
    else:
        date_range = "Unknown date"
    
    # Message count with truncation info
    message_count = conversation.get("message_count", 0)
    truncated_count = conversation.get("truncated_message_count", 0)
    
    if truncated_count > 0:
        msg_info = f"{message_count} messages ({truncated_count} truncated)"
    else:
        msg_info = f"{message_count} messages"
    
    # Build header
    lines.append(f'Conversation: "{title}"')
    lines.append(f"Period: {date_range}")
    lines.append(f"Messages: {msg_info}")
    lines.append("")  # Blank line
    
    # Format messages
    messages = conversation.get("messages", [])
    
    for msg in messages:
        role = msg.get("role", "unknown")
        text = msg.get("text", "")
        
        # Handle different roles
        if role == "user":
            lines.append(f"USER: {text}")
        elif role == "assistant":
            lines.append(f"ASSISTANT: {text}")
        elif role == "system":
            # System messages (like truncation markers) go as-is
            lines.append(text)
        else:
            # Fallback for unknown roles
            lines.append(f"{role.upper()}: {text}")
        
        lines.append("")  # Blank line between messages
    
    return "\n".join(lines)

