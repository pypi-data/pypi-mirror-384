#!/usr/bin/env python3
"""
Analyze token distribution across the memory hierarchy.

Shows token counts for each cognition and its full lineage (learnings → insights).
Helps determine optimal layers for GraphRAG and traversal patterns.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import tiktoken

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def load_data():
    """Load all hierarchy data."""
    base_path = Path("data")
    
    with open(base_path / "cognitions/cognitions.json") as f:
        cognitions_data = json.load(f)
    
    with open(base_path / "learnings/learnings.json") as f:
        learnings_data = json.load(f)
    
    with open(base_path / "observations/observations.json") as f:
        observations_data = json.load(f)
    
    return cognitions_data, learnings_data, observations_data


def analyze_hierarchy(cognitions_data, learnings_data, observations_data):
    """Analyze token distribution across hierarchy."""
    
    # Index by cluster_id since 'id' field doesn't exist
    # Group learnings by their cognition_cluster_id
    learnings_by_cluster = {}
    for l in learnings_data['learnings']:
        cluster_id = l.get('cognition_cluster_id')
        if cluster_id is not None:
            if cluster_id not in learnings_by_cluster:
                learnings_by_cluster[cluster_id] = []
            learnings_by_cluster[cluster_id].append(l)
    
    # Index observations by cluster_id for learnings
    observations_by_cluster = {}
    for o in observations_data['observations']:
        cluster_id = o.get('cluster_id')
        if cluster_id is not None:
            if cluster_id not in observations_by_cluster:
                observations_by_cluster[cluster_id] = []
            observations_by_cluster[cluster_id].append(o)
    
    results = []
    
    for idx, cog in enumerate(cognitions_data['cognitions']):
        cog_cluster_id = cog.get('cluster_id')
        cog_tokens = count_tokens(cog['content'])
        
        # Get child learnings for this cognition's cluster
        learnings = learnings_by_cluster.get(cog_cluster_id, [])
        
        learning_tokens = []
        all_learning_cluster_ids = []
        
        for learning in learnings:
            l_tokens = count_tokens(learning['content'])
            learning_tokens.append(l_tokens)
            # Track which observation clusters fed into this learning
            learning_cluster_id = learning.get('cluster_id')
            if learning_cluster_id is not None:
                all_learning_cluster_ids.append(learning_cluster_id)
        
        # Get child observations from learning clusters
        observations = []
        for l_cluster_id in all_learning_cluster_ids:
            observations.extend(observations_by_cluster.get(l_cluster_id, []))
        
        observation_tokens = [count_tokens(o['content']) for o in observations]
        
        # Calculate totals and averages
        total_learning_tokens = sum(learning_tokens)
        total_observation_tokens = sum(observation_tokens)
        total_tokens = cog_tokens + total_learning_tokens + total_observation_tokens
        
        learning_avg = round(total_learning_tokens / len(learnings)) if learnings else 0
        observation_avg = round(total_observation_tokens / len(observations)) if observations else 0
        
        results.append({
            'cognition_id': f"cognition_{idx:03d}",
            'cluster_id': cog_cluster_id,
            'priority': cog.get('priority', 'unknown'),
            'domains': cog.get('domains', []),
            'cognition_tokens': cog_tokens,
            'learning_count': len(learnings),
            'observation_count': len(observations),
            'learning_avg_token': learning_avg,
            'observation_avg_token': observation_avg,
            'learning_total_token': total_learning_tokens,
            'observation_total_token': total_observation_tokens,
            'total_hierarchy_tokens': total_tokens,
            'expansion_ratio': round(total_tokens / cog_tokens, 2) if cog_tokens > 0 else 0,
            # Keep these for terminal output
            'learning_tokens': learning_tokens,
            'observation_tokens': observation_tokens,
        })
    
    return results


def print_summary(results):
    """Print summary statistics."""
    
    print("\n" + "="*80)
    print("TOKEN HIERARCHY ANALYSIS")
    print("="*80)
    
    # Overall stats
    total_cognitions = len(results)
    avg_cog_tokens = sum(r['cognition_tokens'] for r in results) / total_cognitions
    avg_learning_tokens = sum(r['learning_total_token'] for r in results) / total_cognitions
    avg_observation_tokens = sum(r['observation_total_token'] for r in results) / total_cognitions
    avg_total = sum(r['total_hierarchy_tokens'] for r in results) / total_cognitions
    avg_expansion = sum(r['expansion_ratio'] for r in results) / total_cognitions
    
    print(f"\nOVERALL STATISTICS ({total_cognitions} cognitions)")
    print("-" * 80)
    print(f"Average per cognition:")
    print(f"  Cognition:       {avg_cog_tokens:>8.0f} tokens")
    print(f"  + Learnings:     {avg_learning_tokens:>8.0f} tokens")
    print(f"  + Observations:  {avg_observation_tokens:>8.0f} tokens")
    print(f"  = Total:         {avg_total:>8.0f} tokens")
    print(f"  Expansion ratio: {avg_expansion:>8.2f}x")
    
    # By priority
    print(f"\nBY PRIORITY")
    print("-" * 80)
    by_priority = defaultdict(list)
    for r in results:
        by_priority[r['priority']].append(r)
    
    for priority in ['core', 'important', 'peripheral']:
        if priority in by_priority:
            items = by_priority[priority]
            avg_tokens = sum(i['total_hierarchy_tokens'] for i in items) / len(items)
            avg_exp = sum(i['expansion_ratio'] for i in items) / len(items)
            print(f"  {priority:12s}: {len(items):3d} cognitions, avg {avg_tokens:>8.0f} tokens ({avg_exp:.2f}x expansion)")
    
    # Distribution
    print(f"\nTOKEN DISTRIBUTION")
    print("-" * 80)
    total_all_cog = sum(r['cognition_tokens'] for r in results)
    total_all_learn = sum(r['learning_total_token'] for r in results)
    total_all_observation = sum(r['observation_total_token'] for r in results)
    total_all = total_all_cog + total_all_learn + total_all_observation
    
    print(f"  Cognitions:   {total_all_cog:>10,} tokens ({100*total_all_cog/total_all:>5.1f}%)")
    print(f"  Learnings:    {total_all_learn:>10,} tokens ({100*total_all_learn/total_all:>5.1f}%)")
    print(f"  Observations: {total_all_observation:>10,} tokens ({100*total_all_observation/total_all:>5.1f}%)")
    print(f"  Total:        {total_all:>10,} tokens")


def print_details(results, top_n: int = 10):
    """Print detailed breakdown for top N cognitions by total tokens."""
    
    print(f"\nTOP {top_n} COGNITIONS BY HIERARCHY SIZE")
    print("="*80)
    
    sorted_results = sorted(results, key=lambda x: x['total_hierarchy_tokens'], reverse=True)[:top_n]
    
    for i, r in enumerate(sorted_results, 1):
        domains_str = ', '.join(r['domains'])
        print(f"\n{i}. {r['cognition_id']} ({r['priority']}) [{domains_str}]")
        print(f"   Cognition:    {r['cognition_tokens']:>6,} tokens")
        print(f"   Learnings:    {r['learning_count']:>2d} learnings    × {r['learning_total_token']:>6,} tokens (avg: {r['learning_avg_token']:>4,})")
        print(f"   Observations: {r['observation_count']:>2d} observations × {r['observation_total_token']:>6,} tokens (avg: {r['observation_avg_token']:>4,})")
        print(f"   Total:        {r['total_hierarchy_tokens']:>6,} tokens ({r['expansion_ratio']:.1f}x expansion)")


def print_recommendations(results):
    """Print GraphRAG recommendations."""
    
    print("\n" + "="*80)
    print("GRAPHRAG RECOMMENDATIONS")
    print("="*80)
    
    avg_cog = sum(r['cognition_tokens'] for r in results) / len(results)
    avg_with_learning = sum(r['cognition_tokens'] + r['learning_total_token'] for r in results) / len(results)
    avg_full = sum(r['total_hierarchy_tokens'] for r in results) / len(results)
    
    print("\nLAYER STRATEGIES:")
    print("-" * 80)
    print(f"1. COGNITION ONLY")
    print(f"   - Avg context: ~{avg_cog:.0f} tokens per cognition")
    print(f"   - Best for: High-level concept search, initial retrieval")
    print(f"   - Context window: 5-10 cognitions = ~{avg_cog*5:.0f}-{avg_cog*10:.0f} tokens")
    
    print(f"\n2. COGNITION + LEARNINGS")
    print(f"   - Avg context: ~{avg_with_learning:.0f} tokens per cognition")
    print(f"   - Best for: Understanding reasoning patterns, mid-depth queries")
    print(f"   - Context window: 3-5 cognitions = ~{avg_with_learning*3:.0f}-{avg_with_learning*5:.0f} tokens")
    
    print(f"\n3. FULL HIERARCHY (Cognition + Learnings + Observations)")
    print(f"   - Avg context: ~{avg_full:.0f} tokens per cognition")
    print(f"   - Best for: Deep context, evidence retrieval, fact-checking")
    print(f"   - Context window: 1-2 cognitions = ~{avg_full:.0f}-{avg_full*2:.0f} tokens")
    
    print("\nTRAVERSAL PATTERNS:")
    print("-" * 80)
    print("• Abstract query → Search cognitions → Expand to learnings if needed")
    print("• Specific query → Search learnings directly → Expand to observations for evidence")
    print("• Fact-finding → Search observations directly → Trace up to cognition for context")
    print("• Hybrid → Search all layers, rank by relevance, expand top matches")


def export_csv(results, output_path: str = "data/analysis/token_hierarchy.csv"):
    """Export results to CSV using pandas."""
    import pandas as pd
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Select only the fields we want
    rows = [{
        'cognition_id': r['cognition_id'],
        'cluster_id': r['cluster_id'],
        'priority': r['priority'],
        'domains': '|'.join(r['domains']),
        'cognition_tokens': r['cognition_tokens'],
        'learning_count': r['learning_count'],
        'observation_count': r['observation_count'],
        'learning_avg_token': r['learning_avg_token'],
        'observation_avg_token': r['observation_avg_token'],
        'learning_total_token': r['learning_total_token'],
        'observation_total_token': r['observation_total_token']
    } for r in results]
    
    pd.DataFrame(rows).to_csv(output_file, index=False)
    print(f"\n✓ Exported to: {output_file}")


def main():
    """Main entry point."""
    print("\nLoading data...")
    cognitions_data, learnings_data, observations_data = load_data()
    
    print("Analyzing hierarchy...")
    results = analyze_hierarchy(cognitions_data, learnings_data, observations_data)
    
    print_summary(results)
    print_details(results, top_n=10)
    print_recommendations(results)
    
    export_csv(results)
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

