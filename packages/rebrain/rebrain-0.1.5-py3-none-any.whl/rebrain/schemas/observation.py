"""
Observation schema - first layer of memory hierarchy.

One dominant observation per conversation with unified structure.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class Category(str, Enum):
    """Observation category."""
    TECHNICAL = "technical"
    PROFESSIONAL = "professional"
    PERSONAL = "personal"


class PrivacyLevel(str, Enum):
    """Privacy level for filtering."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Observation(BaseModel):
    """
    Unified observation schema.
    
    Single-layer structure with consistent fields across hierarchy.
    One dominant observation per conversation.
    """
    id: str = Field(..., description="Unique identifier (e.g., observation_00001)")
    title: str = Field(..., description="Short title (5-10 words)")
    content: str = Field(..., description="Detailed observation content")
    keywords: List[str] = Field(
        default_factory=list,
        description="Abstract concepts in lowercase-kebab-case"
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Concrete names in Title Case"
    )
    category: Category
    privacy: PrivacyLevel
    
    # Provenance: track source conversation (added by script)
    conversation_id: Optional[str] = None
    conversation_title: Optional[str] = None
    
    # Metadata (added by script)
    timestamp: Optional[datetime] = None
    main_language: str = "en"


class ObservationExtraction(BaseModel):
    """
    Container for observation extraction result.
    
    One observation per conversation.
    """
    conversation_id: Optional[str] = None  # Added by script after extraction
    observation: Optional[Observation] = None  # None if no dominant observation found
    extracted_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

