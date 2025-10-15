"""Common utility functions."""

from datetime import datetime
from typing import Optional

import tiktoken


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Count tokens in text.

    Args:
        text: Text to count
        encoding_name: Tokenizer encoding name

    Returns:
        Number of tokens
    """
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def format_timestamp(timestamp: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp for display.

    Args:
        timestamp: Timestamp to format (default: now)
        fmt: Format string

    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime(fmt)

