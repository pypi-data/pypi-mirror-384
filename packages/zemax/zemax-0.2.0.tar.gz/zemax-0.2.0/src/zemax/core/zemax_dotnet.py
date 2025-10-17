import clr, ctypes
import numpy as np
# noinspection PyUnresolvedReferences
clr.AddReference("System.Runtime.InteropServices")
# noinspection PyUnresolvedReferences
from System.Runtime.InteropServices import GCHandle, GCHandleType
# noinspection PyUnresolvedReferences
from System import Array  # if you need type hints; optional

def _to_numpy(data, ctype, dtype, copy: bool = True):
    if data is None:
        raise ValueError("data is None")
    n = len(data)
    if n == 0:
        return np.empty(0, dtype=dtype)
    handle = GCHandle.Alloc(data, GCHandleType.Pinned)
    try:
        addr = handle.AddrOfPinnedObject().ToInt64()
        buf = (ctype * n).from_address(addr)
        arr = np.frombuffer(buf, dtype=dtype, count=n)
        return arr.copy() if copy else arr  # copy for safety after unpinning
    finally:
        if handle.IsAllocated:
            handle.Free()

def double_to_numpy(data, copy: bool = True) -> np.ndarray:
    return _to_numpy(data, ctypes.c_double, np.float64, copy)

def long_to_numpy(data, copy: bool = True) -> np.ndarray:
    return _to_numpy(data, ctypes.c_longlong, np.int64, copy)
