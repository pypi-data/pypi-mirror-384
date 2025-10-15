"""
Unified GenAI client for all Gemini API interactions.

This module provides a centralized client for:
- Structured output generation (JSON with Pydantic schemas)
- Free-text generation
- Embeddings with automatic batching and rate limiting

All configuration is loaded from centralized settings (config/settings.py).
"""

import json
import logging
import time
from typing import Any, List

# ⚠️  CRITICAL: Use 'google-genai' package (modern), NOT 'google-generativeai' (deprecated)!
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from pydantic import BaseModel

from config.settings import settings

logger = logging.getLogger(__name__)


class GenAIClient:
    """
    Unified client for all Gemini API interactions.
    
    Features:
    - Centralized configuration from settings
    - Rate limiting and retry logic
    - Support for structured (Pydantic) and free-text generation
    - Embedding with automatic batching
    """

    def __init__(
        self,
        system_instruction: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize the GenAI client.

        Args:
            system_instruction: System prompt to guide model behavior (optional)
            model: Gemini model to use (defaults to GEMINI_MODEL from .env)
            api_key: API key (defaults to GEMINI_API_KEY from .env)
        """
        import os
        
        # Force use of GEMINI_API_KEY from .env, ignore GOOGLE_API_KEY from shell
        # (google.genai library prefers GOOGLE_API_KEY if both exist)
        if 'GOOGLE_API_KEY' in os.environ:
            del os.environ['GOOGLE_API_KEY']  # Remove stale key from shell environment
        self.system_instruction = system_instruction
        self.model = model or settings.gemini_model  # Now loaded from .env
        self.api_key = api_key or settings.gemini_api_key  # Loaded from .env
        
        # Create client with API key only
        self.client = genai.Client(api_key=self.api_key, vertexai=False)

    def generate_structured(
        self,
        content: str,
        response_model: type[BaseModel],
        temperature: float = 0.1,
        max_retries: int = 3,
        retry_delays: List[float] = None,
    ) -> BaseModel:
        """
        Generate structured content using a Pydantic model with retry logic.

        Args:
            content: The input text content for the model
            response_model: Pydantic model class for structured output
            temperature: Generation temperature (default: 0.1)
            max_retries: Maximum number of retries on rate limit (default: 3)
            retry_delays: List of delays in seconds for each retry (default: [20, 40, 60])

        Returns:
            Instance of the response_model with parsed response
            
        Raises:
            Exception: If all retries fail
        """
        if retry_delays is None:
            retry_delays = [20, 40, 60]
        
        # Get JSON schema from Pydantic model
        schema_dict = response_model.model_json_schema()
        
        # Flatten schema (remove $ref and $defs) for Gemini compatibility
        schema_dict = self._flatten_schema(schema_dict)
        
        schema = types.Schema(**schema_dict)

        # Create generation config
        generation_config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
        )

        # Retry loop
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                # Generate content
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=content,
                    config=generation_config,
                )

                # Parse and validate with Pydantic
                if response.parsed is None:
                    # Fallback to empty response
                    return response_model()
                
                return response_model(**response.parsed)
                
            except ClientError as e:
                last_error = e
                error_code = getattr(e, 'code', None)
                error_str = str(e)
                
                # Check if it's a rate limit error (429)
                if error_code == 429 or '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    if attempt < max_retries:
                        delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                        logger.warning(f"Rate limit hit, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} retries")
                        raise
                
                # Check if it's a service unavailable error (503)
                elif error_code == 503 or '503' in error_str or 'UNAVAILABLE' in error_str:
                    if attempt < max_retries:
                        delay = 3  # Short delay for service unavailability
                        logger.warning(f"Service unavailable (503), retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Service unavailable after {max_retries} retries")
                        raise
                
                else:
                    # Non-retryable error, raise immediately
                    logger.error(f"API error: {e}")
                    raise
                    
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")
                raise
        
        # If we get here, all retries failed
        raise last_error

    def generate_json(
        self, content: str, json_schema: str | dict[str, Any], temperature: float = 0.1
    ) -> dict[str, Any]:
        """
        Generate structured content based on JSON schema (dict or string).

        Args:
            content: The input text content for the model
            json_schema: The JSON schema as string or dict for structured output
            temperature: Generation temperature (default: 0.1)

        Returns:
            Parsed response as a dictionary
        """
        # Handle both string and dict schema inputs
        if isinstance(json_schema, str):
            schema_dict = json.loads(json_schema)
        else:
            schema_dict = json_schema

        schema = types.Schema(**schema_dict)

        # Create generation config
        generation_config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
        )

        # Generate content
        response = self.client.models.generate_content(
            model=self.model,
            contents=content,
            config=generation_config,
        )

        # Return the parsed response
        return response.parsed  # type: ignore[return-value]

    def generate_text(
        self, content: str, temperature: float = 0.0, max_output_tokens: int = 2000
    ) -> str:
        """
        Generate free-text content based on the input.

        Args:
            content: The input text content for the model
            temperature: Controls randomness (0.0-1.0, default 0.0)
            max_output_tokens: Maximum tokens to generate (default 2000)

        Returns:
            Generated text as a string
        """
        # Create generation config
        generation_config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        # Generate content
        response = self.client.models.generate_content(
            model=self.model,
            contents=content,
            config=generation_config,
        )

        # Return the text response
        return response.text  # type: ignore[return-value]

    def embed(
        self,
        texts: List[str],
        batch_size: int | None = None,
        rate_delay: float | None = None,
        verbose: bool = False,
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts with automatic batching.

        Args:
            texts: List of text strings to embed
            batch_size: Batch size (must be provided by caller from config)
            rate_delay: Delay between batches in seconds (must be provided by caller from config)
            verbose: Print progress (default: False)

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        if batch_size is None or rate_delay is None:
            raise ValueError("batch_size and rate_delay must be provided (load from config)")
        
        # Use the provided values - NO DEFAULTS!
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            
            if verbose:
                batch_num = (i // batch_size) + 1
                total_batches = (len(texts) + batch_size - 1) // batch_size
                print(f"Embedding batch {batch_num}/{total_batches}...", end=" ", flush=True)
            
            # Call embedding API
            result = self.client.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=batch,
                config=types.EmbedContentConfig(
                    output_dimensionality=settings.gemini_embedding_dimension
                ),
            )
            
            # Extract embeddings
            for embedding_obj in result.embeddings:
                all_embeddings.append(embedding_obj.values)
            
            if verbose:
                print("✓")
            
            # Rate limiting delay (skip on last batch)
            if i + batch_size < len(texts):
                time.sleep(rate_delay)
        
        return all_embeddings

    def _flatten_schema(self, schema: dict) -> dict:
        """
        Flatten JSON schema by removing $ref and inlining $defs.
        
        Gemini's types.Schema doesn't support $ref, so we need to inline all definitions.
        """
        # Remove schema metadata that Gemini doesn't need
        SCHEMA_METADATA = ["$defs", "title", "$schema", "additionalProperties"]
        
        # If there are no $defs, just clean and return
        if "$defs" not in schema:
            return {k: v for k, v in schema.items() if k not in SCHEMA_METADATA}
        
        defs = schema.get("$defs", {})
        
        def resolve_refs(obj, is_definition_root=False):
            """Recursively resolve $ref in schema."""
            if isinstance(obj, dict):
                if "$ref" in obj:
                    # Extract definition name from ref like "#/$defs/Personal*"
                    ref_path = obj["$ref"]
                    if ref_path.startswith("#/$defs/"):
                        def_name = ref_path.split("/")[-1]
                        if def_name in defs:
                            # Recursively resolve the definition (mark as definition root)
                            return resolve_refs(defs[def_name].copy(), is_definition_root=True)
                    return obj
                else:
                    # Recursively process all values
                    result = {}
                    for k, v in obj.items():
                        # Only remove schema metadata at definition root, not in properties
                        if is_definition_root and k in SCHEMA_METADATA:
                            continue
                        elif not is_definition_root and k in ["$schema"]:
                            continue
                        else:
                            result[k] = resolve_refs(v, is_definition_root=False)
                    return result
            elif isinstance(obj, list):
                return [resolve_refs(item, is_definition_root=False) for item in obj]
            else:
                return obj
        
        # Start with the main schema (excluding $defs and other schema metadata)
        flattened = {}
        for k, v in schema.items():
            if k not in SCHEMA_METADATA:
                flattened[k] = resolve_refs(v, is_definition_root=False)
        return flattened

