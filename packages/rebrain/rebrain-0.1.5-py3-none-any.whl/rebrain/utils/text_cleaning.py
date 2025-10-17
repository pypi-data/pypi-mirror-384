"""Text cleaning utilities for preprocessing."""

import re


def remove_code_blocks(text: str) -> str:
    """
    Remove markdown code blocks and replace with placeholders.
    
    Handles multiple formats:
    - Closed blocks: ```language\ncode```
    - Unclosed blocks: ```language\ncode (to end of text)
    - Multiple passes to ensure all removed
    
    Args:
        text: Input text containing potential code blocks
        
    Returns:
        Text with code blocks replaced by placeholders
    """
    # Multiple passes to catch nested or edge cases
    max_iterations = 5
    for _ in range(max_iterations):
        original_text = text
        
        # Pattern 1: Closed code blocks (greedy to catch long blocks)
        text = re.sub(r'```[^\n]*\n[\s\S]*?```', '[Code redacted]', text)
        
        # Pattern 2: Code blocks without newline after opening
        text = re.sub(r'```[^\n]*[\s\S]*?```', '[Code redacted]', text)
        
        # Pattern 3: Unclosed code blocks (``` to end of line/text)
        # This catches cases where ``` opens but never closes
        text = re.sub(r'```[^\n]*\n[\s\S]+$', '[Code redacted]', text)
        text = re.sub(r'```[^\n]+$', '[Code redacted]', text)
        
        # If no changes, we're done
        if text == original_text:
            break
    
    # Also remove long inline code (>100 chars suggests code)
    def replace_inline(match):
        content = match.group(1)
        if len(content) > 100:
            return '[Inline code redacted]'
        return match.group(0)
    
    text = re.sub(r'`([^`]{100,})`', replace_inline, text)
    
    # Final cleanup: remove any remaining triple backticks
    text = text.replace('```', '')
    
    return text

