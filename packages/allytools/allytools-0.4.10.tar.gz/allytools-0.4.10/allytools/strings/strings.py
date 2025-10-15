from typing import Any, Optional
import re
FALSEY_TOKENS = {"", "none", "null", "nan", "n/a", "-"}

"""Normalizes a label-like value: trims, collapses whitespace, and returns None for empty/falsey tokens"""
def clean_str(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    s_norm = " ".join(s.split())  # collapse multiple spaces/tabs/newlines
    return None if s_norm.lower() in FALSEY_TOKENS else s_norm

"""Makes a filename-safe slug: replaces / with -, strips, removes illegal chars, and collapses repeated _."""
def sanitize(st: str) -> str:
    st = st.replace('/', '-').strip()
    st = re.sub(r'[^\w\-.]+', '_', st)   # keep letters/digits/_-. only
    st = re.sub(r'_{2,}', '_', st)       # collapse multiple underscores
    return st
