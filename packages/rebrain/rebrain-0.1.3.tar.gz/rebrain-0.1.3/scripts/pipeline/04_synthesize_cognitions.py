#!/usr/bin/env python3
"""
Step 4: Synthesize Cognitions

Final synthesis: Learning clusters → Cognitions (no embedding/clustering)

Input: data/learnings/learnings.json
Output: data/cognitions/cognitions.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.loader import load_config
from rebrain.operations import GenericSynthesizer
from rebrain.schemas import Cognition

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Synthesize cognitions from learning clusters."""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Synthesize cognitions")
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
        synth_cfg = config.cognition_synthesis
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1
    
    # Paths (fixed relative to data_path)
    input_file = data_path / "learnings/learnings.json"
    output_file = data_path / "cognitions/cognitions.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("STEP 4: SYNTHESIZE COGNITIONS (FINAL)")
    logger.info("=" * 70)
    
    # ========================================================================
    # 4.1: Load clustered learnings
    # ========================================================================
    logger.info(f"[4.1] Loading clustered learnings: {input_file}")
    try:
        with open(input_file) as f:
            data = json.load(f)
        
        learnings = data["learnings"]
        logger.info(f"Loaded {len(learnings):,} learnings")
        
        # Group by cognition cluster
        clusters = defaultdict(list)
        for learning in learnings:
            cluster_id = learning['cognition_cluster_id']
            clusters[cluster_id].append(learning)
        
        logger.info(f"Grouped into {len(clusters)} cognition clusters")
        
    except Exception as e:
        logger.error(f"Failed to load learnings: {e}")
        return 1
    
    # ========================================================================
    # 4.2: Synthesize cognitions
    # ========================================================================
    logger.info(f"[4.2] Synthesizing cognitions (model={secrets.gemini_model}, prompt={synth_cfg.prompt_template})...")
    
    try:
        synthesizer = GenericSynthesizer(prompt_template=synth_cfg.prompt_template)
        
        cognitions = []
        failed = []
        
        for cluster_id in sorted(clusters.keys()):
            cluster_learnings = clusters[cluster_id]
            
            # Format cluster for synthesis
            cluster_data = {
                "cluster_id": cluster_id,
                "learnings": cluster_learnings,
                "count": len(cluster_learnings)
            }
            
            cognition = synthesizer.synthesize(
                input_data=cluster_data,
                output_schema=Cognition
            )
            
            if cognition:
                cognition_dict = cognition.model_dump()
                cognition_dict['cluster_id'] = cluster_id
                cognitions.append(cognition_dict)
            else:
                failed.append(cluster_id)
        
        logger.info(f"Synthesized: {len(cognitions)}/{len(clusters)} cognitions")
        if failed:
            logger.warning(f"Failed: {len(failed)} clusters")
        
        # Statistics
        stabilities = Counter(c['stability'] for c in cognitions)
        priorities = Counter(c['priority'] for c in cognitions)
        
        logger.info(f"Stability: {dict(stabilities)}")
        logger.info(f"Priority: {dict(priorities)}")
        
        # Domain statistics
        all_domains = []
        for c in cognitions:
            all_domains.extend(c['domains'])
        domain_counts = Counter(all_domains)
        logger.info(f"Top domains: {dict(domain_counts.most_common(5))}")
        
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return 1
    
    # ========================================================================
    # 4.3: Save output
    # ========================================================================
    logger.info(f"[4.3] Saving final output: {output_file}")
    
    output_data = {
        "export_date": datetime.now().isoformat(),
        "synthesis": {
            "model": secrets.gemini_model,
            "prompt_template": synth_cfg.prompt_template,
            "total_clusters": len(clusters),
            "successful": len(cognitions),
            "failed": len(failed)
        },
        "cognitions": cognitions,
        "statistics": {
            "total_cognitions": len(cognitions),
            "stability_distribution": dict(stabilities),
            "priority_distribution": dict(priorities),
            "domain_distribution": dict(domain_counts.most_common(10))
        }
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
    logger.info(f"✅ STEP 4 COMPLETE ({duration/60:.1f} min)")
    logger.info("=" * 70)
    logger.info("🎉 PIPELINE FINISHED! All 4 steps complete.")
    logger.info(f"Final output: {output_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

