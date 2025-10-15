#!/usr/bin/env python3
"""
Load Rebrain cognitions and learnings into memg-core dual database.

Creates a memg-core database with cognitions and learnings, including
relationships between them.

Usage:
    python scripts/load_memg.py                           # Default paths
    python scripts/load_memg.py --output /custom/path    # Custom output
    python scripts/load_memg.py --copy-to integrations/mcp/rebrain/  # Copy to MCP
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

# Add memg_core to path (assumes memg-core is installed in venv)
try:
    from memg_core.api.public import MemgClient
except ImportError:
    print("❌ ERROR: memg-core not installed")
    print("   Install: pip install memg-core")
    sys.exit(1)


def load_json_data(cognitions_path: Path, learnings_path: Path):
    """Load cognitions and learnings from JSON files."""
    print(f"📖 Loading data...")
    print(f"   Cognitions: {cognitions_path}")
    print(f"   Learnings:  {learnings_path}")
    
    if not cognitions_path.exists():
        print(f"❌ ERROR: Cognitions file not found: {cognitions_path}")
        sys.exit(1)
    
    if not learnings_path.exists():
        print(f"❌ ERROR: Learnings file not found: {learnings_path}")
        sys.exit(1)
    
    with open(cognitions_path, 'r', encoding='utf-8') as f:
        cognitions_data = json.load(f)
    
    with open(learnings_path, 'r', encoding='utf-8') as f:
        learnings_data = json.load(f)
    
    cognitions = cognitions_data.get("cognitions", [])
    learnings = learnings_data.get("learnings", [])
    
    print(f"✅ Loaded {len(cognitions)} cognitions")
    print(f"✅ Loaded {len(learnings)} learnings")
    print()
    
    return cognitions, learnings


def validate_learnings(learnings, cognitions):
    """Filter out orphan learnings that don't map to any cognition."""
    cognition_cluster_ids = {c["cluster_id"] for c in cognitions}
    
    valid_learnings = []
    skipped_learnings = []
    
    for learning in learnings:
        cognition_cluster_id = learning.get("cognition_cluster_id", "")
        if cognition_cluster_id and cognition_cluster_id in cognition_cluster_ids:
            valid_learnings.append(learning)
        else:
            skipped_learnings.append(cognition_cluster_id or "empty")
    
    print(f"✅ Valid learnings: {len(valid_learnings)}")
    print(f"⚠️  Skipped orphans: {len(skipped_learnings)}")
    if skipped_learnings:
        from collections import Counter
        orphan_counts = Counter(skipped_learnings)
        for cluster_id, count in orphan_counts.most_common(3):
            print(f"   - {cluster_id}: {count} learnings")
    print()
    
    return valid_learnings


def initialize_database(yaml_path: Path, db_path: Path):
    """Initialize memg-core database."""
    print(f"🚀 Initializing memg-core database...")
    print(f"   YAML schema: {yaml_path}")
    print(f"   Database:    {db_path}")
    
    if not yaml_path.exists():
        print(f"❌ ERROR: YAML schema not found: {yaml_path}")
        sys.exit(1)
    
    # Create db directory
    db_path.mkdir(parents=True, exist_ok=True)
    
    try:
        client = MemgClient(
            yaml_path=str(yaml_path),
            db_path=str(db_path)
        )
        print("✅ Database initialized")
        print()
        return client
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def import_cognitions(client, cognitions, user_id: str = "rebrain"):
    """Import cognitions into database."""
    print("💾 Importing cognitions...")
    print("-" * 80)
    
    cognition_map = {}  # cluster_id → HRID
    success_count = 0
    error_count = 0
    
    for idx, cognition in enumerate(cognitions, 1):
        cluster_id = cognition.get("cluster_id", f"cognition_{idx}")
        
        try:
            # Transform to match schema
            payload = {
                "content": cognition["content"],
                "domains": " | ".join(cognition.get("domains", [])),
                "keywords": " | ".join(cognition.get("keywords", [])),
                "entities": " | ".join(cognition.get("entities", [])),
            }
            
            hrid = client.add_memory(
                memory_type="cognition",
                payload=payload,
                user_id=user_id
            )
            
            cognition_map[cluster_id] = hrid
            success_count += 1
            print(f"✅ [{idx:2d}/{len(cognitions)}] {hrid} | {cluster_id}")
            
        except Exception as e:
            error_count += 1
            print(f"❌ [{idx:2d}/{len(cognitions)}] {cluster_id}: {str(e)}")
    
    print("-" * 80)
    print(f"✅ Imported {success_count}/{len(cognitions)} cognitions")
    if error_count > 0:
        print(f"❌ Failed {error_count} cognitions")
    print()
    
    return cognition_map


def import_learnings(client, learnings, user_id: str = "rebrain"):
    """Import learnings into database."""
    print("💾 Importing learnings...")
    print("-" * 80)
    
    learning_map = {}  # cognition_cluster_id → list of learning HRIDs
    success_count = 0
    error_count = 0
    
    for idx, learning in enumerate(learnings, 1):
        cognition_cluster_id = learning.get("cognition_cluster_id", "")
        
        try:
            # Transform to match schema (NEW: keywords instead of tags, add title)
            entities = learning.get("entities", [])
            keywords = learning.get("keywords", [])  # Changed from tags
            
            payload = {
                "content": learning["content"],
                "title": learning.get("title", ""),  # NEW: title field
                "keywords": " | ".join(keywords) if keywords else "",  # Changed from tags
                "entities": " | ".join(entities) if entities else "",
                "category": learning.get("category", ""),
            }
            
            hrid = client.add_memory(
                memory_type="learning",
                payload=payload,
                user_id=user_id
            )
            
            # Track for relationship mapping
            if cognition_cluster_id not in learning_map:
                learning_map[cognition_cluster_id] = []
            learning_map[cognition_cluster_id].append(hrid)
            
            success_count += 1
            
            # Print progress every 10 items
            if idx % 10 == 0 or idx == len(learnings):
                print(f"✅ [{idx:3d}/{len(learnings)}] {hrid}")
            
        except Exception as e:
            error_count += 1
            print(f"❌ [{idx:3d}/{len(learnings)}] {str(e)}")
    
    print("-" * 80)
    print(f"✅ Imported {success_count}/{len(learnings)} learnings")
    if error_count > 0:
        print(f"❌ Failed {error_count} learnings")
    print()
    
    return learning_map


def create_relationships(client, cognition_map, learning_map, user_id: str = "rebrain"):
    """Create relationships between cognitions and learnings."""
    print("🔗 Creating relationships (Cognition → Learning)...")
    print("-" * 80)
    
    success_count = 0
    error_count = 0
    
    for cognition_cluster_id, learning_hrids in learning_map.items():
        if cognition_cluster_id not in cognition_map:
            continue
        
        cognition_hrid = cognition_map[cognition_cluster_id]
        
        for learning_hrid in learning_hrids:
            try:
                client.add_relationship(
                    from_memory_hrid=cognition_hrid,
                    to_memory_hrid=learning_hrid,
                    relation_type="SYNTHESIZED_FROM",
                    from_memory_type="cognition",
                    to_memory_type="learning",
                    user_id=user_id
                )
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"❌ {cognition_hrid} → {learning_hrid}: {str(e)}")
    
    print(f"✅ Created {success_count} relationships")
    if error_count > 0:
        print(f"❌ Failed {error_count} relationships")
    print("-" * 80)
    print()
    
    return success_count


def copy_database(source_db: Path, target_dir: Path):
    """Copy database to another location (target_dir/db/)."""
    # Target is target_dir/db/ to match docker mount structure
    target_db_dir = target_dir / "db"
    print(f"📦 Copying database to: {target_db_dir}")
    
    target_db_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear existing database at target
    qdrant_target = target_db_dir / "qdrant"
    kuzu_target = target_db_dir / "kuzu"
    
    if qdrant_target.exists():
        shutil.rmtree(qdrant_target)
        print(f"✅ Cleared: {qdrant_target}")
    
    if kuzu_target.exists():
        shutil.rmtree(kuzu_target)
        print(f"✅ Cleared: {kuzu_target}")
    
    # Copy from source
    qdrant_source = source_db / "qdrant"
    kuzu_source = source_db / "kuzu"
    
    if qdrant_source.exists():
        shutil.copytree(qdrant_source, qdrant_target)
        print(f"✅ Copied: qdrant → {qdrant_target}")
    
    if kuzu_source.exists():
        shutil.copytree(kuzu_source, kuzu_target)
        print(f"✅ Copied: kuzu → {kuzu_target}")
    
    print()


def main():
    """Main import process."""
    parser = argparse.ArgumentParser(
        description="Load Rebrain cognitions and learnings into memg-core database"
    )
    parser.add_argument(
        "--cognitions",
        default="data/cognitions/cognitions.json",
        help="Path to cognitions JSON file (default: data/cognitions/cognitions.json)"
    )
    parser.add_argument(
        "--learnings",
        default="data/learnings/learnings.json",
        help="Path to learnings JSON file (default: data/learnings/learnings.json)"
    )
    parser.add_argument(
        "--yaml",
        default="integrations/mcp/rebrain/rebrain.yaml",
        help="Path to memg-core YAML schema (default: integrations/mcp/rebrain/rebrain.yaml)"
    )
    parser.add_argument(
        "--output",
        default="data/memg_core",
        help="Output database directory (default: data/memg_core)"
    )
    parser.add_argument(
        "--copy-to",
        help="Optional: Copy database to this location (e.g., integrations/mcp/rebrain/)"
    )
    parser.add_argument(
        "--user-id",
        default="rebrain",
        help="User ID for memg-core (default: rebrain)"
    )
    
    args = parser.parse_args()
    
    # Convert to Path objects
    cognitions_path = Path(args.cognitions)
    learnings_path = Path(args.learnings)
    yaml_path = Path(args.yaml)
    output_path = Path(args.output)
    
    print("=" * 80)
    print("MEMG-CORE DATABASE LOADER")
    print("=" * 80)
    print()
    
    # Load data
    cognitions, learnings = load_json_data(cognitions_path, learnings_path)
    
    # Validate learnings
    valid_learnings = validate_learnings(learnings, cognitions)
    
    # Initialize database
    client = initialize_database(yaml_path, output_path)
    
    try:
        # Import cognitions
        cognition_map = import_cognitions(client, cognitions, args.user_id)
        
        # Import learnings
        learning_map = import_learnings(client, valid_learnings, args.user_id)
        
        # Create relationships
        relationship_count = create_relationships(client, cognition_map, learning_map, args.user_id)
        
        # Summary
        print("=" * 80)
        print("IMPORT SUMMARY")
        print("=" * 80)
        print(f"✅ Cognitions imported:    {len(cognition_map)}/{len(cognitions)}")
        print(f"✅ Learnings imported:     {len([l for ls in learning_map.values() for l in ls])}/{len(valid_learnings)}")
        print(f"✅ Relationships created:  {relationship_count}")
        print()
        print(f"📊 Total memories:         {len(cognition_map) + len([l for ls in learning_map.values() for l in ls])}")
        print(f"📊 Total relationships:    {relationship_count}")
        print(f"⚠️  Skipped orphans:       {len(learnings) - len(valid_learnings)}")
        print()
        print(f"📁 Database location:      {output_path}")
        print(f"👤 User ID:                {args.user_id}")
        print()
        
        # Copy to MCP location if requested
        if args.copy_to:
            copy_to_path = Path(args.copy_to)
            copy_database(output_path, copy_to_path)
        
        print("🎉 All data imported successfully!")
        print("=" * 80)
    
    finally:
        # Always close the client to prevent file locks
        print("🔒 Closing database connection...")
        client.close()
        print("✅ Connection closed")


if __name__ == "__main__":
    main()

