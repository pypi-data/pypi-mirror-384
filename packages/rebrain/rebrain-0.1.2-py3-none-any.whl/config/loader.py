"""
Configuration loader for pipeline.yaml and secrets from .env
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field

# Import Settings (which contains secrets and defaults) from settings.py
from config.settings import Settings


class IngestionConfig(BaseModel):
    """Ingestion stage configuration."""
    date_cutoff_days: int
    remove_code_blocks: bool
    chunk_size_tokens: int
    chunk_overlap_percent: float


class ObservationExtractionConfig(BaseModel):
    """Observation extraction configuration (temperature from prompt template)."""
    prompt_template: str
    max_concurrent: int
    one_per_conversation: bool
    enable_truncation: bool
    truncation_max_tokens: int
    batch_size: int
    request_delay: float = 0.5
    max_retries: int = 3
    retry_delays: list = Field(default_factory=lambda: [20, 40, 60])


class EmbeddingConfig(BaseModel):
    """Embedding configuration (model and dimension from .env)."""
    batch_size: int
    rate_delay: float
    retry_delays: list = Field(default_factory=lambda: [20, 40])
    max_retries: int = 2


class ClusteringConfig(BaseModel):
    """Clustering configuration."""
    algorithm: str
    target_clusters: int | None = None  # Optional for category-based clustering
    optimize: bool = True
    tolerance: float = 0.2
    test_points: int = 5
    normalize_embeddings: bool = True
    random_state: int = 42


class ObservationClusteringConfig(ClusteringConfig):
    """Observation clustering with category support."""
    by_category: bool = True
    categories: Dict[str, Any] = Field(default_factory=dict)


class SynthesisConfig(BaseModel):
    """Synthesis configuration (model and temperature from prompt template)."""
    prompt_template: str


class LearningSynthesisConfig(SynthesisConfig):
    """Learning synthesis with confidence thresholds."""
    confidence_thresholds: Dict[str, int] = Field(default_factory=dict)


class CategoryExclusionConfig(BaseModel):
    """Category-specific privacy exclusion rules."""
    privacy_levels: list = Field(default_factory=list)


class ObservationExclusionsConfig(BaseModel):
    """
    Observation filtering by category and privacy level.
    
    Applied after extraction, before embedding.
    All observations saved to observations.json for analysis.
    Only filtered observations get embedded.
    """
    technical: CategoryExclusionConfig = Field(default_factory=lambda: CategoryExclusionConfig(privacy_levels=["high"]))
    professional: CategoryExclusionConfig = Field(default_factory=lambda: CategoryExclusionConfig(privacy_levels=["high"]))
    personal: CategoryExclusionConfig = Field(default_factory=lambda: CategoryExclusionConfig(privacy_levels=["medium", "high"]))


class RetrievalConfig(BaseModel):
    """Retrieval configuration."""
    top_k: int = 10
    similarity_threshold: float = 0.7
    enable_graph_traversal: bool = True
    max_hops: int = 2


class PathsConfig(BaseModel):
    """Path configuration."""
    data_dir: str = "./data"


class PipelineConfig(BaseModel):
    """Complete pipeline configuration."""
    paths: PathsConfig
    ingestion: IngestionConfig
    observation_extraction: ObservationExtractionConfig
    observation_embedding: EmbeddingConfig
    observation_clustering: ObservationClusteringConfig
    learning_synthesis: LearningSynthesisConfig
    learning_embedding: EmbeddingConfig
    learning_clustering: ClusteringConfig
    cognition_synthesis: SynthesisConfig
    observation_exclusions: ObservationExclusionsConfig
    retrieval: RetrievalConfig


def load_config(config_path: Optional[str] = None) -> tuple[Settings, PipelineConfig]:
    """
    Load configuration from YAML and .env
    
    Uses bundled config/pipeline.yaml from installed package by default.
    User can override by providing custom config_path.
    
    Args:
        config_path: Optional path to custom pipeline.yaml (overrides bundled config)
    
    Returns:
        Tuple of (secrets, pipeline_config)
    """
    # Load secrets from .env
    secrets = Settings()
    
    # Determine which config file to use
    if config_path and Path(config_path).exists():
        # User provided custom config - use it
        yaml_path = Path(config_path)
    else:
        # Use bundled config (works for both development and installed package)
        # This file is in config/loader.py, so pipeline.yaml is in the same directory
        yaml_path = Path(__file__).parent / "pipeline.yaml"
        
        if not yaml_path.exists():
            raise FileNotFoundError(
                f"Could not find bundled config at {yaml_path}. "
                "Please provide a custom config_path or ensure the package is installed correctly."
            )
    
    # Load from file path
    with open(yaml_path) as f:
        config_data = yaml.safe_load(f)
    
    pipeline_config = PipelineConfig(**config_data)
    
    return secrets, pipeline_config


def get_config() -> tuple[Settings, PipelineConfig]:
    """
    Convenience function to load configuration.
    
    Returns:
        Tuple of (secrets, pipeline_config)
    """
    return load_config()

