from contextlib import contextmanager
from typing import Iterator, Optional, Any
from pathlib import Path
from core import  ZemaxStandAlone, ZemaxZMX

@contextmanager
def opticstudio(filepath: Optional[str | Path] = None,
                     save_on_close: bool = False) -> Iterator[tuple[ZemaxStandAlone, Any]]:
    with ZemaxStandAlone() as zs:
        if filepath is not None:
            with ZemaxZMX(zs, filepath, save_on_close=save_on_close):
                yield zs, zs.TheSystem
        else:
            yield zs, zs.TheSystem