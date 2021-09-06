# DO NOT EDIT!!! built with `python _building/build_setup.py`
import setuptools
setuptools.setup(
    name="k3cacheable",
    packages=["k3cacheable"],
    version="0.1.0",
    license='MIT',
    description='Cache data which access frequently.',
    long_description="# k3cacheable\n\n[![Action-CI](https://github.com/pykit3/k3cacheable/actions/workflows/python-package.yml/badge.svg)](https://github.com/pykit3/k3cacheable/actions/workflows/python-package.yml)\n[![Build Status](https://travis-ci.com/pykit3/k3cacheable.svg?branch=master)](https://travis-ci.com/pykit3/k3cacheable)\n[![Documentation Status](https://readthedocs.org/projects/k3cacheable/badge/?version=stable)](https://k3cacheable.readthedocs.io/en/stable/?badge=stable)\n[![Package](https://img.shields.io/pypi/pyversions/k3cacheable)](https://pypi.org/project/k3cacheable)\n\nCache data which access frequently.\n\nk3cacheable is a component of [pykit3] project: a python3 toolkit set.\n\n\nCache data which access frequently.\n\n\n\n\n# Install\n\n```\npip install k3cacheable\n```\n\n# Synopsis\n\n```python\n\nimport k3cacheable\nimport time\n\n# create a `LRU`, capacity:10 timeout:60\nc = k3cacheable.LRU(10, 60)\n\n# set value like the `dict`\nc['key'] = 'val'\n\n# get value like the `dict`\n# if item timeout, delete it and raise `KeyError`\n# if item not exist, raise `KeyError`\ntry:\n    val = c['key']\nexcept KeyError:\n    print('key error')\n\ncache_data = {\n    'key1': 'val_1',\n    'key2': 'val_2',\n}\n\n# define the function with a decorator\n@k3cacheable.cache('cache_name', capacity=100, timeout=60,\n                 is_deepcopy=False, mutex_update=False)\ndef get_data(param):\n    return cache_data.get(param, '')\n\n# call `get_data`, if item has not been cached, cache the return value\ndata = get_data('key1')\n\n# call `get_data` use the same param, data will be got from cache\ntime.sleep(1)\ndata = get_data('key1')\n\n# if item timeout, when call `get_data`, cache again\ntime.sleep(1)\ndata = get_data('key1')\n\n# define a method with a decorator\nclass MethodCache(object):\n\n    @k3cacheable.cache('method_cache_name', capacity=100, timeout=60,\n                     is_deepcopy=False, mutex_update=False)\n    def get_data(self, param):\n        return cache_data.get(param, '')\n\nmm = MethodCache()\ndata = mm.get_data('key2')\n\n```\n\n#   Author\n\nZhang Yanpo (张炎泼) <drdr.xp@gmail.com>\n\n#   Copyright and License\n\nThe MIT License (MIT)\n\nCopyright (c) 2015 Zhang Yanpo (张炎泼) <drdr.xp@gmail.com>\n\n\n[pykit3]: https://github.com/pykit3",
    long_description_content_type="text/markdown",
    author='Zhang Yanpo',
    author_email='drdr.xp@gmail.com',
    url='https://github.com/pykit3/k3cacheable',
    keywords=['python', 'cache'],
    python_requires='>=3.0',

    install_requires=['msgpack>=1.0.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
    ] + ['Programming Language :: Python :: 3'],
)
