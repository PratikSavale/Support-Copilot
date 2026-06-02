import pytest
from datetime import datetime
import uuid
from utils.formatters import format_uuid, format_timestamp, truncate_text, sanitize_for_json
from utils.validators import is_valid_url, is_valid_email, is_valid_uuid, sanitize_input

def test_formatters():
    uid = uuid.uuid4()
    assert format_uuid(uid) == str(uid)
    assert format_uuid("not-a-uuid") == "not-a-uuid"

    dt = datetime(2025, 1, 1, 12, 0, 0)
    assert format_timestamp(dt) == dt.isoformat()
    assert format_timestamp(None) is None

    assert truncate_text("hello world", 5) == "hello..."
    assert truncate_text("hello", 10) == "hello"

    assert sanitize_for_json(uid) == str(uid)
    assert sanitize_for_json(dt) == dt.isoformat()
    assert sanitize_for_json({"key": "value"}) == {"key": "value"}

def test_validators():
    assert is_valid_url("https://example.com") is True
    assert is_valid_url("not-a-url") is False

    assert is_valid_email("test@example.com") is True
    assert is_valid_email("test@") is False

    uid_str = str(uuid.uuid4())
    assert is_valid_uuid(uid_str) is True
    assert is_valid_uuid("not-a-uuid") is False

    assert sanitize_input("hello\x00world", max_length=100) == "helloworld"
    assert sanitize_input("a" * 15, max_length=10) == "a" * 10
