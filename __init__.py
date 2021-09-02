"""
Cache data which access frequently.

"""

# from .proc import CalledProcessError
# from .proc import ProcError

__version__ = "0.1.0"
__name__ = "k3cacheable"

from .cacheable import (
    LRU,
    Cacheable,
    cache,
)

__all__ = [
    'LRU',
    'Cacheable',
    'cache',
]
