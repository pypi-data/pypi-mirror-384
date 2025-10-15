"""
Generic synthesizer for all AI processing stages.

with one unified interface.
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from rebrain.core import GenAIClient
from rebrain.prompts import PromptLoader

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class GenericSynthesizer:
    """
    Generic synthesizer for all AI processing stages.
    
    Unified interface: provide prompt template and output schema,
    synthesize any input to any output.
    """
    
    def __init__(self, prompt_template: str):
        """
        Initialize synthesizer with prompt template.
        
        Args:
            prompt_template: Name of prompt template to load (e.g., "observation_extraction")
        """
        self.prompt_loader = PromptLoader()
        self.prompt_template = self.prompt_loader.load(prompt_template)
        
        # Use model from prompt template metadata if available, otherwise default
        model = None
        if self.prompt_template.metadata and "model_recommendation" in self.prompt_template.metadata:
            model = self.prompt_template.metadata["model_recommendation"]
            logger.info(f"Using model from prompt template: {model}")
        
        self.client = GenAIClient(model=model)
    
    def synthesize(
        self,
        input_data: Any,
        output_schema: Type[T],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[T]:
        """
        Synthesize input data to output schema.
        
        Args:
            input_data: Input data (conversation, cluster, etc.)
            output_schema: Pydantic model for output
            context: Additional context for prompt
        
        Returns:
            Instance of output_schema or None if synthesis fails
        """
        # Format input for prompt
        formatted_input = self._format_input(input_data, context or {})
        
        # Build full prompt
        prompt_content = f"{self.prompt_template.system_instruction}\n\n{formatted_input}"
        
        try:
            # Call AI with structured output
            result = self.client.generate_structured(
                content=prompt_content,
                response_model=output_schema,
                temperature=self.prompt_template.temperature
            )
            
            return result
            
        except Exception as e:
            logger.debug(f"Synthesis error: {e}")
            return None
    
    async def synthesize_async(
        self,
        input_data: Any,
        output_schema: Type[T],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[T]:
        """
        Async version of synthesize - runs in thread pool.
        
        Args:
            input_data: Input data
            output_schema: Output Pydantic model
            context: Additional context
        
        Returns:
            Instance of output_schema or None
        """
        return await asyncio.to_thread(self.synthesize, input_data, output_schema, context)
    
    async def synthesize_batch_async(
        self,
        inputs: List[Any],
        output_schema: Type[T],
        max_concurrent: int = 20,
        context_fn: Optional[callable] = None,
        verbose: bool = True,
        request_delay: float = 0.5  # Delay between STARTING requests in seconds
    ) -> List[Optional[T]]:
        """
        Synthesize multiple inputs in parallel with proper rate limiting.
        
        The request_delay ensures tasks are STARTED with a delay between them,
        not just delayed within the semaphore.
        
        Args:
            inputs: List of input data
            output_schema: Output Pydantic model
            max_concurrent: Maximum concurrent calls
            context_fn: Function to generate context for each input (optional)
            verbose: Print progress
            request_delay: Delay between STARTING requests (default: 0.5s)
        
        Returns:
            List of synthesized outputs (same order as inputs)
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        start_lock = asyncio.Lock()
        last_start_time = [0.0]  # Mutable container for closure
        
        async def process_with_rate_limit(idx: int, input_data: Any) -> tuple:
            # Rate limiting: ensure delay between STARTING requests
            async with start_lock:
                if request_delay > 0:
                    elapsed = time.time() - last_start_time[0]
                    if elapsed < request_delay:
                        await asyncio.sleep(request_delay - elapsed)
                last_start_time[0] = time.time()
            
            # Now process with concurrency control
            async with semaphore:
                context = context_fn(input_data) if context_fn else None
                result = await self.synthesize_async(input_data, output_schema, context)
                return (idx, result)
        
        # Create tasks with proper rate limiting
        tasks = [process_with_rate_limit(i, inp) for i, inp in enumerate(inputs)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        results_list = []
        success_count = 0
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {idx} failed: {result}")
                results_list.append((idx, None))
            else:
                results_list.append(result)
                if result[1] is not None:
                    success_count += 1
        
        # Log summary
        if verbose:
            logger.info(f"Completed: {success_count}/{len(inputs)} successful")
        
        # Sort by original index
        results_list.sort(key=lambda x: x[0])
        outputs = [r[1] for r in results_list]
        
        return outputs
    
    def _format_input(self, input_data: Any, context: Dict[str, Any]) -> str:
        """
        Format input data for prompt.
        
        Override this method for custom formatting if needed.
        
        Args:
            input_data: Input data
            context: Additional context
        
        Returns:
            Formatted string for prompt
        """
        # Default: convert to string
        # Subclasses or callers can provide custom formatting
        if isinstance(input_data, dict):
            return self._format_dict(input_data)
        elif isinstance(input_data, list):
            return self._format_list(input_data)
        else:
            return str(input_data)
    
    def _format_dict(self, data: dict) -> str:
        """Format dictionary as key-value pairs."""
        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _format_list(self, data: list) -> str:
        """Format list as numbered items."""
        lines = []
        for i, item in enumerate(data, 1):
            lines.append(f"{i}. {item}")
        return "\n".join(lines)

