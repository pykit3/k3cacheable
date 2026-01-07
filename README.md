# k3cacheable

[![Action-CI](https://github.com/pykit3/k3cacheable/actions/workflows/python-package.yml/badge.svg)](https://github.com/pykit3/k3cacheable/actions/workflows/python-package.yml)
[![Documentation Status](https://readthedocs.org/projects/k3cacheable/badge/?version=stable)](https://k3cacheable.readthedocs.io/en/stable/?badge=stable)
[![Package](https://img.shields.io/pypi/pyversions/k3cacheable)](https://pypi.org/project/k3cacheable)

Cache data which access frequently.

k3cacheable is a component of [pykit3] project: a python3 toolkit set.


Cache data which access frequently.




# Install

```
pip install k3cacheable
```

# Synopsis

```python

import k3cacheable
import time

# create a `LRU`, capacity:10 timeout:60
c = k3cacheable.LRU(10, 60)

# set value like the `dict`
c['key'] = 'val'

# get value like the `dict`
# if item timeout, delete it and raise `KeyError`
# if item not exist, raise `KeyError`
try:
    val = c['key']
except KeyError:
    print('key error')

cache_data = {
    'key1': 'val_1',
    'key2': 'val_2',
}

# define the function with a decorator
@k3cacheable.cache('cache_name', capacity=100, timeout=60,
                 is_deepcopy=False, mutex_update=False)
def get_data(param):
    return cache_data.get(param, '')

# call `get_data`, if item has not been cached, cache the return value
data = get_data('key1')

# call `get_data` use the same param, data will be got from cache
time.sleep(1)
data = get_data('key1')

# if item timeout, when call `get_data`, cache again
time.sleep(1)
data = get_data('key1')

# define a method with a decorator
class MethodCache(object):

    @k3cacheable.cache('method_cache_name', capacity=100, timeout=60,
                     is_deepcopy=False, mutex_update=False)
    def get_data(self, param):
        return cache_data.get(param, '')

mm = MethodCache()
data = mm.get_data('key2')

```

#   Author

Zhang Yanpo (张炎泼) <drdr.xp@gmail.com>

#   Copyright and License

The MIT License (MIT)

Copyright (c) 2015 Zhang Yanpo (张炎泼) <drdr.xp@gmail.com>


[pykit3]: https://github.com/pykit3