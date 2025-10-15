"""
Configuration loader for pipeline.yaml and secrets from .env
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Secrets(BaseSettings):
    """
    Secrets and model config loaded from .env file only.
    
    Model names and API keys are in .env.
    Pipeline parameters (temperature, batch_size, etc.) are in pipeline.yaml.
    
    Note: gemini_model is optional - can be overridden by prompt template metadata.
    """
    gemini_api_key: str
    gemini_model: Optional[str] = "gemini-2.5-flash-lite"  # Default fallback
    gemini_embedding_model: str
    gemini_embedding_dimension: int
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Ignore extra fields from .env
        "env_prefix": "",  # No prefix needed
        "case_sensitive": False,  # Allow GEMINI_API_KEY or gemini_api_key
    }


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


class PipelineConfig(BaseModel):
    """Complete pipeline configuration."""
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


def load_config(config_path: str = "config/pipeline.yaml") -> tuple[Secrets, PipelineConfig]:
    """
    Load configuration from YAML and .env
    
    Args:
        config_path: Path to pipeline.yaml
    
    Returns:
        Tuple of (secrets, pipeline_config)
    """
    # Load secrets from .env
    secrets = Secrets()
    
    # Load pipeline config from YAML
    with open(config_path) as f:
        config_data = yaml.safe_load(f)
    
    pipeline_config = PipelineConfig(**config_data)
    
    return secrets, pipeline_config


def get_config() -> tuple[Secrets, PipelineConfig]:
    """
    Convenience function to load configuration.
    
    Returns:
        Tuple of (secrets, pipeline_config)
    """
    return load_config()

