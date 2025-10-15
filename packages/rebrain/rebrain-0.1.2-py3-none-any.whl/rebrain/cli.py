#!/usr/bin/env python3
"""
ReBrain CLI - User-friendly command-line interface.

Provides UV/UVX compatible commands for pipeline processing and status.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rebrain.config.user_config import (
    get_api_key,
    get_data_path,
    ensure_directories,
    load_user_config,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="rebrain",
        description="ReBrain - Transform chat history into structured AI memory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  rebrain pipeline run --input conversations.json
  
  # Start MCP server
  rebrain mcp
  
  # Check status
  rebrain status
  
  # Interactive setup
  rebrain init
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run pipeline processing",
    )
    pipeline_subparsers = pipeline_parser.add_subparsers(
        dest="pipeline_command",
        help="Pipeline operations",
    )
    
    # Pipeline run
    run_parser = pipeline_subparsers.add_parser(
        "run",
        help="Run full pipeline (all 5 steps)",
    )
    run_parser.add_argument(
        "--input",
        "-i",
        default="conversations.json",
        help="Input conversations JSON file (default: conversations.json)",
    )
    run_parser.add_argument(
        "--data-path",
        help="Data directory path (default: auto-detect)",
    )
    run_parser.add_argument(
        "--max-conversations",
        type=int,
        default=1000,
        help="Maximum number of conversations to process (default: 1000)",
    )
    run_parser.add_argument(
        "--cutoff-days",
        type=int,
        help="Only process conversations from last N days",
    )
    run_parser.add_argument(
        "--config",
        help="Path to custom pipeline.yaml (default: uses bundled config)",
    )
    run_parser.add_argument(
        "--continue",
        dest="continue_from",
        choices=["step2", "step3", "step4", "step5"],
        help=argparse.SUPPRESS,  # Hidden option for recovery
    )
    
    # Individual pipeline steps (hidden from main help)
    for step_num in range(1, 6):
        step_parser = pipeline_subparsers.add_parser(
            f"step{step_num}",
            help=argparse.SUPPRESS,
        )
        step_parser.add_argument("--data-path", help="Data directory path")
        step_parser.add_argument("--config", help="Path to custom pipeline.yaml")
    
    # Load command
    load_parser = subparsers.add_parser(
        "load",
        help="Load JSONs into memg-core database",
    )
    load_parser.add_argument(
        "--data-path",
        help="Data directory path (default: auto-detect)",
    )
    load_parser.add_argument(
        "--force",
        action="store_true",
        help="Force reload even if database exists",
    )
    
    # Status command
    subparsers.add_parser(
        "status",
        help="Show processing status",
    )
    
    # Init command
    subparsers.add_parser(
        "init",
        help="Interactive setup wizard",
    )
    
    # Version command
    subparsers.add_parser(
        "version",
        help="Show version information",
    )
    
    return parser


def run_pipeline(args: argparse.Namespace) -> int:
    """Run the full pipeline or continue from specific step."""
    # Get API key early
    api_key = get_api_key()
    os.environ["GEMINI_API_KEY"] = api_key
    
    # Load config to potentially override data_path
    from config.loader import load_config
    _, config = load_config(config_path=args.config if hasattr(args, 'config') else None)
    
    # Determine data path with smarter detection
    if args.data_path:
        data_path = Path(args.data_path)
        # Override config's data_dir
        config.paths.data_dir = str(data_path)
        print(f"📍 Using data directory: {data_path} (overridden)")
    else:
        # Try to derive data path from input file location
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = Path.cwd() / input_path
        
        # If input is in data/raw/*, use data/ as base
        if input_path.exists():
            # Check if input is in a data/raw structure
            if input_path.parent.name == "raw" and input_path.parent.parent.name == "data":
                data_path = input_path.parent.parent
                print(f"📍 Detected data directory from input file: {data_path}")
            else:
                # Fall back to config default or auto-detection
                data_path = Path(config.paths.data_dir) if hasattr(config, 'paths') else get_data_path()
        else:
            # Input doesn't exist yet, use config default or auto-detection
            data_path = Path(config.paths.data_dir) if hasattr(config, 'paths') else get_data_path()
    
    ensure_directories(data_path)
    
    print(f"🧠 ReBrain Pipeline")
    print(f"📁 Data directory: {data_path}")
    print()
    
    # Find scripts directory
    scripts_dir = Path(__file__).parent.parent / "scripts" / "pipeline"
    
    # Determine which steps to run
    if args.continue_from:
        step_map = {
            "step2": 2,
            "step3": 3,
            "step4": 4,
            "step5": 5,
        }
        start_step = step_map[args.continue_from]
        print(f"▶️  Continuing from step {start_step}")
    else:
        start_step = 1
    
    steps = [
        (1, "01_transform_filter.py", "Transform & Filter"),
        (2, "02_extract_cluster_observations.py", "Extract & Cluster Observations"),
        (3, "03_synthesize_cluster_learnings.py", "Synthesize Learnings"),
        (4, "04_synthesize_cognitions.py", "Synthesize Cognitions"),
        (5, "05_build_persona.py", "Build Persona"),
    ]
    
    # Ensure input file exists at data_path/raw/conversations.json
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = Path.cwd() / input_path
    
    expected_input = data_path / "raw" / "conversations.json"
    if input_path != expected_input:
        # Copy or symlink the input file to the expected location
        expected_input.parent.mkdir(parents=True, exist_ok=True)
        if not expected_input.exists():
            import shutil
            print(f"📋 Copying input file to: {expected_input}")
            shutil.copy2(input_path, expected_input)
    
    # Run steps
    for step_num, script_name, step_name in steps:
        if step_num < start_step:
            continue
        
        print(f"{'=' * 80}")
        print(f"Step {step_num}: {step_name}")
        print(f"{'=' * 80}")
        
        script_path = scripts_dir / script_name
        
        # Build command - all scripts now use unified --data-path interface
        cmd = [sys.executable, str(script_path), "--data-path", str(data_path)]
        
        # Add custom config if provided
        if hasattr(args, 'config') and args.config:
            cmd.extend(["--config", args.config])
        
        # Add step-specific arguments
        if step_num == 1:
            # Step 1 also accepts --max-conversations
            if args.max_conversations:
                cmd.extend(["--max-conversations", str(args.max_conversations)])
        
        # Run step
        try:
            result = subprocess.run(cmd, check=True)
            if result.returncode != 0:
                print(f"❌ Step {step_num} failed")
                print(f"💡 To continue from this step: rebrain pipeline run --continue step{step_num}")
                return 1
        except subprocess.CalledProcessError as e:
            print(f"❌ Step {step_num} failed with error: {e}")
            print(f"💡 To continue from this step: rebrain pipeline run --continue step{step_num}")
            return 1
        except KeyboardInterrupt:
            print(f"\n⚠️  Pipeline interrupted at step {step_num}")
            print(f"💡 To continue: rebrain pipeline run --continue step{step_num}")
            return 130
        
        print()
    
    print(f"{'=' * 80}")
    print("✅ Pipeline completed successfully!")
    print(f"{'=' * 80}")
    print()
    print(f"📊 Results:")
    print(f"   Persona: {data_path / 'persona' / 'persona.md'}")
    print(f"   All data: {data_path}")
    print()
    print(f"💡 Next steps:")
    print(f"   1. Load into memg-core: rebrain load")
    print(f"   2. Start MCP server: rebrain mcp")
    print()
    
    return 0


def run_individual_step(args: argparse.Namespace) -> int:
    """Run a single pipeline step."""
    # Get API key early
    api_key = get_api_key()
    os.environ["GEMINI_API_KEY"] = api_key
    
    # Load config
    from config.loader import load_config
    _, config = load_config(config_path=args.config if hasattr(args, 'config') else None)
    
    # Determine data path
    if args.data_path:
        data_path = Path(args.data_path)
    else:
        data_path = Path(config.paths.data_dir) if hasattr(config, 'paths') else get_data_path()
    
    ensure_directories(data_path)
    
    # Extract step number from command (e.g., "step1" -> 1)
    step_num = int(args.pipeline_command.replace("step", ""))
    
    # Map step numbers to scripts
    step_map = {
        1: ("01_transform_filter.py", "Transform & Filter"),
        2: ("02_extract_cluster_observations.py", "Extract & Cluster Observations"),
        3: ("03_synthesize_cluster_learnings.py", "Synthesize Learnings"),
        4: ("04_synthesize_cognitions.py", "Synthesize Cognitions"),
        5: ("05_build_persona.py", "Build Persona"),
    }
    
    if step_num not in step_map:
        print(f"❌ Invalid step: {args.pipeline_command}")
        return 1
    
    script_name, step_name = step_map[step_num]
    
    print(f"🧠 ReBrain Pipeline - Step {step_num}")
    print(f"📁 Data directory: {data_path}")
    print()
    print(f"{'=' * 80}")
    print(f"Step {step_num}: {step_name}")
    print(f"{'=' * 80}")
    
    # Find scripts directory
    scripts_dir = Path(__file__).parent.parent / "scripts" / "pipeline"
    script_path = scripts_dir / script_name
    
    # Build command - all scripts use unified --data-path interface
    cmd = [sys.executable, str(script_path), "--data-path", str(data_path)]
    
    # Add custom config if provided
    if hasattr(args, 'config') and args.config:
        cmd.extend(["--config", args.config])
    
    # Run step
    try:
        result = subprocess.run(cmd, check=True)
        print()
        print(f"✅ Step {step_num} completed successfully!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ Step {step_num} failed with error: {e}")
        return 1
    except KeyboardInterrupt:
        print(f"\n⚠️  Step {step_num} interrupted")
        return 130


def run_load(args: argparse.Namespace) -> int:
    """Load JSONs into memg-core database."""
    # Determine data path
    if args.data_path:
        data_path = Path(args.data_path)
    else:
        data_path = get_data_path()
    
    print(f"📦 Loading data into memg-core")
    print(f"📁 Data directory: {data_path}")
    print()
    
    # Find load_memg.py script
    load_script = Path(__file__).parent.parent / "scripts" / "load_memg.py"
    
    # Build command
    cmd = [
        sys.executable,
        str(load_script),
        "--cognitions", str(data_path / "cognitions" / "cognitions.json"),
        "--learnings", str(data_path / "learnings" / "learnings.json"),
        "--output", str(data_path / "memory_db"),
    ]
    
    # Add force flag if needed
    if args.force:
        # Delete existing database
        import shutil
        db_path = data_path / "memory_db"
        if db_path.exists():
            print(f"🗑️  Removing existing database...")
            shutil.rmtree(db_path)
    
    # Run load script
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Load failed: {e}")
        return 1


def show_status(args: argparse.Namespace) -> int:
    """Show processing status."""
    data_path = get_data_path()
    
    print(f"🧠 ReBrain Status")
    print(f"{'=' * 80}")
    print(f"📁 Data directory: {data_path}")
    print()
    
    # Check files
    files_to_check = [
        ("Raw conversations", "raw/conversations.json", False),
        ("Cleaned conversations", "preprocessed/conversations_clean.json", False),
        ("Observations", "observations/observations.json", False),
        ("Learnings", "learnings/learnings.json", False),
        ("Cognitions", "cognitions/cognitions.json", False),
        ("Persona (JSON)", "persona/persona.json", False),
        ("Persona (MD)", "persona/persona.md", False),
        ("Memg-core DB", "memory_db", True),
    ]
    
    all_exist = True
    for name, path, is_dir in files_to_check:
        full_path = data_path / path
        if is_dir:
            exists = full_path.exists() and full_path.is_dir()
        else:
            exists = full_path.exists() and full_path.is_file()
        
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {path}")
        
        if exists and not is_dir:
            # Show file size
            size = full_path.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            print(f"   Size: {size_str}")
        
        if not exists:
            all_exist = False
    
    print()
    
    if all_exist:
        print("✅ All pipeline outputs present")
        print()
        print("💡 You can:")
        print("   - Start MCP server: rebrain mcp")
        print("   - View persona: cat", data_path / "persona" / "persona.md")
    else:
        print("⚠️  Some outputs missing")
        print()
        print("💡 To process:")
        print("   - Run pipeline: rebrain pipeline run --input conversations.json")
    
    return 0


def run_init(args: argparse.Namespace) -> int:
    """Interactive setup wizard."""
    print("🧠 ReBrain Setup Wizard")
    print("=" * 80)
    print()
    
    # Check API key
    print("1️⃣  Checking API key...")
    try:
        api_key = get_api_key()
        print("✅ API key configured")
    except SystemExit:
        return 1
    
    print()
    
    # Check data directory
    print("2️⃣  Checking data directory...")
    data_path = get_data_path()
    print(f"✅ Using: {data_path}")
    
    ensure_directories(data_path)
    print("✅ Directories created")
    
    print()
    
    # Check for conversations file
    print("3️⃣  Looking for conversations.json...")
    conv_paths = [
        Path.cwd() / "conversations.json",
        data_path / "raw" / "conversations.json",
    ]
    
    found = None
    for path in conv_paths:
        if path.exists():
            found = path
            break
    
    if found:
        print(f"✅ Found: {found}")
    else:
        print("❌ Not found")
        print()
        print("💡 Please:")
        print("   1. Export your ChatGPT conversations")
        print("   2. Place the file at: conversations.json")
        print("   3. Run: rebrain pipeline run --input conversations.json")
    
    print()
    print("=" * 80)
    print("✅ Setup complete!")
    print()
    
    if found:
        print("💡 Next step:")
        print(f"   rebrain pipeline run --input {found}")
    
    return 0


def show_version(args: argparse.Namespace) -> int:
    """Show version information."""
    from rebrain import __version__
    print("🧠 ReBrain")
    print(f"Version: {__version__}")
    print("Built by Yasin Salimibeni")
    return 0


def main() -> int:
    """Main entry point for rebrain CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Route to appropriate handler
    if args.command == "pipeline":
        if args.pipeline_command == "run":
            return run_pipeline(args)
        elif args.pipeline_command and args.pipeline_command.startswith("step"):
            return run_individual_step(args)
        else:
            parser.parse_args(["pipeline", "--help"])
            return 0
    
    elif args.command == "load":
        return run_load(args)
    
    elif args.command == "status":
        return show_status(args)
    
    elif args.command == "init":
        return run_init(args)
    
    elif args.command == "version":
        return show_version(args)
    
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

