#!/usr/bin/env python3
"""
Export learnings.json to CSV format.

Extracts key fields for review and analysis.
"""

import json
import argparse
import re
from pathlib import Path
import pandas as pd


def normalize_text_for_csv(text: str) -> str:
    """Normalize text for CSV: replace newlines with literal \\n and compress doubles."""
    if not text:
        return text
    # Replace actual newlines with literal \n
    text = text.replace('\n', '\\n')
    # Compress multiple consecutive \n to single \n
    text = re.sub(r'(\\n){2,}', r'\\n', text)
    return text


def load_learnings(file_path: str):
    """Load learnings from JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['learnings']


def export_to_csv(learnings, output_path: str):
    """Export learnings to CSV with key fields."""
    
    rows = []
    for learning in learnings:
        content = normalize_text_for_csv(learning.get('content', ''))
        title = normalize_text_for_csv(learning.get('title', ''))
        rows.append({
            'learning_id': learning.get('id', 'unknown'),
            'title': title,
            'cluster_id': learning.get('cluster_id'),
            'cognition_cluster_id': learning.get('cognition_cluster_id'),
            'category': learning.get('category'),
            'confidence': learning.get('confidence'),
            'entities': '|'.join(learning.get('entities', [])),
            'keywords': '|'.join(learning.get('keywords', [])),
            'source_observation_count': learning.get('source_observation_count', 0),
            'content_preview': content[:200] + '...' if len(content) > 200 else content,
            'content': content
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    
    return df


def main():
    parser = argparse.ArgumentParser(description="Export learnings to CSV")
    parser.add_argument(
        "-i", "--input",
        default="data/learnings/learnings.json",
        help="Input learnings JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        default="data/exports/learnings.csv",
        help="Output CSV file"
    )
    args = parser.parse_args()
    
    input_file = Path(args.input)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading learnings from: {input_file}")
    learnings = load_learnings(input_file)
    print(f"  Found {len(learnings)} learnings")
    
    print(f"\nExporting to CSV: {output_file}")
    df = export_to_csv(learnings, output_file)
    
    print(f"\n✓ Exported {len(df)} rows")
    print(f"  Columns: {', '.join(df.columns)}")
    print(f"\nBreakdown by category:")
    print(df['category'].value_counts().to_string())
    print(f"\nBreakdown by confidence:")
    print(df['confidence'].value_counts().to_string())
    print(f"\nTotal observations: {df['source_observation_count'].sum()}")
    print(f"Avg observations per learning: {df['source_observation_count'].mean():.1f}")


if __name__ == "__main__":
    main()

