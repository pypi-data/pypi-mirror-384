from typing import Any
import numpy as np

def as_npz(x: Any) -> np.ndarray:
    if isinstance(x, str):
        return np.array(x, dtype=np.str_)
    try:
        arr = np.asarray(x)
    except (TypeError, ValueError):
        return np.array(x, dtype=object)
    if np.issubdtype(arr.dtype, np.number): # Numeric → keep numeric and contiguous
        return np.ascontiguousarray(arr)
    if arr.dtype.kind in ("U", "S"): # String / Unicode arrays → keep as-is
        return arr
    return np.array(x, dtype=object) # Everything else → stores as an object array


