"""
Minimal Result Cleaner for Rebrain MCP
Cleans and formats memory search results to markdown for token efficiency.

Schema (available in payload):
- Learning: content, title, keywords, entities, category
- Cognition: content, keywords, entities, domains, source_learning_count

Note: Currently displays content only. Title field available but not shown yet.
"""

from typing import Any, Dict, List


def clean_and_format(
    raw_result: Dict[str, Any],
    neighbor_limit: int = 3
) -> str:
    """
    Clean raw memg-core results and convert to markdown.
    
    Args:
        raw_result: Raw result from memg-core API (search, get_memory, list_memories)
        neighbor_limit: Max neighbors per seed (default: 3, enforced per-seed with score sorting)
    
    Returns:
        Formatted markdown string
    """
    # Extract data
    query = raw_result.get("query", "")
    memories = raw_result.get("memories", [])
    neighbors_raw = raw_result.get("neighbors", [])
    
    # Track needed neighbor HRIDs after per-seed limiting
    needed_neighbor_hrids = set()
    cleaned_seeds = []
    
    # Process seeds and apply per-seed neighbor limiting
    for mem in memories:
        seed = {
            "hrid": mem.get("hrid", "N/A"),
            "updated": _extract_date(mem.get("updated_at", "")),
            "score": round(mem.get("score", 0), 2),
            "content": mem.get("payload", {}).get("content", ""),
            "relationships": []
        }
        
        # Add source_learning_count for cognitions
        payload = mem.get("payload", {})
        if "source_learning_count" in payload:
            seed["source_learning_count"] = payload["source_learning_count"]
        
        # Sort and limit relationships by score per seed
        relationships = mem.get("relationships", [])
        if relationships:
            # Sort by score descending
            sorted_rels = sorted(
                relationships,
                key=lambda r: r.get("score", 0),
                reverse=True
            )[:neighbor_limit]
            
            # Clean and collect
            for rel in sorted_rels:
                target = rel.get("target_hrid", "")
                needed_neighbor_hrids.add(target)
                seed["relationships"].append({
                    "target": target,
                    "score": round(rel.get("score", 0), 2)
                })
        
        cleaned_seeds.append(seed)
    
    # Get only needed neighbors
    neighbor_map = {n["hrid"]: n for n in neighbors_raw}
    needed_neighbors = []
    for hrid in needed_neighbor_hrids:
        if hrid in neighbor_map:
            n = neighbor_map[hrid]
            needed_neighbors.append({
                "hrid": hrid,
                "content": n.get("payload", {}).get("content", "")
            })
    
    # Sort neighbors by score if available
    needed_neighbors.sort(
        key=lambda n: neighbor_map.get(n["hrid"], {}).get("score", 0),
        reverse=True
    )
    
    # Format to markdown
    return _format_markdown(
        query=query,
        seeds=cleaned_seeds,
        neighbors=needed_neighbors,
        total_seeds=len(memories),
        total_neighbors_raw=len(neighbors_raw),
        neighbors_returned=len(needed_neighbors)
    )


def _extract_date(datetime_str: str) -> str:
    """Extract date only from datetime string."""
    if not datetime_str:
        return ""
    return datetime_str.split()[0] if " " in datetime_str else datetime_str


def _format_markdown(
    query: str,
    seeds: List[Dict[str, Any]],
    neighbors: List[Dict[str, Any]],
    total_seeds: int,
    total_neighbors_raw: int,
    neighbors_returned: int
) -> str:
    """Format cleaned data to markdown."""
    lines = []
    
    # Header
    if query:
        lines.append(f"# Query: {query}")
    else:
        lines.append("# Memory Results")
    lines.append("")
    
    # Summary
    lines.append("**Results:**")
    lines.append(f"- Seeds: {total_seeds}")
    lines.append(f"- Neighbors: {neighbors_returned} / {total_neighbors_raw}")
    
    # Latest update
    if seeds:
        updates = [s["updated"] for s in seeds if s.get("updated")]
        if updates:
            lines.append(f"- Updated: {max(updates)}")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Seeds
    for i, seed in enumerate(seeds):
        # Title with score
        lines.append(f"## {i+1}. {seed['hrid']} · score {seed['score']}")
        lines.append("")
        
        # Content
        lines.append(seed["content"])
        lines.append("")
        
        # Source learning count (for cognitions)
        if "source_learning_count" in seed:
            lines.append(f"*Synthesized from {seed['source_learning_count']} learnings*")
            lines.append("")
        
        # Relationships
        if seed.get("relationships"):
            refs = [f"`{r['target']}`" for r in seed["relationships"]]
            lines.append(f"**→** {', '.join(refs)}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # Neighbors
    if neighbors:
        lines.append("## Neighbors")
        lines.append("")
        
        for neighbor in neighbors:
            lines.append(f"### {neighbor['hrid']}")
            lines.append("")
            lines.append(neighbor["content"])
            lines.append("")
    
    return "\n".join(lines)

