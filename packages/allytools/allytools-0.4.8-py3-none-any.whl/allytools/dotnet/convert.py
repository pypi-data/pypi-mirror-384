from __future__ import annotations
from typing import Any, Optional
from datetime import datetime

"""
Convert a .NET System.DateTime (or string) into a Python datetime.
Falls back to None if not parseable.
"""
def to_py_datetime(dt: Any) -> Optional[datetime]:
    if dt is None:
        return None
    try:
        s = str(dt.ToString("o"))
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        pass

    if isinstance(dt, datetime):
        return dt
    # Last resort: parse str(dt)
    try:
        return datetime.fromisoformat(str(dt))
    except Exception:
        return None