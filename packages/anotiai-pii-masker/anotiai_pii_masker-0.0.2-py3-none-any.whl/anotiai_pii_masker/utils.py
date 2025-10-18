"""
Utility functions for the AnotiAI PII Masker package.
"""
import json
from typing import Any, Dict

def count_tokens(data: Any) -> int:
    """
    Calculates the token count for various data types based on character length.

    - For strings, it's the character count.
    - For dictionaries or lists, it's the character count of the JSON representation.
    - For other types, it's the character count of their string representation.

    Args:
        data: The data to measure (e.g., text, pii_map).

    Returns:
        The calculated token count.
    """
    if isinstance(data, str):
        return len(data)
    if isinstance(data, (dict, list)):
        try:
            return len(json.dumps(data))
        except TypeError:
            return len(str(data))  # Fallback for non-serializable objects
    return len(str(data))
