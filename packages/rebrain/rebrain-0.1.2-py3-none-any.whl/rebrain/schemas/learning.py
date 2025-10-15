"""
Learning schema - simplified single-layer structure.

Content only (no manifestations), synthesized from observation clusters.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from rebrain.schemas.observation import Category


class ConfidenceLevel(str, Enum):
    """Confidence level based on observation count and consistency."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Learning(BaseModel):
    """
    Simplified learning schema.
    
    Single-layer: content only (manifestations removed to reduce tokens).
    Synthesized from clusters of observations.
    Consistent with Observation schema structure.
    """
    id: str = Field(..., description="Unique identifier (e.g., learning_00001)")
    title: str = Field(..., description="Short title (5-10 words)")
    content: str = Field(..., description="Synthesized learning content (self-sustained, includes all context)")
    keywords: List[str] = Field(
        default_factory=list,
        description="Abstract concepts in lowercase-kebab-case"
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Relevant entities, concepts, or frameworks in Title Case"
    )
    category: Category
    confidence: ConfidenceLevel
    
    # Provenance
    source_observation_ids: List[str] = Field(default_factory=list)
    cluster_id: str
    
    # Metadata
    first_observed: datetime
    last_observed: datetime
    source_observation_count: int


class LearningSynthesis(BaseModel):
    """
    Container for learning synthesis results.
    """
    cluster_id: str
    learning: Learning
    synthesized_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

