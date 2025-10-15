from __future__ import annotations

import base64
import json
from typing import Any


def apply_value(obj: Any, method_name: str, value: Any) -> None:
    """Apply a value to an object using a method name."""
    if value is not None:
        getattr(obj, method_name)(value)


def create_basic_auth_token(key: str, secret: str) -> str:
    """Create a basic authentication token."""
    token = base64.b64encode(f"{key}:{secret}".encode()).decode()
    return f"Basic {token}"


def get(target: Any, key: str, default_value: Any = "") -> Any:
    """Get a value from an object using a key."""
    if target is None:
        return default_value
    if isinstance(target, dict):
        return target.get(key, default_value)
    elif hasattr(target, key):
        return getattr(target, key) or default_value
    return default_value


def merge(a: dict[str, Any] | None, b: dict[str, Any] | None) -> dict[str, Any]:
    """Merge two dictionaries, handling None values."""
    if a is None and b is None:
        return {}
    if a is None:
        return b.copy() if b else {}
    if b is None:
        return a.copy() if a else {}
    return {**a, **b}


def to_json(data: dict[str, Any]) -> str:
    """Convert a dictionary to a JSON string."""
    try:
        return json.dumps(data)
    except Exception:
        return repr(data)
