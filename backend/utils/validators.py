"""
Validators
Input validation helper functions.
"""
import re
from typing import Optional

def is_valid_url(url: str) -> bool:
    """Validate if a string is a valid URL."""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))

def is_valid_email(email: str) -> bool:
    """Validate if a string is a valid email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_uuid(uuid_str: str) -> bool:
    """Validate if a string is a valid UUID."""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_str.lower()))

def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input by removing potentially dangerous characters."""
    # Remove null bytes
    text = text.replace('\x00', '')
    # Truncate to max length
    return text[:max_length]
