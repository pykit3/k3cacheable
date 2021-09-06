#!/usr/bin/env python
# coding: utf-8

import copy
import logging
import threading
import time
import msgpack

logger = logging.getLogger(__name__)
_lock_mutex_update = threading.RLock()


class LRU(object):
    """
    `LRU` contain `__getitem__` and `__setitem__`,
    so can get value and set value like `dict`
    `LRU[key]`: return the item of `LRU` with `key`.
    If item exist, move it to the tail to avoid to be cleaned.
    Raise a `KeyError` if `key` is not in `LRU` or has been timeout.
    `LRU[key] = value`: set `LRU[key]` to `value` and
    move it to tail of `LRU` to avoid to be cleaned.

    If size of `LRU` is greater than `capacity` * 1.5,
    clean items from head until size is equal to `capacity`.
    
    .. highlight:: python
    .. code-block:: python

        import k3cacheable

        # create `LRU`, capacity:10, timeout:60
        lru = k3cacheable.LRU(10, 60)

        # set `lru['a']` to 'val_a'
        lru['a'] = 'val_a'

        sleep_time = 30
        try:
            time.sleep(sleep_time)
            val = lru['a']
            # if sleep_time <= timeout of LRU, return the value
            # if sleep_time > timeout of LRU, delete it and raise a `KeyError`
        except KeyError as e:
            print('key not in lru')

        try:
            val = lru['b']
            # if item not in lru, raise a `KeyError`
        except KeyError as e:
            print('key not in lru')
        ...
    """
    def __init__(self, capacity, timeout=60):
        """
        Least Recently Used Cache.
        :param capacity: capacity of `LRU`, when the size of `LRU` is greater than `capacity` * 1.5,
        clean old items until the size is equal to `capacity`
        :param timeout: max cache time of item, unit is second, default is 60
        """
        self.lock = threading.RLock()
        self.capacity = capacity
        self.cleanup_threshold = int(capacity * 1.5)
        self.timeout = timeout
        self.size = 0
        self.items = {}
        self.head = {'next': None, 'pre': None}
        self.tail = self.head

    def __getitem__(self, key):

        with self.lock:
            now = int(time.time())
            item = self.items[key]

            if now > item['tm'] + self.timeout:
                self._del_item(item)
                raise KeyError('{k} is timeout'.format(k=key))

            self._move_to_tail(item)

            return item['val']

    def __setitem__(self, key, val):

        with self.lock:
            if key in self.items:
                item = self.items[key]
                item['val'] = val
                item['tm'] = int(time.time())

                self._move_to_tail(item)

            else:
                self.items[key] = {'key': key,
                                   'val': val,
                                   'pre': None,
                                   'next': None,
                                   'tm': int(time.time())}

                self._move_to_tail(self.items[key])

                self.size += 1

                if self.size > self.cleanup_threshold:
                    self._cleanup()

    def _remove_item(self, item):

        item['pre']['next'] = item['next']
        if item['next'] is not None:
            item['next']['pre'] = item['pre']
        else:
            self.tail = item['pre']

    def _move_to_tail(self, item):

        if item['pre'] is not None:
            self._remove_item(item)

        self.tail['next'] = item
        item['pre'] = self.tail
        item['next'] = None
        self.tail = item

    def _del_item(self, item):

        del self.items[item['key']]
        self._remove_item(item)
        self.size -= 1

    def _cleanup(self):

        while self.size > self.capacity:
            item = self.head['next']
            self._del_item(item)


class Cacheable(object):

    def __init__(self, capacity=1024 * 4, timeout=60,
                    is_deepcopy=True, is_pack=False, mutex_update=False):
        """
        Create a `LRU` object, all items will be cached in it.
        :param capacity: for create `LRU` object, default is 1024 * 4
        :param timeout: for create `LRU` object, default is 60, unit is second
        :param is_deepcopy: `cacheable.cache` return a decorator that use `is_deepcopy`
        to return deepcopy or reference of cached item.
        `True`: return deepcopy of cached item
        `False`: return reference of cached item

        :param is_pack: return a decorator that use `is_pack`
        to return `msgpack.pack` item.
        `True`: return `msgpack.pack` of cached item
        `False`: return reference of cached item

        :param mutex_update:  allows only one thread to update the cache item.
        Default is `False`.
        `True`: mutex update
        `False`: concurrently update

        """
        self.lru = LRU(capacity, timeout)
        self.is_deepcopy = is_deepcopy
        self.is_pack = is_pack
        self.mutex_update = mutex_update

    def _arg_str(self, args, argkv):

        argkv = [(k, v) for k, v in list(argkv.items())]
        argkv.sort()

        return str([args, argkv])

    def _cache_wrapper(self, fun):

        def func_wrapper(*args, **argkv):

            val = None
            generate_key = self._arg_str(args, argkv)

            try:
                val = self.lru[generate_key]
            except KeyError:
                if self.mutex_update:
                    with _lock_mutex_update:
                        try:
                            val = self.lru[generate_key]
                        except KeyError:
                            val = fun(*args, **argkv)
                            if self.is_pack:
                                val = msgpack.packb(val, use_bin_type=True)
                            self.lru[generate_key] = val
                else:
                    val = fun(*args, **argkv)
                    if self.is_pack:
                        val = msgpack.packb(val, use_bin_type=True)
                    self.lru[generate_key] = val

            if self.is_pack:
                val = msgpack.unpackb(val, raw=False)

            if self.is_deepcopy:
                return copy.deepcopy(val)
            else:
                return val

        return func_wrapper


caches = {}


def cache(name, capacity=1024 * 4, timeout=60,
        is_deepcopy=True, is_pack=False, mutex_update=False):
    """
    If not exist, create a `cacheable.Cacheable` and save it, else use exist one.
    :param name: for distinguishing different `cacheable.Cacheable`
    :param capacity: used as `capacity` of `cacheable.Cacheable`
    :param timeout: used as `timeout` of `cacheable.Cacheable`
    :param is_deepcopy: used as 's_deepcopy'of 'acheable.Cacheable'
    :param mutex_update: used as 'utex_update'of 'acheable.Cacheable'
    :return: A decorator function that it checks whether the data has been cached, if not or has been timeout,cache and
    return the data.

    .. highlight:: python
    .. code-block:: python

        import k3cacheable

        need_cache_data_aa = {'key': 'val_aa'}
        need_cache_data_bb = {'key': 'val_bb'}

        #use different `name` create two objects, they don't have any relation.
        @k3cacheable.cache('name_aa', capacity=100, timeout=60, is_deepcopy=False, mutex_update=False)
        def cache_aa(param):
            return need_cache_data_aa.get(param, '')

        @k3cacheable.cache('name_bb', capacity=100, timeout=60, is_deepcopy=False, mutex_update=False)
        def cache_bb(param):
            return need_cache_data_bb.get(param, '')
        ...

    """
    c = caches.get(name)
    if c is None:
        c = Cacheable(capacity=capacity, timeout=timeout,
                      is_deepcopy=is_deepcopy, mutex_update=mutex_update)
        caches[name] = c

    return c._cache_wrapper
