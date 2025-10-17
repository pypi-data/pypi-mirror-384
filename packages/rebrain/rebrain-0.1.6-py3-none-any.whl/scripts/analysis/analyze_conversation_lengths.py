#!/usr/bin/env python3
"""Analyze conversation length distribution."""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from config.settings import settings
from config.loader import get_config


def main():
    # Load default from config
    _, config = get_config()
    default_cutoff = config.ingestion.date_cutoff_days
    
    # Parse CLI args
    parser = argparse.ArgumentParser(description="Analyze conversation lengths")
    parser.add_argument("--cutoff-days", type=int, default=None,
                        help=f"Only analyze conversations from last N days (default: {default_cutoff} from pipeline.yaml)")
    args = parser.parse_args()
    
    # Use config value if not provided via CLI
    cutoff_days = args.cutoff_days if args.cutoff_days is not None else default_cutoff
    
    # Load conversations
    raw_path = Path(settings.data_path) / "raw" / "conversations.json"
    with open(raw_path) as f:
        data = json.load(f)
    
    conversations = data if isinstance(data, list) else data.get("conversations", [])
    
    # Filter by recency
    cutoff = datetime.now() - timedelta(days=cutoff_days)
    
    filtered = []
    for conv in conversations:
        created = conv.get("create_time")
        if created:
            conv_date = datetime.fromtimestamp(created)
            if conv_date >= cutoff:
                filtered.append(conv)
    
    # Calculate token counts and bin conversations
    bins = {
        "0-200": [],
        "200-500": [],
        "500-1000": [],
        "1000-2000": [],
        "2000-5000": [],
        "5000-10000": [],
        "10000+": []
    }
    
    for conv in filtered:
        # Count tokens (simple word-based estimate: ~1.3 tokens per word)
        text = conv.get("title", "") + " "
        mapping = conv.get("mapping", {})
        for node_id, node in mapping.items():
            message = node.get("message")
            if message:
                content = message.get("content", {})
                if content:
                    parts = content.get("parts", [])
                    text += " ".join(str(p) for p in parts if p)
        
        # Estimate tokens (1.3 tokens per word)
        words = len(text.split())
        tokens = int(words * 1.3)
        
        # Bin it
        if tokens < 200:
            bins["0-200"].append(tokens)
        elif tokens < 500:
            bins["200-500"].append(tokens)
        elif tokens < 1000:
            bins["500-1000"].append(tokens)
        elif tokens < 2000:
            bins["1000-2000"].append(tokens)
        elif tokens < 5000:
            bins["2000-5000"].append(tokens)
        elif tokens < 10000:
            bins["5000-10000"].append(tokens)
        else:
            bins["10000+"].append(tokens)
    
    # Calculate stats
    all_tokens = [t for bin_tokens in bins.values() for t in bin_tokens]
    
    # Generate markdown report
    output = []
    output.append("# Conversation Length Distribution")
    output.append(f"\n**Recency Filter:** Last {cutoff_days} days")
    output.append(f"**Total Conversations:** {len(filtered):,}")
    output.append(f"**Total Tokens:** {sum(all_tokens):,}")
    output.append(f"**Average Tokens/Conversation:** {sum(all_tokens) // len(filtered):,}")
    
    output.append("\n## Distribution by Token Range\n")
    output.append("| Bin | Count | % | Avg Tokens | Total Tokens |")
    output.append("|-----|-------|---|------------|--------------|")
    
    for bin_name in ["0-200", "200-500", "500-1000", "1000-2000", "2000-5000", "5000-10000", "10000+"]:
        bin_tokens = bins[bin_name]
        count = len(bin_tokens)
        pct = (count / len(filtered) * 100) if count > 0 else 0
        avg = sum(bin_tokens) // count if count > 0 else 0
        total = sum(bin_tokens)
        output.append(f"| {bin_name} | {count:,} | {pct:.1f}% | {avg:,} | {total:,} |")
    
    # Write output
    output_path = Path(settings.data_path) / "CONVERSATION_LENGTH_ANALYSIS.md"
    with open(output_path, "w") as f:
        f.write("\n".join(output))
    
    print(f"✅ Analysis complete: {output_path}")
    print("\n".join(output))


if __name__ == "__main__":
    main()

