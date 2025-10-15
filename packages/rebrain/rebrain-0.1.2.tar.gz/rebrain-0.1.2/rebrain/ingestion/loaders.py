"""
Chat export loaders for different formats (JSONL, HTML, etc.).

Normalizes chat data into a consistent structure:
- timestamp
- role (user, assistant, system)
- text content
- source metadata
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

import json


class ChatLoader(ABC):
    """Base class for chat export loaders."""

    @abstractmethod
    def load(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Load and normalize chat data from file.

        Returns:
            List of normalized messages with keys: timestamp, role, text, source
        """
        pass


class JSONLChatLoader(ChatLoader):
    """Load chat exports from JSONL format."""

    def load(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load JSONL chat export."""
        messages = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    messages.append(self._normalize_message(data))
        return messages

    def _normalize_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize message to standard format."""
        # TODO: Implement format-specific normalization
        return {
            "timestamp": raw_message.get("timestamp"),
            "role": raw_message.get("role", "user"),
            "text": raw_message.get("text", ""),
            "source": raw_message.get("source", "unknown"),
        }


class ChatGPTJSONLoader(ChatLoader):
    """Load ChatGPT conversation exports from JSON format."""

    def __init__(self, include_roles: List[str] = None, exclude_content_types: List[str] = None):
        """
        Initialize ChatGPT JSON loader.

        Args:
            include_roles: List of roles to include (default: ["user", "assistant"])
            exclude_content_types: Content types to exclude (default: ["code", "thoughts", "reasoning_recap", "user_editable_context"])
        """
        self.include_roles = include_roles or ["user", "assistant"]
        self.exclude_content_types = exclude_content_types or [
            "code",
            "thoughts",
            "reasoning_recap",
            "user_editable_context",
            "system_error",
        ]

    def load(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Load ChatGPT JSON export and extract core conversation messages.

        Returns:
            List of normalized messages with keys: id, timestamp, role, text, conversation_id, conversation_title
        """
        with open(file_path, "r", encoding="utf-8") as f:
            conversations = json.load(f)

        all_messages = []
        for conv in conversations:
            messages = self._extract_messages_from_conversation(conv)
            all_messages.extend(messages)

        return all_messages

    def _extract_messages_from_conversation(self, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and normalize messages from a single conversation.

        Args:
            conversation: Raw conversation object

        Returns:
            List of normalized messages
        """
        conv_id = conversation.get("id")
        conv_title = conversation.get("title", "Untitled")
        mapping = conversation.get("mapping", {})

        messages = []
        for node_id, node in mapping.items():
            message = node.get("message")
            if not message:
                continue

            # Filter by role
            role = message.get("author", {}).get("role")
            if role not in self.include_roles:
                continue

            # Filter by content type
            content = message.get("content", {})
            content_type = content.get("content_type", "text")
            if content_type in self.exclude_content_types:
                continue

            # Extract text from parts
            parts = content.get("parts", [])
            if not parts:
                continue

            # Join all text parts (filter out non-strings)
            text_parts = [str(part) for part in parts if part and isinstance(part, str)]
            if not text_parts:
                continue

            text = "\n".join(text_parts).strip()
            if not text:
                continue

            # Create normalized message
            normalized = {
                "id": node_id,
                "conversation_id": conv_id,
                "conversation_title": conv_title,
                "timestamp": message.get("create_time"),
                "role": role,
                "text": text,
                "parent_id": node.get("parent"),
            }

            messages.append(normalized)

        # Sort by timestamp (nulls last)
        messages.sort(key=lambda x: x["timestamp"] if x["timestamp"] else float("inf"))

        return messages


class HTMLChatLoader(ChatLoader):
    """Load chat exports from HTML format (e.g., ChatGPT exports)."""

    def load(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load HTML chat export."""
        # TODO: Implement HTML parsing logic
        raise NotImplementedError("HTML loader not yet implemented")

