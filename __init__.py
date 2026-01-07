"""
Cache data which access frequently.

"""

# from .proc import CalledProcessError
# from .proc import ProcError

from importlib.metadata import version

__version__ = version("k3cacheable")

from .cacheable import (
    LRU,
    Cacheable,
    cache,
)

__all__ = [
    "LRU",
    "Cacheable",
    "cache",
]
