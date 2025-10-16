"""
Cognition schema - simplified single-layer structure.

Content only (no double-layer), synthesized from learning clusters.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class StabilityLevel(str, Enum):
    """How stable/consistent this cognition is over time."""
    STABLE = "stable"
    EVOLVING = "evolving"
    EMERGING = "emerging"


class PriorityLevel(str, Enum):
    """Importance/priority of this cognition."""
    CORE = "core"
    IMPORTANT = "important"
    PERIPHERAL = "peripheral"


class Cognition(BaseModel):
    """
    Simplified cognition schema.
    
    Single-layer: content only (no manifestations).
    Highest-level abstraction synthesized from learning clusters.
    """
    content: str = Field(..., description="Core principle/cognition content")
    domains: List[str] = Field(default_factory=list, description="Applicable domains")
    stability: StabilityLevel
    priority: PriorityLevel
    keywords: List[str] = Field(default_factory=list)
    
    # Provenance: track source learnings
    source_learning_ids: List[str] = Field(default_factory=list)
    cluster_id: str
    
    # Metadata
    first_observed: datetime
    last_observed: datetime
    source_learning_count: int


class CognitionSynthesis(BaseModel):
    """
    Container for cognition synthesis results.
    """
    cluster_id: str
    cognition: Cognition
    synthesized_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

