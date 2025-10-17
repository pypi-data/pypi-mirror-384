"""
User configuration helpers for ReBrain CLI.

Handles API key management, data path detection, and directory setup.
"""

import os
import sys
from getpass import getpass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv


def get_api_key() -> str:
    """
    Get Google GenAI API key with priority: env var > .env file > prompt user.
    
    Returns:
        API key string
        
    Raises:
        SystemExit if no key can be obtained
    """
    # Priority 1: Environment variable
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key.strip()
    
    # Priority 2: .env file in current directory
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            return api_key.strip()
    
    # Priority 3: Gracefully guide user
    print("🔑 Google GenAI API key not found")
    print()
    print("Please provide your API key in one of these ways:")
    print("  1. Set environment variable: export GEMINI_API_KEY=your_key_here")
    print("  2. Create .env file with: GEMINI_API_KEY=your_key_here")
    print()
    print("Get your API key from: https://aistudio.google.com/app/apikey")
    print()
    
    response = input("Would you like to enter it now? (y/n): ").strip().lower()
    if response in ('y', 'yes'):
        api_key = getpass("Enter your Google GenAI API key: ").strip()
        if validate_api_key(api_key):
            # Offer to save to .env
            save = input("Save to .env file for future use? (y/n): ").strip().lower()
            if save in ('y', 'yes'):
                with open(".env", "a") as f:
                    f.write(f"\nGEMINI_API_KEY={api_key}\n")
                print("✅ Saved to .env file")
            return api_key
    
    print("❌ Cannot proceed without API key")
    sys.exit(1)


def validate_api_key(key: str) -> bool:
    """
    Basic validation of API key format.
    
    Args:
        key: API key to validate
        
    Returns:
        True if key looks valid, False otherwise
    """
    if not key:
        return False
    
    # Basic checks
    key = key.strip()
    if len(key) < 20:
        print("⚠️  Warning: API key seems too short")
        return False
    
    if ' ' in key:
        print("⚠️  Warning: API key should not contain spaces")
        return False
    
    return True


def get_data_path() -> Path:
    """
    Auto-detect data directory with convention-based search.
    
    Priority:
      1. Current directory has data/ → use it
      2. Parent directory has data/ → use it  
      3. ~/.rebrain/data (create if needed)
    
    Returns:
        Path to data directory
    """
    # Check current directory
    cwd_data = Path.cwd() / "data"
    if cwd_data.exists() and cwd_data.is_dir():
        return cwd_data
    
    # Check parent directory
    parent_data = Path.cwd().parent / "data"
    if parent_data.exists() and parent_data.is_dir():
        return parent_data
    
    # Fallback to user home
    home_data = Path.home() / ".rebrain" / "data"
    home_data.mkdir(parents=True, exist_ok=True)
    return home_data


def ensure_directories(data_path: Path) -> None:
    """
    Ensure all required directories exist in data path.
    
    Args:
        data_path: Base data directory path
    """
    directories = [
        data_path / "raw",
        data_path / "preprocessed",
        data_path / "observations",
        data_path / "learnings",
        data_path / "cognitions",
        data_path / "persona",
        data_path / "memory_db",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_config_path() -> Path:
    """
    Get path to user config file.
    
    Returns:
        Path to ~/.rebrain/config.yaml
    """
    config_dir = Path.home() / ".rebrain"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.yaml"


def load_user_config() -> dict:
    """
    Load user configuration from ~/.rebrain/config.yaml
    
    Returns:
        Configuration dictionary (empty if file doesn't exist)
    """
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


def save_user_config(config: dict) -> None:
    """
    Save user configuration to ~/.rebrain/config.yaml
    
    Args:
        config: Configuration dictionary to save
    """
    config_path = get_config_path()
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_or_set_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get configuration value or set default if not present.
    
    Args:
        key: Configuration key
        default: Default value to set if key not present
        
    Returns:
        Configuration value or None
    """
    config = load_user_config()
    
    if key in config:
        return config[key]
    
    if default is not None:
        config[key] = default
        save_user_config(config)
    
    return default

