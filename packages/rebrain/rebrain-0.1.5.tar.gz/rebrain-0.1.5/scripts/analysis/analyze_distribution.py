#!/usr/bin/env python3
"""
Analyze conversation size distribution for ingestion planning.

Shows how conversations are distributed by token count to help determine
optimal ingestion strategies (single API call vs chunking, etc.)
"""

import json
import sys
from pathlib import Path
from collections import Counter

import pandas as pd


def analyze_distribution(json_file):
    """Analyze conversation token distribution."""
    
    print(f"📊 Analyzing: {json_file.name}\n")
    
    with open(json_file) as f:
        data = json.load(f)
    
    # Extract conversations (works for both nested and flat formats)
    if "conversations" in data:
        conversations = data["conversations"]
        # For flat format, conversations are metadata objects
        if conversations and "metrics" in conversations[0]:
            conv_data = [
                {
                    "id": c["id"],
                    "title": c["title"],
                    "message_count": c["message_count"],
                    "total_tokens": c["metrics"]["total_tokens"],
                    "user_tokens": c["metrics"]["user_tokens"],
                    "assistant_tokens": c["metrics"]["assistant_tokens"],
                    "avg_tokens": c["metrics"]["avg_tokens_per_message"],
                    "max_tokens": c["metrics"]["max_tokens_per_message"],
                }
                for c in conversations
            ]
        else:
            # Nested format
            conv_data = [
                {
                    "id": c["id"],
                    "title": c["title"],
                    "message_count": c["message_count"],
                    "total_tokens": c["metrics"]["total_tokens"],
                    "user_tokens": c["metrics"]["user_tokens"],
                    "assistant_tokens": c["metrics"]["assistant_tokens"],
                    "avg_tokens": c["metrics"]["avg_tokens_per_message"],
                    "max_tokens": c["metrics"]["max_tokens_per_message"],
                }
                for c in conversations
            ]
    else:
        print("Error: Unknown JSON format")
        return
    
    df = pd.DataFrame(conv_data)
    
    # Define size buckets
    def categorize_size(tokens):
        if tokens < 500:
            return "Tiny (<500)"
        elif tokens < 2000:
            return "Small (500-2K)"
        elif tokens < 5000:
            return "Medium (2K-5K)"
        elif tokens < 10000:
            return "Large (5K-10K)"
        elif tokens < 50000:
            return "Very Large (10K-50K)"
        elif tokens < 100000:
            return "Huge (50K-100K)"
        else:
            return "Massive (>100K)"
    
    df["size_category"] = df["total_tokens"].apply(categorize_size)
    
    # Overall statistics
    print("=" * 70)
    print("OVERALL STATISTICS")
    print("=" * 70)
    print(f"Total conversations: {len(df):,}")
    print(f"Total messages: {df['message_count'].sum():,}")
    print(f"Total tokens: {df['total_tokens'].sum():,}")
    print(f"\nToken distribution:")
    print(f"  Mean:   {df['total_tokens'].mean():,.0f} tokens")
    print(f"  Median: {df['total_tokens'].median():,.0f} tokens")
    print(f"  Min:    {df['total_tokens'].min():,} tokens")
    print(f"  Max:    {df['total_tokens'].max():,} tokens")
    print(f"  Std:    {df['total_tokens'].std():,.0f} tokens")
    
    # Percentiles
    print(f"\nPercentiles:")
    for p in [25, 50, 75, 90, 95, 99]:
        val = df['total_tokens'].quantile(p / 100)
        print(f"  {p}th: {val:,.0f} tokens")
    
    # Size distribution
    print(f"\n{'=' * 70}")
    print("SIZE DISTRIBUTION")
    print("=" * 70)
    
    size_counts = df['size_category'].value_counts().sort_index()
    size_order = [
        "Tiny (<500)",
        "Small (500-2K)",
        "Medium (2K-5K)",
        "Large (5K-10K)",
        "Very Large (10K-50K)",
        "Huge (50K-100K)",
        "Massive (>100K)"
    ]
    
    total = len(df)
    print(f"\n{'Category':<25} {'Count':>8} {'Percent':>10} {'Cumulative':>12}")
    print("-" * 70)
    
    cumulative = 0
    for category in size_order:
        if category in size_counts.index:
            count = size_counts[category]
            percent = (count / total) * 100
            cumulative += percent
            print(f"{category:<25} {count:>8,} {percent:>9.1f}% {cumulative:>11.1f}%")
    
    # Token distribution by category
    print(f"\n{'=' * 70}")
    print("TOKENS BY CATEGORY")
    print("=" * 70)
    print(f"\n{'Category':<25} {'Total Tokens':>15} {'Avg Tokens':>12} {'% of Total':>12}")
    print("-" * 70)
    
    total_tokens = df['total_tokens'].sum()
    for category in size_order:
        if category in size_counts.index:
            subset = df[df['size_category'] == category]
            cat_tokens = subset['total_tokens'].sum()
            avg_tokens = subset['total_tokens'].mean()
            percent = (cat_tokens / total_tokens) * 100
            print(f"{category:<25} {cat_tokens:>15,} {avg_tokens:>12,.0f} {percent:>11.1f}%")
    
    # Ingestion strategy recommendations
    print(f"\n{'=' * 70}")
    print("INGESTION STRATEGY ANALYSIS")
    print("=" * 70)
    
    # Common context window sizes
    context_windows = {
        "GPT-3.5-turbo (4K)": 4000,
        "GPT-3.5-turbo-16K": 16000,
        "GPT-4 (8K)": 8000,
        "GPT-4-32K": 32000,
        "GPT-4-turbo (128K)": 128000,
        "Claude 3 (200K)": 200000,
    }
    
    print("\nConversations that fit in different context windows:")
    print(f"{'Model':<25} {'Fit Count':>12} {'Percent':>10} {'Need Chunking':>15}")
    print("-" * 70)
    
    for model, window in context_windows.items():
        fits = (df['total_tokens'] <= window).sum()
        percent = (fits / total) * 100
        needs_chunking = total - fits
        print(f"{model:<25} {fits:>12,} {percent:>9.1f}% {needs_chunking:>14,}")
    
    # User-defined thresholds
    print(f"\n{'=' * 70}")
    print("CUSTOM THRESHOLD ANALYSIS")
    print("=" * 70)
    
    thresholds = [2000, 5000, 10000, 20000, 50000, 100000]
    print(f"\n{'Threshold':>12} {'Below':>10} {'Above':>10} {'% Below':>10} {'% Above':>10}")
    print("-" * 70)
    
    for threshold in thresholds:
        below = (df['total_tokens'] <= threshold).sum()
        above = (df['total_tokens'] > threshold).sum()
        pct_below = (below / total) * 100
        pct_above = (above / total) * 100
        print(f"{threshold:>12,} {below:>10,} {above:>10,} {pct_below:>9.1f}% {pct_above:>9.1f}%")
    
    # Top 10 largest conversations
    print(f"\n{'=' * 70}")
    print("TOP 10 LARGEST CONVERSATIONS")
    print("=" * 70)
    print(f"\n{'Title':<50} {'Messages':>10} {'Tokens':>12}")
    print("-" * 70)
    
    top_10 = df.nlargest(10, 'total_tokens')
    for _, row in top_10.iterrows():
        title = row['title'][:47] + "..." if len(row['title']) > 50 else row['title']
        print(f"{title:<50} {row['message_count']:>10,} {row['total_tokens']:>12,}")
    
    # Recommendations
    print(f"\n{'=' * 70}")
    print("💡 RECOMMENDATIONS")
    print("=" * 70)
    
    tiny_small = (df['total_tokens'] <= 2000).sum()
    medium = ((df['total_tokens'] > 2000) & (df['total_tokens'] <= 10000)).sum()
    large = (df['total_tokens'] > 10000).sum()
    
    pct_tiny_small = (tiny_small / total) * 100
    pct_medium = (medium / total) * 100
    pct_large = (large / total) * 100
    
    print(f"""
1. **Single API Call Strategy (≤2K tokens)**
   - Conversations: {tiny_small:,} ({pct_tiny_small:.1f}%)
   - Strategy: Process entire conversation in one call
   - Models: Any model with 4K+ context window
   - Cost: Low per conversation

2. **Medium Conversations (2K-10K tokens)**
   - Conversations: {medium:,} ({pct_medium:.1f}%)
   - Strategy: Single call with larger context model
   - Models: GPT-4-turbo, Claude 3, GPT-3.5-turbo-16K
   - Cost: Moderate per conversation

3. **Large Conversations (>10K tokens)**
   - Conversations: {large:,} ({pct_large:.1f}%)
   - Strategy: Chunking or summarization required
   - Options:
     a) Chunk into overlapping segments
     b) Hierarchical summarization
     c) Use 128K+ context models (GPT-4-turbo, Claude)
   - Cost: High per conversation

4. **Recommended Approach**:
   - Use GPT-4-turbo (128K) or Claude 3 (200K) for {(df['total_tokens'] <= 100000).sum():,} conversations ({(df['total_tokens'] <= 100000).sum()/total*100:.1f}%)
   - Only {(df['total_tokens'] > 100000).sum():,} conversations ({(df['total_tokens'] > 100000).sum()/total*100:.1f}%) need special handling
""")
    
    return df


def main():
    """Run analysis on exported JSON files."""
    
    # Check for nested format first, fall back to flat
    nested_file = Path("data/exports/conversations_nested.json")
    flat_file = Path("data/exports/conversations_flat.json")
    
    if nested_file.exists():
        df = analyze_distribution(nested_file)
    elif flat_file.exists():
        df = analyze_distribution(flat_file)
    else:
        print("Error: No JSON export files found.")
        print("Please run: python scripts/convert_to_json.py")
        sys.exit(1)
    
    # Optional: Save detailed stats to CSV
    output_csv = Path("data/exports/conversation_stats.csv")
    df.to_csv(output_csv, index=False)
    print(f"\n📄 Detailed stats saved to: {output_csv}")


if __name__ == "__main__":
    main()

