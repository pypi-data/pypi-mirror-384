#!/usr/bin/env python3
"""
Step 1: Transform & Filter Conversations

Transform raw ChatGPT JSON (with mapping structure) to clean, AI-ready format.

Input: data/raw/conversations.json (raw ChatGPT export)
Output: data/preprocessed/conversations_clean.json (clean messages array)
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean, median

import tiktoken

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.loader import get_config
from rebrain.operations import DateFilter
from rebrain.ingestion.models import Conversation, Message, ConversationMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def remove_code_blocks(text: str) -> str:
    """
    Remove markdown code blocks and replace with placeholders.
    
    Handles multiple formats:
    - Closed blocks: ```language\ncode```
    - Unclosed blocks: ```language\ncode (to end of text)
    - Multiple passes to ensure all removed
    """
    # Multiple passes to catch nested or edge cases
    max_iterations = 5
    for _ in range(max_iterations):
        original_text = text
        
        # Pattern 1: Closed code blocks (greedy to catch long blocks)
        text = re.sub(r'```[^\n]*\n[\s\S]*?```', '[Code redacted]', text)
        
        # Pattern 2: Code blocks without newline after opening
        text = re.sub(r'```[^\n]*[\s\S]*?```', '[Code redacted]', text)
        
        # Pattern 3: Unclosed code blocks (``` to end of line/text)
        # This catches cases where ``` opens but never closes
        text = re.sub(r'```[^\n]*\n[\s\S]+$', '[Code redacted]', text)
        text = re.sub(r'```[^\n]+$', '[Code redacted]', text)
        
        # If no changes, we're done
        if text == original_text:
            break
    
    # Also remove long inline code (>100 chars suggests code)
    def replace_inline(match):
        content = match.group(1)
        if len(content) > 100:
            return '[Inline code redacted]'
        return match.group(0)
    
    text = re.sub(r'`([^`]{100,})`', replace_inline, text)
    
    # Final cleanup: remove any remaining triple backticks
    text = text.replace('```', '')
    
    return text


def parse_conversation(raw_conv: dict, encoding, remove_code: bool) -> Conversation:
    """
    Parse raw ChatGPT conversation to clean Conversation object.
    
    Extracts messages from mapping structure, filters by role, counts tokens.
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
        
        # Remove code blocks if requested
        if remove_code:
            text = remove_code_blocks(text)
        
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


def main():
    """Transform and filter conversations."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Transform and filter raw conversations")
    parser.add_argument("-i", "--input", default="data/raw/conversations.json",
                        help="Input file path (default: data/raw/conversations.json)")
    parser.add_argument("-o", "--output", default="data/preprocessed/conversations_clean.json",
                        help="Output file path (default: data/preprocessed/conversations_clean.json)")
    parser.add_argument("--max-conversations", type=int, default=1000,
                        help="Maximum number of conversations to process (default: 1000)")
    args = parser.parse_args()
    
    start_time = datetime.now()
    
    # Load configuration
    try:
        _, config = get_config()
        cutoff_days = config.ingestion.date_cutoff_days
        remove_code = config.ingestion.remove_code_blocks
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1
    
    # Paths
    input_file = Path(args.input)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("STEP 1: TRANSFORM & FILTER CONVERSATIONS")
    logger.info("=" * 70)
    
    # Load raw conversations
    logger.info(f"Loading raw data: {input_file}")
    try:
        with open(input_file) as f:
            raw_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load input: {e}")
        return 1
    
    # Handle both list and dict formats
    if isinstance(raw_data, dict) and "conversations" in raw_data:
        raw_conversations = raw_data["conversations"]
    else:
        raw_conversations = raw_data
    
    logger.info(f"Loaded {len(raw_conversations):,} raw conversations")
    
    # Initialize tokenizer
    logger.info("Initializing tiktoken encoder...")
    encoding = tiktoken.get_encoding("cl100k_base")
    
    # Transform conversations
    logger.info(f"Transforming conversations (remove_code_blocks={remove_code})...")
    conversations = []
    skipped = 0
    
    for raw_conv in raw_conversations:
        try:
            conv = parse_conversation(raw_conv, encoding, remove_code)
            if conv.messages:  # Only keep conversations with messages
                conversations.append(conv)
            else:
                skipped += 1
        except Exception as e:
            logger.warning(f"Failed to parse conversation {raw_conv.get('id', 'unknown')}: {e}")
            skipped += 1
    
    logger.info(f"Transformed: {len(conversations):,} | Skipped: {skipped} (no messages)")
    
    # Filter by date
    logger.info(f"Filtering by date: last {cutoff_days} days")
    
    # Convert Conversation objects to dicts for date filtering
    conv_dicts = [c.model_dump() for c in conversations]
    
    try:
        filtered_dicts = DateFilter.filter_by_cutoff(
            items=conv_dicts,
            cutoff_days=cutoff_days,
            date_field="created_at"
        )
    except Exception as e:
        logger.error(f"Date filtering failed: {e}")
        return 1
    
    removed = len(conversations) - len(filtered_dicts)
    logger.info(f"Kept: {len(filtered_dicts):,} | Removed: {removed:,}")
    
    # Apply max-conversations limit if specified
    if args.max_conversations and len(filtered_dicts) > args.max_conversations:
        logger.info(f"Limiting to {args.max_conversations:,} most recent conversations")
        # Sort by created_at descending (most recent first)
        filtered_dicts = sorted(filtered_dicts, key=lambda x: x.get("created_at", 0), reverse=True)
        filtered_dicts = filtered_dicts[:args.max_conversations]
        logger.info(f"After limit: {len(filtered_dicts):,} conversations")
    
    # Calculate overall statistics
    total_messages = sum(c.get("message_count", 0) for c in filtered_dicts)
    total_tokens = sum(c.get("metrics", {}).get("total_tokens", 0) for c in filtered_dicts)
    avg_tokens = total_tokens / len(filtered_dicts) if filtered_dicts else 0
    
    logger.info(f"Stats: {total_messages:,} messages, {total_tokens:,} tokens (avg {avg_tokens:,.0f}/conv)")
    
    # Save clean conversations
    logger.info(f"Saving clean conversations: {output_file}")
    output_data = {
        "export_date": datetime.now().isoformat(),
        "filter_cutoff_days": cutoff_days,
        "remove_code_blocks": remove_code,
        "total_conversations": len(filtered_dicts),
        "total_messages": total_messages,
        "total_tokens": total_tokens,
        "conversations": filtered_dicts
    }
    
    try:
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        file_size_mb = output_file.stat().st_size / 1024 / 1024
        logger.info(f"Saved: {file_size_mb:.2f} MB")
    except Exception as e:
        logger.error(f"Failed to save output: {e}")
        return 1
    
    duration = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 70)
    logger.info(f"✅ STEP 1 COMPLETE ({duration:.1f}s)")
    logger.info("=" * 70)
    logger.info("Next: ./cli.sh step2")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

