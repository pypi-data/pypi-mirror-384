"""Persona output formatters."""


def generate_markdown(persona_dict: dict, metadata: dict) -> str:
    """
    Generate markdown representation of persona.
    
    Creates user-friendly markdown with:
    - Metadata header (date, model, stats)
    - Personal Profile section
    - Communication Preferences section  
    - Professional Profile section
    
    Args:
        persona_dict: Persona data with profile sections
        metadata: Generation metadata (generated_at, model, source_cognitions)
    
    Returns:
        Markdown formatted string
    """
    generated_at = metadata['generated_at'].split('T')[0]  # Date only
    model = metadata['model']
    source_count = metadata['source_cognitions']
    
    md = f"""# User Persona Information for AI

> **Generated:** {generated_at}  
> **Source:** {source_count} cognitions  
> **Model:** {model}

---

## Personal Profile

{persona_dict['personal_profile']}

---

## Communication Preferences

{persona_dict['communication_preferences']}

---

## Professional Profile

{persona_dict['professional_profile']}

---

*This persona is synthesized from chat history and should be used to personalize AI interactions.*
"""
    
    return md

