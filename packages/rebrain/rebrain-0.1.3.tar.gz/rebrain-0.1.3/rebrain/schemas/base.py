"""
Base schema for unified memory hierarchy.

All layers (observations, learnings, cognitions) share these core fields.
"""

from typing import List
from pydantic import BaseModel, Field


class MemoryBase(BaseModel):
    """
    Base schema for all memory layers.
    
    Provides unified structure across observations, learnings, and cognitions.
    """
    title: str = Field(..., description="Concise title summarizing the content")
    content: str = Field(..., description="Detailed content")
    keywords: List[str] = Field(
        default_factory=list,
        description="Abstract concepts in lowercase-kebab-case (e.g., 'cloud-computing', 'data-persistence')"
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Concrete names in Title Case (e.g., 'AWS', 'Docker', 'Python')"
    )
