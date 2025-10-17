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
import sys
from datetime import datetime
from pathlib import Path

import tiktoken

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.loader import load_config
from rebrain.operations import DateFilter
from rebrain.utils.text_cleaning import remove_code_blocks
from rebrain.ingestion.parsers import parse_chatgpt_conversation, truncate_conversation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Transform and filter conversations."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Transform and filter raw conversations")
    parser.add_argument("--data-path", type=str, default=None,
                        help="Base data directory (overrides config, e.g., temp_data)")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to custom pipeline.yaml")
    parser.add_argument("--max-conversations", type=int, default=1000,
                        help="Maximum number of conversations to process (default: 1000)")
    args = parser.parse_args()
    
    start_time = datetime.now()
    
    # Load configuration
    try:
        _, config = load_config(config_path=args.config)
        # Use CLI data-path if provided, otherwise use config
        if args.data_path:
            data_path = Path(args.data_path)
        else:
            data_path = Path(config.paths.data_dir)
        cutoff_days = config.ingestion.date_cutoff_days
        remove_code = config.ingestion.remove_code_blocks
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1
    
    # Paths (fixed relative to data_path)
    input_file = data_path / "raw/conversations.json"
    output_file = data_path / "preprocessed/conversations_clean.json"
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
    
    # Prepare text cleaner if needed
    text_cleaner = remove_code_blocks if remove_code else None
    
    for raw_conv in raw_conversations:
        try:
            conv = parse_chatgpt_conversation(raw_conv, encoding, text_cleaner)
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
    
    # Apply truncation strategy (head+tail for long conversations)
    logger.info("Applying truncation strategy...")
    truncated_dicts = []
    truncation_stats = {"total": 0, "tier1": 0, "tier2": 0, "tier3": 0}
    
    for conv in filtered_dicts:
        total_tokens = conv.get("metrics", {}).get("total_tokens", 0)
        
        if total_tokens <= 5000:
            # Tier 1: Keep as-is
            truncated_dicts.append(conv)
            truncation_stats["tier1"] += 1
        else:
            # Tier 2+: Truncate with 2000 head + 3000 tail
            truncated_conv = truncate_conversation(
                conversation=conv,
                max_tokens=5000,
                head_tokens=2000,
                tail_tokens=3000
            )
            truncated_dicts.append(truncated_conv)
            if truncated_conv.get("truncated"):
                truncation_stats["total"] += 1
                if total_tokens <= 20000:
                    truncation_stats["tier2"] += 1
                else:
                    truncation_stats["tier3"] += 1
    
    logger.info(f"Truncation: {truncation_stats['total']:,} conversations truncated")
    logger.info(f"  Tier 1 (≤5K): {truncation_stats['tier1']:,} kept as-is")
    logger.info(f"  Tier 2 (5K-20K): {truncation_stats['tier2']:,} truncated")
    logger.info(f"  Tier 3 (>20K): {truncation_stats['tier3']:,} truncated")
    
    # Calculate overall statistics (using truncated conversations)
    total_messages = sum(c.get("message_count", 0) for c in truncated_dicts)
    total_tokens = sum(c.get("metrics", {}).get("total_tokens", 0) for c in truncated_dicts)
    avg_tokens = total_tokens / len(truncated_dicts) if truncated_dicts else 0
    
    logger.info(f"Stats (after truncation): {total_messages:,} messages, {total_tokens:,} tokens (avg {avg_tokens:,.0f}/conv)")
    
    # Save truncated conversations
    logger.info(f"Saving truncated conversations: {output_file}")
    output_data = {
        "export_date": datetime.now().isoformat(),
        "filter_cutoff_days": cutoff_days,
        "remove_code_blocks": remove_code,
        "truncation_applied": True,
        "truncation_strategy": "head_2000_tail_3000",
        "total_conversations": len(truncated_dicts),
        "total_messages": total_messages,
        "total_tokens": total_tokens,
        "truncated_count": truncation_stats["total"],
        "conversations": truncated_dicts
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

