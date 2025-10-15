from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, List

def prepare_filter_value(value: Any) -> Any:
    """Prepare a filter value for API request."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [prepare_filter_value(v) for v in value]
    return value
