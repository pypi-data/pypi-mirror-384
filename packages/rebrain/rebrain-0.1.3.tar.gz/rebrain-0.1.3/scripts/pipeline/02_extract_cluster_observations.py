#!/usr/bin/env python3
"""
Step 2: Extract & Cluster Observations

Consolidated: Extract observations → Filter privacy → Embed → Cluster

Input: data/preprocessed/conversations_clean.json
Output: data/observations/observations.json

Modes:
  --full (default): Extract + filter + embed + cluster
  --cluster-only:   Load existing observations and re-cluster
  --skip-cluster:   Extract + filter only (for review before clustering)
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.loader import load_config
from rebrain.operations import GenericSynthesizer, Embedder, Clusterer, PrivacyFilter
from rebrain.schemas.observation import ObservationExtraction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Suppress verbose HTTP logs from google-genai
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('google.auth').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)


async def main_async(args):
    """Extract and cluster observations."""
    start_time = datetime.now()
    
    # Load configuration
    try:
        secrets, config = load_config(config_path=args.config)
        # Use CLI data-path if provided, otherwise use config
        if args.data_path:
            data_path = Path(args.data_path)
        else:
            data_path = Path(config.paths.data_dir)
        extract_cfg = config.observation_extraction
        embed_cfg = config.observation_embedding
        cluster_cfg = config.observation_clustering
        exclusions_cfg = config.observation_exclusions
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1
    
    # Paths (fixed relative to data_path)
    input_file = data_path / "preprocessed/conversations_clean.json"
    output_file = data_path / "observations/observations.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine mode
    cluster_only = args.cluster_only
    skip_cluster = args.skip_cluster
    
    logger.info("=" * 70)
    mode_str = "CLUSTER ONLY" if cluster_only else ("EXTRACT ONLY" if skip_cluster else "FULL")
    logger.info(f"STEP 2: EXTRACT & CLUSTER OBSERVATIONS ({mode_str})")
    logger.info("=" * 70)
    
    # ========================================================================
    # CLUSTER-ONLY MODE: Load existing observations and re-cluster
    # ========================================================================
    if cluster_only:
        logger.info("[CLUSTER-ONLY] Loading existing observations...")
        try:
            with open(output_file) as f:
                data = json.load(f)
            observations_filtered = data["observations"]
            embeddings_array = np.array(data["embeddings"])
            logger.info(f"Loaded {len(observations_filtered):,} observations with embeddings")
        except Exception as e:
            logger.error(f"Failed to load existing observations: {e}")
            return 1
    
    # ========================================================================
    # NORMAL MODE: Extract and filter observations
    # ========================================================================
    else:
        # 2.1: Load conversations
        logger.info(f"[2.1] Loading conversations: {input_file}")
        try:
            with open(input_file) as f:
                data = json.load(f)
            conversations = data["conversations"]
            logger.info(f"Loaded {len(conversations):,} conversations")
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")
            return 1
        
        # 2.2: Extract observations (AI processing)
        logger.info(f"[2.2] Extracting observations (model={secrets.gemini_model}, prompt={extract_cfg.prompt_template}, concurrent={extract_cfg.max_concurrent})...")
        logger.info(f"Processing {len(conversations)} conversations (this may take several minutes)...")
        
        # Check if we have conversations to process
        if len(conversations) == 0:
            logger.warning("=" * 70)
            logger.warning("⚠️  NO CONVERSATIONS TO PROCESS")
            logger.warning("=" * 70)
            logger.warning("All conversations were filtered out. Possible reasons:")
            logger.warning(f"  - date_cutoff_days too restrictive (current: {config.ingestion.date_cutoff_days} days)")
            logger.warning("  - Input file has no valid conversations")
            logger.warning("  - All conversations skipped due to missing messages")
            logger.warning("")
            logger.warning("💡 To fix:")
            logger.warning("  - Increase date_cutoff_days in config/pipeline.yaml")
            logger.warning("  - Check your input file has valid conversations")
            logger.warning("=" * 70)
            return 1
        
        try:
            synthesizer = GenericSynthesizer(prompt_template=extract_cfg.prompt_template)
            
            extractions = await synthesizer.synthesize_batch_async(
                inputs=conversations,
                output_schema=ObservationExtraction,
                max_concurrent=extract_cfg.max_concurrent,
                request_delay=extract_cfg.request_delay,
                verbose=True  # Show summary
            )
            
            # Filter out None and extract observations with unique IDs
            observations_raw = []
            for idx, extraction in enumerate(extractions):
                if extraction and extraction.observation:
                    observation_dict = extraction.observation.model_dump()
                    # Generate unique ID
                    observation_dict['id'] = f"observation_{idx:05d}"
                    observations_raw.append(observation_dict)
            
            logger.info(f"Extracted: {len(observations_raw)}/{len(conversations)} observations ({len(observations_raw)/len(conversations)*100:.1f}% success)")
            
            # Category breakdown
            categories = Counter(i['category'] for i in observations_raw)
            logger.info(f"Categories: {dict(categories)}")
            
        except Exception as e:
            logger.error(f"Observation extraction failed: {e}")
            return 1
        
        # 2.3a: Save ALL observations (unfiltered) for eyeballing/analysis
        observations_raw_file = output_file.parent / "observations_raw.json"
        logger.info(f"[2.3a] Saving all observations (unfiltered): {observations_raw_file}")
        
        try:
            raw_data = {
                "export_date": datetime.now().isoformat(),
                "total_observations": len(observations_raw),
                "observations": observations_raw
            }
            with open(observations_raw_file, 'w') as f:
                json.dump(raw_data, f, indent=2, default=str)
            logger.info(f"Saved: {len(observations_raw)} observations (unfiltered)")
        except Exception as e:
            logger.error(f"Failed to save raw observations: {e}")
            return 1
        
        # 2.3b: Filter by category-specific privacy rules
        logger.info(f"[2.3b] Applying category-specific privacy filtering...")
        
        try:
            exclusion_rules = {
                "technical": exclusions_cfg.technical.privacy_levels,
                "professional": exclusions_cfg.professional.privacy_levels,
                "personal": exclusions_cfg.personal.privacy_levels
            }
            logger.info(f"Exclusion rules: {exclusion_rules}")
            
            observations_filtered = PrivacyFilter.filter_by_category_and_privacy(
                items=observations_raw,
                exclusion_rules=exclusion_rules
            )
            
            filtered_count = len(observations_raw) - len(observations_filtered)
            logger.info(f"Filtered: {filtered_count} observations")
            logger.info(f"Remaining: {len(observations_filtered)} for embedding")
            
        except Exception as e:
            logger.error(f"Privacy filtering failed: {e}")
            return 1
        
        # 2.4: Embed filtered observations and save as embeddings.json
        logger.info(f"[2.4] Embedding filtered observations (model={secrets.gemini_embedding_model}, batch={embed_cfg.batch_size}, dim={secrets.gemini_embedding_dimension})...")
        
        try:
            embedder = Embedder()
            
            # Prepare texts (title + content)
            texts = [f"{i['title']}\n{i['content']}" for i in observations_filtered]
            
            embeddings_array = embedder.embed_texts(
                texts=texts,
                show_progress=True,
                retry_on_failure=True
            )
            
            logger.info(f"Embedded: {embeddings_array.shape[0]} observations ({embeddings_array.shape[1]}d)")
            
            # Save embeddings.json (filtered observations with embeddings)
            embeddings_file = output_file.parent / "embeddings.json"
            
            embeddings_data = []
            for i, obs in enumerate(observations_filtered):
                embeddings_data.append({
                    "id": obs['id'],
                    "category": obs['category'],
                    "embedding": embeddings_array[i].tolist()
                })
            
            with open(embeddings_file, 'w') as f:
                json.dump({
                    "export_date": datetime.now().isoformat(),
                    "model": secrets.gemini_embedding_model,
                    "dimension": secrets.gemini_embedding_dimension,
                    "total_embeddings": len(embeddings_data),
                    "exclusion_rules": exclusion_rules,
                    "embeddings": embeddings_data
                }, f, indent=2, default=str)
            
            logger.info(f"Saved: {embeddings_file} ({len(embeddings_data)} embeddings)")
            
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return 1
    
    # ========================================================================
    # 2.5: Cluster observations (skip if --skip-cluster)
    # ========================================================================
    if skip_cluster:
        logger.info("[SKIP-CLUSTER] Skipping clustering step")
        result = None
    else:
        logger.info(f"[2.5] Clustering observations (by_category={cluster_cfg.by_category}, optimize={cluster_cfg.optimize})...")
        
        try:
            clusterer = Clusterer(random_state=cluster_cfg.random_state)
            
            # Extract categories for clustering
            categories_list = [i['category'] for i in observations_filtered]
            
            # Prepare category-k map
            category_k_map = {cat: info["target_clusters"] 
                              for cat, info in cluster_cfg.categories.items()}
            
            # Cluster by category with optimization
            result = clusterer.cluster_by_category(
                embeddings=embeddings_array,
                categories=categories_list,
                category_k_map=category_k_map,
                tolerance=cluster_cfg.tolerance,
                test_points=cluster_cfg.test_points,
                normalize_embeddings=cluster_cfg.normalize_embeddings,
                optimize=cluster_cfg.optimize,
                verbose=True
            )
            
            logger.info(f"Clustered: {result['total_clusters']} clusters")
            
            # Add cluster assignments to observations
            for i, observation in enumerate(observations_filtered):
                observation['cluster_id'] = result['cluster_ids'][i]
                observation['cluster_number'] = result['cluster_numbers'][i]
            
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return 1
    
    # ========================================================================
    # 2.6: Save final observations (filtered + clustered)
    # ========================================================================
    logger.info(f"[2.6] Saving final observations (filtered + clustered): {output_file}")
    
    output_data = {
        "export_date": datetime.now().isoformat(),
        "mode": mode_str,
        "observations": observations_filtered,
    }
    
    # Add extraction metadata if we extracted
    if not cluster_only:
        output_data["extraction"] = {
            "model": secrets.gemini_model,
            "prompt_template": extract_cfg.prompt_template,
            "total_conversations": len(conversations),
            "total_observations_extracted": len(observations_raw),
            "total_observations_filtered": len(observations_filtered),
            "exclusion_rules": exclusion_rules
        }
        output_data["embedding"] = {
            "model": secrets.gemini_embedding_model,
            "dimension": secrets.gemini_embedding_dimension,
            "total_embedded": embeddings_array.shape[0],
            "embeddings_file": "embeddings.json"
        }
    
    # Add clustering metadata if we clustered
    if result:
        output_data["clustering"] = {
            "algorithm": cluster_cfg.algorithm,
            "by_category": cluster_cfg.by_category,
            "total_clusters": result['total_clusters'],
            "optimization_results": result['optimization_results'],
            "cluster_sizes": result['cluster_sizes']
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
    logger.info(f"✅ STEP 2 COMPLETE ({duration/60:.1f} min)")
    logger.info("=" * 70)
    
    if skip_cluster:
        logger.info("Next: Review observations, then run ./cli.sh step2 --cluster-only")
    else:
        logger.info("Next: ./cli.sh step3")
    
    return 0


def main():
    """Sync wrapper for async main."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Extract and cluster observations")
    parser.add_argument("--data-path", type=str, default=None,
                        help="Base data directory (overrides config, e.g., temp_data)")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to custom pipeline.yaml")
    parser.add_argument("--cluster-only", action="store_true",
                        help="Only re-cluster existing observations (skip extraction)")
    parser.add_argument("--skip-cluster", action="store_true",
                        help="Only extract observations, skip clustering (for review)")
    args = parser.parse_args()
    
    # Validate mutually exclusive options
    if args.cluster_only and args.skip_cluster:
        logger.error("Cannot use --cluster-only and --skip-cluster together")
        return 1
    
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())

