#!/usr/bin/env python3
"""
Export cognitions.json to CSV format.

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


def load_cognitions(file_path: str):
    """Load cognitions from JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['cognitions']


def export_to_csv(cognitions, output_path: str):
    """Export cognitions to CSV with key fields."""
    
    rows = []
    for idx, cog in enumerate(cognitions):
        content = normalize_text_for_csv(cog.get('content', ''))
        rows.append({
            'cognition_id': f"cognition_{idx:03d}",
            'cluster_id': cog.get('cluster_id'),
            'priority': cog.get('priority'),
            'stability': cog.get('stability'),
            'domains': '|'.join(cog.get('domains', [])),
            'entities': '|'.join(cog.get('entities', [])),
            'keywords': '|'.join(cog.get('keywords', [])),
            'source_learning_count': cog.get('source_learning_count', len(cog.get('source_learning_ids', []))),
            'content_preview': content[:200] + '...' if len(content) > 200 else content,
            'content': content
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    
    return df


def main():
    parser = argparse.ArgumentParser(description="Export cognitions to CSV")
    parser.add_argument(
        "-i", "--input",
        default="data/cognitions/cognitions.json",
        help="Input cognitions JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        default="data/exports/cognitions.csv",
        help="Output CSV file"
    )
    args = parser.parse_args()
    
    input_file = Path(args.input)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading cognitions from: {input_file}")
    cognitions = load_cognitions(input_file)
    print(f"  Found {len(cognitions)} cognitions")
    
    print(f"\nExporting to CSV: {output_file}")
    df = export_to_csv(cognitions, output_file)
    
    print(f"\n✓ Exported {len(df)} rows")
    print(f"  Columns: {', '.join(df.columns)}")
    print(f"\nBreakdown by priority:")
    print(df['priority'].value_counts().to_string())


if __name__ == "__main__":
    main()

