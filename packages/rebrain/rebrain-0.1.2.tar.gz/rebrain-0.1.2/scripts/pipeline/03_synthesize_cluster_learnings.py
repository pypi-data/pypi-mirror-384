#!/usr/bin/env python3
"""
Step 3: Synthesize & Cluster Learnings

Consolidated: Synthesize learnings → Embed → Cluster

Input: data/observations/observations.json
Output: data/learnings/learnings.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.loader import load_config
from rebrain.operations import GenericSynthesizer, Embedder, Clusterer
from rebrain.schemas import Learning

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Synthesize and cluster learnings."""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Synthesize and cluster learnings")
    parser.add_argument("--data-path", type=str, default=None,
                        help="Base data directory (overrides config, e.g., temp_data)")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to custom pipeline.yaml")
    args = parser.parse_args()
    
    start_time = datetime.now()
    
    # Load configuration
    try:
        secrets, config = load_config(config_path=args.config)
        # Use CLI data-path if provided, otherwise use config
        if args.data_path:
            data_path = Path(args.data_path)
        else:
            data_path = Path(config.paths.data_dir)
        synth_cfg = config.learning_synthesis
        embed_cfg = config.learning_embedding
        cluster_cfg = config.learning_clustering
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1
    
    # Paths (fixed relative to data_path)
    input_file = data_path / "observations/observations.json"
    output_file = data_path / "learnings/learnings.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("STEP 3: SYNTHESIZE & CLUSTER LEARNINGS")
    logger.info("=" * 70)
    
    # ========================================================================
    # 3.1: Load clustered observations
    # ========================================================================
    logger.info(f"[3.1] Loading clustered observations: {input_file}")
    try:
        with open(input_file) as f:
            data = json.load(f)
        
        observations = data["observations"]
        logger.info(f"Loaded {len(observations):,} observations")
        
        # Group by cluster
        clusters = defaultdict(list)
        for observation in observations:
            cluster_id = observation['cluster_id']
            clusters[cluster_id].append(observation)
        
        logger.info(f"Grouped into {len(clusters)} clusters")
        
    except Exception as e:
        logger.error(f"Failed to load observations: {e}")
        return 1
    
    # ========================================================================
    # 3.2: Synthesize learnings from clusters
    # ========================================================================
    logger.info(f"[3.2] Synthesizing learnings (model={secrets.gemini_model}, prompt={synth_cfg.prompt_template})...")
    
    try:
        synthesizer = GenericSynthesizer(prompt_template=synth_cfg.prompt_template)
        
        learnings = []
        failed = []
        
        for cluster_id in sorted(clusters.keys()):
            cluster_observations = clusters[cluster_id]
            
            # Format cluster for synthesis
            cluster_data = {
                "cluster_id": cluster_id,
                "observations": cluster_observations,
                "count": len(cluster_observations)
            }
            
            learning = synthesizer.synthesize(
                input_data=cluster_data,
                output_schema=Learning
            )
            
            if learning:
                learning_dict = learning.model_dump()
                # Add unique ID (e.g., learning_00001)
                learning_dict['id'] = f"learning_{len(learnings):05d}"
                learning_dict['cluster_id'] = cluster_id
                learnings.append(learning_dict)
            else:
                failed.append(cluster_id)
        
        logger.info(f"Synthesized: {len(learnings)}/{len(clusters)} learnings")
        if failed:
            logger.warning(f"Failed: {len(failed)} clusters")
        
        # Statistics
        categories = Counter(l['category'] for l in learnings)
        logger.info(f"Categories: {dict(categories)}")
        
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return 1
    
    # ========================================================================
    # 3.3: Embed learnings
    # ========================================================================
    logger.info(f"[3.3] Embedding learnings (model={secrets.gemini_embedding_model}, batch={embed_cfg.batch_size})...")
    
    try:
        embedder = Embedder()
        
        # Extract title + content for embedding (same as observations)
        texts = [f"{l['title']}\n{l['content']}" for l in learnings]
        
        embeddings_array = embedder.embed_texts(
            texts=texts,
            show_progress=True,
            retry_on_failure=True
        )
        
        logger.info(f"Embedded: {embeddings_array.shape[0]} learnings")
        
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return 1
    
    # ========================================================================
    # 3.4: Cluster learnings
    # ========================================================================
    logger.info(f"[3.4] Clustering learnings (target={cluster_cfg.target_clusters}, optimize={cluster_cfg.optimize})...")
    
    try:
        clusterer = Clusterer(random_state=cluster_cfg.random_state)
        
        result = clusterer.cluster_with_optimization(
            embeddings=embeddings_array,
            target=cluster_cfg.target_clusters,
            tolerance=cluster_cfg.tolerance,
            test_points=cluster_cfg.test_points,
            normalize_embeddings=cluster_cfg.normalize_embeddings,
            verbose=True
        )
        
        logger.info(f"Clustered: {result['best_k']} clusters (silhouette={result['best_score']:.4f})")
        
        # Add cluster assignments to learnings
        for i, learning in enumerate(learnings):
            cluster_label = result['cluster_labels'][i]
            learning['cognition_cluster_id'] = f"cognition_{cluster_label}"
            learning['cognition_cluster_number'] = int(cluster_label)
        
        # Calculate cluster sizes
        cluster_stats = clusterer.get_cluster_statistics(result['cluster_labels'])
        logger.info(f"Cluster sizes: min={cluster_stats['min_size']}, max={cluster_stats['max_size']}, mean={cluster_stats['mean_size']:.1f}")
        
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        return 1
    
    # ========================================================================
    # 3.5: Save output
    # ========================================================================
    logger.info(f"[3.5] Saving output: {output_file}")
    
    output_data = {
        "export_date": datetime.now().isoformat(),
        "synthesis": {
            "model": secrets.gemini_model,
            "prompt_template": synth_cfg.prompt_template,
            "total_clusters": len(clusters),
            "successful": len(learnings),
            "failed": len(failed)
        },
        "embedding": {
            "model": secrets.gemini_embedding_model,
            "dimension": secrets.gemini_embedding_dimension,
            "total_embedded": embeddings_array.shape[0]
        },
        "clustering": {
            "algorithm": cluster_cfg.algorithm,
            "target": cluster_cfg.target_clusters,
            "best_k": result['best_k'],
            "best_score": result['best_score'],
            "optimization": {
                "tested_k_values": result['tested_k_values'],
                "scores": result['scores']
            }
        },
        "learnings": learnings,
        "embeddings": embeddings_array.tolist(),
        "cluster_statistics": cluster_stats
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
    logger.info(f"✅ STEP 3 COMPLETE ({duration/60:.1f} min)")
    logger.info("=" * 70)
    logger.info("Next: python 04_synthesize_cognitions.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

