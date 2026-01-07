# k3cacheable

[![Action-CI](https://github.com/pykit3/k3cacheable/actions/workflows/python-package.yml/badge.svg)](https://github.com/pykit3/k3cacheable/actions/workflows/python-package.yml)
[![Documentation Status](https://readthedocs.org/projects/k3cacheable/badge/?version=stable)](https://k3cacheable.readthedocs.io/en/stable/?badge=stable)
[![Package](https://img.shields.io/pypi/pyversions/k3cacheable)](https://pypi.org/project/k3cacheable)

Cache data which access frequently.

k3cacheable is a component of [pykit3](https://github.com/pykit3) project: a python3 toolkit set.

## Installation

```bash
pip install k3cacheable
```

## Quick Start

```python
import k3cacheable

# LRU cache with capacity=10, timeout=60 seconds
c = k3cacheable.LRU(10, 60)
c['key'] = 'val'
val = c['key']

# Function decorator
@k3cacheable.cache('my_cache', capacity=100, timeout=60)
def get_data(param):
    return expensive_operation(param)
```

## API Reference

::: k3cacheable

## License

The MIT License (MIT) - Copyright (c) 2015 Zhang Yanpo (张炎泼)
