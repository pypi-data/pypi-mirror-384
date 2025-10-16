"""Application settings and configuration.

Updated to use config/pipeline.yaml for pipeline parameters.
Only secrets (API keys) and paths remain in .env
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env if it exists
# Environment variables take priority if .env doesn't exist
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file, override=False)  # Don't override existing env vars


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
    # Model Configuration (defaults provided, can override via .env)
    # ============================================
    # gemini_model is optional - can be overridden by prompt template metadata
    gemini_model: Optional[str] = "gemini-2.5-flash-lite"  # Default fallback
    gemini_embedding_model: str = "gemini-embedding-001"  # Gemini's text embedding model
    gemini_embedding_dimension: int = 768  # Standard dimension for gemini-embedding-001
    
    # ============================================
    # NOTE: All pipeline parameters (batch_size, cutoff_days, etc.)
    # are now in config/pipeline.yaml - NOT in .env!
    # Use config.loader.get_config() to access them.
    # ============================================

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


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

