"""
Test OpenAI Structured Outputs with our Pydantic schemas.

OpenAI's response_format parameter accepts Pydantic models directly:
https://platform.openai.com/docs/guides/structured-outputs

This test validates that our existing schemas (Observation, Learning) 
work seamlessly with OpenAI's API.
"""

import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from rebrain.schemas.observation import Observation, ObservationExtraction, Category, PrivacyLevel
from rebrain.schemas.learning import Learning, LearningSynthesis, ConfidenceLevel
from datetime import datetime

# Load environment variables
assert load_dotenv(find_dotenv())


def test_observation_extraction():
    """Test that OpenAI can extract Observation using our Pydantic schema."""
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Sample conversation text
    conversation = """
    User: I'm working on a Python project and struggling with async/await patterns.
    Assistant: Async/await in Python allows you to write concurrent code. The key is understanding event loops.
    User: How do I handle multiple API calls efficiently?
    Assistant: Use asyncio.gather() to run multiple coroutines concurrently...
    """
    
    prompt = f"""Extract a single dominant observation from this conversation.

Conversation:
{conversation}

Focus on:
- The main technical concept discussed
- Relevant keywords (lowercase-kebab-case)
- Concrete entities (Title Case: Python, asyncio)
- Categorize as technical/professional/personal
- Privacy level: low/medium/high
"""
    
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You extract observations from conversations."},
                {"role": "user", "content": prompt}
            ],
            response_format=Observation,
        )
        
        observation = completion.choices[0].message.parsed
        
        print("✅ OpenAI Structured Output - Observation")
        print("-" * 60)
        print(f"Title: {observation.title}")
        print(f"Category: {observation.category}")
        print(f"Privacy: {observation.privacy}")
        print(f"Keywords: {', '.join(observation.keywords)}")
        print(f"Entities: {', '.join(observation.entities)}")
        print(f"\nContent:\n{observation.content}")
        print("-" * 60)
        
        # Validate structure
        assert isinstance(observation, Observation)
        assert observation.title
        assert observation.content
        assert observation.category in [c.value for c in Category]
        assert observation.privacy in [p.value for p in PrivacyLevel]
        
        print("✅ All validations passed!")
        return observation
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


def test_learning_synthesis():
    """Test that OpenAI can synthesize Learning using our Pydantic schema."""
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Sample observations cluster
    observations_summary = """
    Observation 1: User learning about Python async/await patterns
    Observation 2: User implementing asyncio for API calls
    Observation 3: User debugging event loop issues in Python
    Observation 4: User optimizing concurrent requests with gather()
    """
    
    prompt = f"""Synthesize a learning from these related observations:

{observations_summary}

Create a self-contained learning that captures the pattern or insight.
Include keywords and entities, categorize appropriately.
Confidence should be HIGH (4 observations show consistent pattern).
"""
    
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You synthesize learnings from observation clusters."},
                {"role": "user", "content": prompt}
            ],
            response_format=Learning,
        )
        
        learning = completion.choices[0].message.parsed
        
        print("\n✅ OpenAI Structured Output - Learning")
        print("-" * 60)
        print(f"Title: {learning.title}")
        print(f"Category: {learning.category}")
        print(f"Confidence: {learning.confidence}")
        print(f"Keywords: {', '.join(learning.keywords)}")
        print(f"Entities: {', '.join(learning.entities)}")
        print(f"\nContent:\n{learning.content}")
        print("-" * 60)
        
        # Validate structure
        assert isinstance(learning, Learning)
        assert learning.title
        assert learning.content
        assert learning.confidence in [c.value for c in ConfidenceLevel]
        
        print("✅ All validations passed!")
        return learning
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("Testing OpenAI Structured Outputs with Rebrain Schemas")
    print("=" * 60)
    print()
    
    # Test 1: Observation Extraction
    observation = test_observation_extraction()
    
    # Test 2: Learning Synthesis
    learning = test_learning_synthesis()
    
    print()
    print("=" * 60)
    print("🎉 All tests passed! OpenAI structured outputs work with our schemas.")
    print("=" * 60)
    print()
    print("✅ Compatible: Observation schema")
    print("✅ Compatible: Learning schema")
    print()
    print("Next steps:")
    print("  1. Add openai>=1.40.0 to dependencies")
    print("  2. Create LLMProvider abstraction (Gemini/OpenAI)")
    print("  3. Add --provider flag to pipeline CLI")
    print("  4. Update config.yaml with provider settings")

