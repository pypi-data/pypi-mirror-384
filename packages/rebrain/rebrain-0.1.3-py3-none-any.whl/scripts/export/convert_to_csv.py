#!/usr/bin/env python3
"""
Simple converter: ChatGPT conversations.json → CSV

Extracts only core conversation messages (user and assistant text).
No API calls, no processing - just JSON to CSV using pandas.
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


def normalize_text_for_csv(text):
    """
    Normalize text to prevent CSV formatting issues.
    
    - Replaces actual line breaks with literal \n
    - Compresses multiple \n\n to single \n
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text suitable for CSV
    """
    # Replace actual newlines with literal \n
    text = text.replace('\n', '\\n')
    
    # Replace multiple consecutive \n with single \n
    text = re.sub(r'(\\n){2,}', r'\\n', text)
    
    return text


def remove_code_blocks(text):
    """
    Remove markdown code blocks and replace with descriptive placeholders.
    
    Matches patterns like:
    ```python
    code here
    ```
    
    Args:
        text: Text containing potential code blocks
        
    Returns:
        Text with code blocks replaced by placeholders
    """
    # Pattern to match code blocks with optional language identifier
    # Matches ```language\ncode\n``` or ```\ncode\n```
    pattern = r'```(\w+)?\n(.*?)```'
    
    def replace_block(match):
        language = match.group(1)
        if language:
            # Capitalize first letter for better readability
            lang_name = language.capitalize()
            return f"[{lang_name} code redacted]"
        else:
            return "[Code block redacted]"
    
    # Replace all code blocks
    cleaned = re.sub(pattern, replace_block, text, flags=re.DOTALL)
    
    return cleaned


def load_conversations(file_path):
    """Load conversations from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_messages(conversations, remove_code_blocks_flag=True):
    """
    Extract simple message records from conversations.
    
    Filters to only user and assistant text messages.
    Excludes code, thoughts, and other auxiliary content.
    
    Args:
        conversations: List of conversation objects
        remove_code_blocks_flag: If True, remove code blocks and replace with placeholders
    
    Returns:
        List of message records
    """
    records = []
    
    exclude_content_types = {
        "code",
        "thoughts", 
        "reasoning_recap",
        "user_editable_context",
        "system_error",
    }
    
    for conv in conversations:
        conv_id = conv.get("id")
        conv_title = conv.get("title", "Untitled")
        mapping = conv.get("mapping", {})
        
        for node_id, node in mapping.items():
            message = node.get("message")
            if not message:
                continue
            
            # Get role
            role = message.get("author", {}).get("role")
            if role not in ["user", "assistant"]:
                continue
            
            # Get content
            content = message.get("content", {})
            content_type = content.get("content_type", "text")
            
            # Skip non-text content
            if content_type in exclude_content_types:
                continue
            
            # Extract text from parts
            parts = content.get("parts", [])
            if not parts:
                continue
            
            # Join text parts
            text_parts = [str(p) for p in parts if p and isinstance(p, str)]
            if not text_parts:
                continue
            
            text = "\n".join(text_parts).strip()
            if not text:
                continue
            
            # Remove code blocks if requested
            if remove_code_blocks_flag:
                text = remove_code_blocks(text)
            
            # Normalize text for CSV (replace newlines with \n, compress multiple \n)
            text = normalize_text_for_csv(text)
            
            # Create record
            timestamp = message.get("create_time")
            records.append({
                "id": node_id,
                "conversation_id": conv_id,
                "conversation_title": conv_title,
                "timestamp": timestamp,
                "timestamp_formatted": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "",
                "role": role,
                "message": text,
            })
    
    return records


def main(remove_code_blocks_flag=True):
    """
    Convert conversations.json to CSV.
    
    Args:
        remove_code_blocks_flag: If True (default), remove code blocks and replace with placeholders
    """
    input_file = Path("data/raw/conversations.json")
    output_file = Path("data/exports/conversations_simple.csv")
    
    print(f"📖 Loading: {input_file}")
    conversations = load_conversations(input_file)
    print(f"   Found {len(conversations)} conversations")
    
    print(f"\n🔍 Extracting messages...")
    print(f"   Code block removal: {'✓ Enabled' if remove_code_blocks_flag else '✗ Disabled'}")
    records = extract_messages(conversations, remove_code_blocks_flag)
    print(f"   Extracted {len(records)} core messages")
    
    # Convert to DataFrame
    df = pd.DataFrame(records)
    
    # Sort by timestamp
    df = df.sort_values("timestamp", na_position="last")
    
    # Stats
    print(f"\n📊 Statistics:")
    print(f"   - Total conversations: {df['conversation_id'].nunique()}")
    print(f"   - User messages: {(df['role'] == 'user').sum()}")
    print(f"   - Assistant messages: {(df['role'] == 'assistant').sum()}")
    
    # Save to CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Saved to: {output_file}")
    print(f"   Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Show sample
    print(f"\n📝 First 3 messages:")
    for idx, row in df.head(3).iterrows():
        print(f"\n   [{row['role']}] {row['conversation_title']}")
        preview = row['message'][:80] + "..." if len(row['message']) > 80 else row['message']
        print(f"   {preview}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert ChatGPT conversations.json to simple CSV format"
    )
    parser.add_argument(
        "--keep-code-blocks",
        action="store_true",
        help="Keep code blocks instead of replacing with placeholders (default: False)",
    )
    
    args = parser.parse_args()
    
    # Invert the flag: by default we remove code blocks
    remove_code_blocks_flag = not args.keep_code_blocks
    
    main(remove_code_blocks_flag)
