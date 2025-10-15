"""
Persona schema - simple 3-field model for system prompt injection.
"""

from pydantic import BaseModel, Field


class Persona(BaseModel):
    """
    User persona - 3 plain text blocks for system prompt injection.
    
    These evolve slowly over time as cognitions update.
    """
    
    personal_profile: str = Field(
        description="1-2 paragraphs describing who the user is: core identity, values, beliefs, approach to life and work"
    )
    
    communication_preferences: str = Field(
        description="How AI should communicate with the user: tone, style, format preferences, response expectations"
    )
    
    professional_profile: str = Field(
        description="Professional identity: skills, expertise, current projects, objectives, interests, technical preferences"
    )
