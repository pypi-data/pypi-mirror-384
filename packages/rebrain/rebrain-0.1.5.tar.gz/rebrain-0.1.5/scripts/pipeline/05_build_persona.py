#!/usr/bin/env python3
"""
Step 5: Build Persona

Synthesizes all cognitions into a simple 3-field persona for system prompt injection.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.loader import load_config
from rebrain.operations import GenericSynthesizer
from rebrain.schemas.persona import Persona
from rebrain.persona.formatters import generate_markdown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Suppress verbose HTTP logs
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)


def main():
    """Build persona from cognitions."""
    start_time = datetime.now()
    
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Build persona from cognitions")
    parser.add_argument("--data-path", type=str, default=None,
                        help="Base data directory (overrides config, e.g., temp_data)")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to custom pipeline.yaml")
    args = parser.parse_args()
    
    # Load configuration
    try:
        secrets, config = load_config(config_path=args.config)
        # Use CLI data-path if provided, otherwise use config
        if args.data_path:
            data_path = Path(args.data_path)
        else:
            data_path = Path(config.paths.data_dir)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1
    
    # Paths (fixed relative to data_path)
    input_file = data_path / "cognitions/cognitions.json"
    output_file = data_path / "persona/persona.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("STEP 5: BUILD PERSONA")
    logger.info("=" * 70)
    
    # ========================================================================
    # 5.1: Load cognitions
    # ========================================================================
    logger.info(f"[5.1] Loading cognitions: {input_file}")
    try:
        with open(input_file) as f:
            data = json.load(f)
        
        cognitions = data.get("cognitions", [])
        logger.info(f"Loaded {len(cognitions)} cognitions")
        
        if not cognitions:
            logger.error("No cognitions found")
            return 1
        
    except Exception as e:
        logger.error(f"Failed to load cognitions: {e}")
        return 1
    
    # ========================================================================
    # 5.2: Synthesize persona
    # ========================================================================
    logger.info(f"[5.2] Synthesizing persona (model={secrets.gemini_model})...")
    
    try:
        synthesizer = GenericSynthesizer(prompt_template="persona_synthesis")
        
        # Format cognitions for synthesis
        cognitions_context = []
        for i, cog in enumerate(cognitions, 1):
            content = cog.get('content', '')
            domains = ', '.join(cog.get('domains', []))
            priority = cog.get('priority', 'unknown')
            cognitions_context.append(
                f"{i}. [{domains}] [{priority}] {content}"
            )
        
        input_data = {
            "cognition_count": len(cognitions),
            "cognitions": "\n\n".join(cognitions_context)
        }
        
        persona = synthesizer.synthesize(
            input_data=input_data,
            output_schema=Persona
        )
        
        if not persona:
            logger.error("Persona synthesis failed")
            return 1
        
        logger.info("✓ Persona synthesized")
        
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return 1
    
    # ========================================================================
    # 5.3: Save persona (JSON + Markdown)
    # ========================================================================
    logger.info(f"[5.3] Saving persona...")
    
    persona_dict = persona.model_dump()
    
    # Save JSON
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "source_cognitions": len(cognitions),
        "model": synthesizer.client.model,  # Actual model used (may be overridden by prompt)
        "persona": persona_dict
    }
    
    try:
        # Save JSON file
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        json_size = output_file.stat().st_size / 1024
        logger.info(f"✓ JSON saved: {output_file} ({json_size:.2f} KB)")
        
        # Save Markdown file
        md_file = output_file.with_suffix('.md')
        md_content = generate_markdown(persona_dict, output_data)
        
        with open(md_file, 'w') as f:
            f.write(md_content)
        
        md_size = md_file.stat().st_size / 1024
        logger.info(f"✓ Markdown saved: {md_file} ({md_size:.2f} KB)")
        
    except Exception as e:
        logger.error(f"Failed to save persona: {e}")
        return 1
    
    # ========================================================================
    # Summary
    # ========================================================================
    duration = (datetime.now() - start_time).total_seconds()
    
    logger.info("=" * 70)
    logger.info(f"✅ STEP 5 COMPLETE ({duration:.1f}s)")
    logger.info("=" * 70)
    logger.info(f"Persona built from {len(cognitions)} cognitions")
    logger.info(f"Output files:")
    logger.info(f"  - {output_file}")
    logger.info(f"  - {output_file.with_suffix('.md')}")
    logger.info("")
    logger.info("Preview:")
    logger.info("-" * 70)
    logger.info("PERSONAL PROFILE:")
    logger.info(persona_dict['personal_profile'][:200] + "...")
    logger.info("")
    logger.info("COMMUNICATION PREFERENCES:")
    logger.info(persona_dict['communication_preferences'][:150] + "...")
    logger.info("")
    logger.info("PROFESSIONAL PROFILE:")
    logger.info(persona_dict['professional_profile'][:200] + "...")
    logger.info("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

