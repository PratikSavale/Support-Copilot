"""
Formatters
Utility functions for formatting data.
"""
from datetime import datetime
from typing import Any, Optional
import uuid

def format_uuid(value: Any) -> str:
    """Convert any value to UUID string."""
    if isinstance(value, uuid.UUID):
        return str(value)
    return str(value)

def format_timestamp(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO 8601 string."""
    if dt is None:
        return None
    return dt.isoformat()

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def sanitize_for_json(value: Any) -> Any:
    """Sanitize a value for JSON serialization."""
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value
