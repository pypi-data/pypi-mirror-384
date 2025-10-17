"""
Prompt management system for loading and rendering prompts from YAML templates.

This module provides a centralized way to manage prompts, enabling:
- Version control of prompts separate from code
- Easy A/B testing of different prompts
- Hot-reload without code changes
- Template rendering with variables
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """A loaded prompt template with metadata."""
    
    name: str
    version: str
    temperature: float
    system_instruction: str
    output_schema: Optional[str] = None
    variables: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None


class PromptLoader:
    """
    Load and manage prompt templates from YAML files.
    
    Usage:
        loader = PromptLoader()
        prompt = loader.load("observation_extraction")
        rendered = loader.render(prompt.system_instruction, conversation_text="...")
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the prompt loader.
        
        Args:
            templates_dir: Directory containing prompt YAML files
                          (defaults to rebrain/prompts/templates/)
        """
        if templates_dir is None:
            # Default to templates/ directory relative to this file
            templates_dir = Path(__file__).parent / "templates"
        
        self.templates_dir = Path(templates_dir)
        self._cache: Dict[str, PromptTemplate] = {}
    
    def load(self, prompt_name: str, use_cache: bool = True) -> PromptTemplate:
        """
        Load a prompt template from YAML file.
        
        Args:
            prompt_name: Name of the prompt (without .yaml extension)
            use_cache: Use cached version if available (default: True)
        
        Returns:
            PromptTemplate object with loaded data
        
        Raises:
            FileNotFoundError: If prompt file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        # Check cache
        if use_cache and prompt_name in self._cache:
            return self._cache[prompt_name]
        
        # Load from file
        prompt_file = self.templates_dir / f"{prompt_name}.yaml"
        
        if not prompt_file.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {prompt_file}\n"
                f"Available prompts: {self.list_available_prompts()}"
            )
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Create template object
        template = PromptTemplate(
            name=data.get("name", prompt_name),
            version=data.get("version", "1.0"),
            temperature=data.get("temperature", 0.1),
            system_instruction=data.get("system_instruction", ""),
            output_schema=data.get("output_schema"),
            variables=data.get("variables"),
            metadata=data.get("metadata"),
        )
        
        # Cache it
        self._cache[prompt_name] = template
        
        return template
    
    def render(self, template_text: str, **kwargs) -> str:
        """
        Render a template string with variables.
        
        Simple variable substitution using Python string formatting.
        For more complex templating, could use Jinja2.
        
        Args:
            template_text: Template string with {variable} placeholders
            **kwargs: Variables to substitute
        
        Returns:
            Rendered string with variables substituted
        """
        try:
            return template_text.format(**kwargs)
        except KeyError as e:
            raise ValueError(
                f"Missing required variable in template: {e}\n"
                f"Provided variables: {list(kwargs.keys())}"
            )
    
    def list_available_prompts(self) -> list[str]:
        """
        List all available prompt templates.
        
        Returns:
            List of prompt names (without .yaml extension)
        """
        if not self.templates_dir.exists():
            return []
        
        return [
            f.stem for f in self.templates_dir.glob("*.yaml")
        ]
    
    def clear_cache(self):
        """Clear the template cache to force reload."""
        self._cache.clear()

