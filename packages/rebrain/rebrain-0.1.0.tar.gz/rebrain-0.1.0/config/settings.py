"""Application settings and configuration.

Updated to use config/pipeline.yaml for pipeline parameters.
Only secrets (API keys) and paths remain in .env
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env and FORCE them into os.environ
# This ensures .env takes priority over shell environment
env_file = find_dotenv()
assert env_file, "Couldn't find .env file"
load_dotenv(env_file, override=True)  # override=True forces .env to override environment


class Settings(BaseSettings):
    """
    Minimal settings for secrets and paths.
    
    Pipeline parameters moved to config/pipeline.yaml
    Use config.loader.get_config() for pipeline configuration.
    """

    # ============================================
    # Secrets (from .env)
    # ============================================
    gemini_api_key: str

    # ============================================
    # Storage Paths (from .env)
    # ============================================
    data_path: Path = Path("./data")
    storage_path: Path = Path("./storage")
    
    # ============================================
    # Model Configuration (from .env)
    # ============================================
    # gemini_model is optional - can be overridden by prompt template metadata
    gemini_model: Optional[str] = "gemini-2.5-flash-lite"  # Default fallback
    gemini_embedding_model: str
    gemini_embedding_dimension: int
    
    # ============================================
    # NOTE: All pipeline parameters (batch_size, cutoff_days, etc.)
    # are now in config/pipeline.yaml - NOT in .env!
    # Use config.loader.get_config() to access them.
    # ============================================

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()


# Convenience function for new code
def get_pipeline_config():
    """
    Get pipeline configuration from pipeline.yaml
    
    Returns:
        Tuple of (secrets, pipeline_config)
    """
    from config.loader import get_config
    return get_config()

