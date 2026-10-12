import _thread
import threading
import time
import unittest
from unittest import mock

import k3cacheable


class TestLRU(unittest.TestCase):
    def _assert_lru_list(self, lru):
        size = lru.size
        item_head = lru.head
        item_tail = lru.tail
        for i in range(size):
            item_head = item_head["next"]
            item_tail = item_tail["pre"]

        self.assertIs(item_head, lru.tail)
        self.assertIs(item_tail, lru.head)

    def _assert_lru_items_order(self, lru, order_keys):
        item = lru.head["next"]
        lru_keys = []
        while item is not None:
            lru_keys.append(item["key"])
            item = item["next"]

        self.assertEqual(order_keys, lru_keys)

    @mock.patch("time.time")
    def test_lru_timeout(self, mock_time):
        cases = (
            ("k1", "v1", 3, True),
            ("k2", "v2", 1, False),
        )

        mock_time.return_value = 1000.0
        lru = k3cacheable.LRU(10, 2)
        for key, val, sleep_time, is_timeout in cases:
            lru[key] = val
            mock_time.return_value += sleep_time

            try:
                lru[key]
                self.assertFalse(is_timeout)

            except KeyError:
                self._assert_lru_list(lru)
                self.assertTrue(is_timeout)

    def test_lru_getitem(self):
        capacity = 4
        cases = (
            (3, [0, 1, 2], []),
            (4, [0, 1, 2, 3], []),
            (5, [0, 1, 2, 3, 4], []),
            (6, [0, 1, 2, 3, 4, 5], []),
            (7, [3, 4, 5, 6], [0, 1, 2]),
        )

        for insert_count, exist_items, cleanup_items in cases:
            lru = k3cacheable.LRU(capacity, 10)
            for i in range(insert_count):
                lru[i] = f"val{i}"

            for i in range(insert_count):
                try:
                    val = lru[i]
                    self.assertEqual(val, f"val{i}")
                    self.assertEqual(lru.tail["key"], i)
                    self.assertIn(i, exist_items)

                except KeyError:
                    self.assertIn(i, cleanup_items)

    def test_lru_setitem(self):
        capacity = 4
        cases = (
            (3, [0, 1, 2]),
            (4, [0, 1, 2, 3]),
            (5, [0, 1, 2, 3, 4]),
            (6, [0, 1, 2, 3, 4, 5]),
            # size of lru > capacity*1.5
            # clean items from head, until size=capacity
            (7, [3, 4, 5, 6]),
        )

        for insert_count, expect_order_keys in cases:
            lru = k3cacheable.LRU(capacity, 10)
            for i in range(insert_count):
                lru[i] = "val"
                self._assert_lru_list(lru)

            self._assert_lru_items_order(lru, expect_order_keys)

    def test_lru_capacity(self):
        cases = (
            (0, ((0, 0), (1, 0))),
            (1, ((1, 1), (2, 1))),
            (10, ((9, 9), (10, 10), (13, 13), (15, 15), (16, 10))),
        )

        for capacity, case in cases:
            for insert_count, expect_size in case:
                lru = k3cacheable.LRU(capacity, 60)
                for i in range(insert_count):
                    lru[i] = "val"

                self.assertEqual(lru.size, expect_size)

    def test_lru_negative_capacity(self):
        with self.assertRaises(ValueError):
            k3cacheable.LRU(-1)


class TestCacheable(unittest.TestCase):
    @k3cacheable.cache("method_cache_data", capacity=10, timeout=4, is_deepcopy=False)
    def _method_cache_data(self, key):
        data = need_cache_data.get(key, {})
        data["tm"] = time.time()
        return data

    def test_get_items_from_cache(self):
        cache_items = {}
        for key in need_cache_data:
            cache_items[key] = get_cache_data(key)

        time.sleep(0.1)
        for key in need_cache_data:
            self.assertEqual(get_cache_data(key), cache_items[key])

    def test_get_items_from_cache_use_method(self):
        cache_items = {}
        for key in need_cache_data:
            cache_items[key] = self._method_cache_data(key)

        time.sleep(0.1)
        for key in need_cache_data:
            self.assertEqual(self._method_cache_data(key), cache_items[key])

    def test_cache_item_timeout_and_cache_again(self):
        cases = (
            (2, False),
            (4, True),
        )

        tm = get_cache_data("key")["tm"]
        for sleep_time, is_timeout in cases:
            time.sleep(sleep_time)
            if is_timeout:
                self.assertNotEqual(tm, get_cache_data("key")["tm"])
            else:
                self.assertEqual(tm, get_cache_data("key")["tm"])

    def test_get_deepcopy_item_from_cache(self):
        self.assertIsNot(get_deepcopy_of_cache_data("key1"), get_deepcopy_of_cache_data("key1"))

    def test_get_pack_item_from_cache(self):
        # With `is_deepcopy=False`, only unpacking the cached msgpack bytes gives a new object on each call.
        first = get_pack_of_cache_data("key1")
        second = get_pack_of_cache_data("key1")
        self.assertEqual({"key": "key1"}, first)
        self.assertIsNot(first, second)

    def test_get_concurrent_update_cache_data(self):
        result = {}

        def _store_result(key):
            result[key] = get_concurrent_update_cache_data()

        _thread.start_new_thread(_store_result, ("key1",))
        time.sleep(1)
        _thread.start_new_thread(_store_result, ("key2",))

        while True:
            if "key2" in result:
                break
            time.sleep(0.1)

        self.assertIsNot(result["key1"], result["key2"])

    def test_get_mutext_update_cache_data(self):
        result = {}

        def _store_result(key):
            result[key] = get_mutex_update_cache_data()

        _thread.start_new_thread(_store_result, ("key1",))
        time.sleep(1)
        _thread.start_new_thread(_store_result, ("key2",))

        while True:
            if "key2" in result:
                break
            time.sleep(0.1)

        self.assertIs(result["key1"], result["key2"])

    def test_mutex_update_per_cache(self):
        started = threading.Event()
        release = threading.Event()

        @k3cacheable.cache("mutex_update_per_cache_slow", mutex_update=True)
        def slow():
            started.set()
            release.wait()
            return "slow"

        @k3cacheable.cache("mutex_update_per_cache_fast", mutex_update=True)
        def fast():
            return "fast"

        th_slow = threading.Thread(target=slow)
        th_slow.start()
        started.wait()

        # fast() uses another cache, so it does not wait for slow() to finish its update.
        rst = []
        th_fast = threading.Thread(target=lambda: rst.append(fast()))
        th_fast.start()
        th_fast.join(timeout=5)
        done = list(rst)

        release.set()
        th_slow.join()
        th_fast.join()
        self.assertEqual(["fast"], done)

    def test_wrapper_keeps_function_metadata(self):
        @k3cacheable.cache("wrapper_keeps_function_metadata")
        def documented(key):
            """Return the key."""
            return key

        self.assertEqual("documented", documented.__name__)
        self.assertEqual("Return the key.", documented.__doc__)

    def test_generate_lru_key(self):
        cases = (
            ((), {}, ((), ())),
            ((1,), {"a": "val_a"}, (((int, 1),), (("a", (str, "val_a")),))),
            ((1.0, True), {}, (((float, 1.0), (bool, True)), ())),
            (
                ("c", 1),
                {"b": "val_b", "a": "val_a"},
                (((str, "c"), (int, 1)), (("a", (str, "val_a")), ("b", (str, "val_b")))),
            ),
            (([1, 2],), {"a": {"b": 1}}, (((list, "[1, 2]"),), (("a", (dict, "{'b': 1}")),))),
        )

        for args, argkv, expected in cases:
            key = k3cacheable.Cacheable()._arg_key(args, argkv)
            self.assertEqual(expected, key)

    def test_args_with_same_repr(self):
        # Distinct args with the same repr must not share a cached result.
        class Box:
            def __init__(self, v):
                self.v = v

            def __repr__(self):
                return "Box"

        calls = []

        @k3cacheable.cache("args_with_same_repr", capacity=10, timeout=60, is_deepcopy=False)
        def get(box):
            calls.append(box.v)
            return box.v

        box1 = Box(1)
        box2 = Box(2)

        results = [get(box1), get(box2), get(box1), get(box2)]
        self.assertEqual([1, 2, 1, 2], results)
        self.assertEqual([1, 2], calls)

    def test_args_of_equal_value_and_other_type(self):
        calls = []

        @k3cacheable.cache("args_of_equal_value_and_other_type", capacity=10, timeout=60, is_deepcopy=False)
        def get(v):
            calls.append(v)
            return repr(v)

        results = [get(1), get(1.0), get(True), get(1), get([1]), get([1])]
        self.assertEqual(["1", "1.0", "True", "1", "[1]", "[1]"], results)

        # 1, 1.0 and True compare equal, so the types show that each one was called.
        call_types = [type(v) for v in calls]
        self.assertEqual([int, float, bool, list], call_types)

    def test_functions_sharing_cache_name(self):
        @k3cacheable.cache("shared_by_two_functions", capacity=10, timeout=60, is_deepcopy=False)
        def get_aa(key):
            return "aa-" + key

        @k3cacheable.cache("shared_by_two_functions", capacity=10, timeout=60, is_deepcopy=False)
        def get_bb(key):
            return "bb-" + key

        self.assertEqual("aa-k", get_aa("k"))
        self.assertEqual("bb-k", get_bb("k"))


@k3cacheable.cache("deepcopy_of_cache_data", capacity=100, timeout=60, is_deepcopy=True)
def get_deepcopy_of_cache_data(key):
    return need_cache_data.get(key, {})


@k3cacheable.cache("pack_of_cache_data", capacity=100, timeout=60, is_deepcopy=False, is_pack=True)
def get_pack_of_cache_data(key):
    return {"key": key}


@k3cacheable.cache("cache_data", capacity=100, timeout=4, is_deepcopy=False)
def get_cache_data(key):
    cache_data = need_cache_data.get(key, {})
    cache_data["tm"] = time.time()
    return cache_data


@k3cacheable.cache("concurrent_update_cache_data", capacity=100, timeout=60, is_deepcopy=False, mutex_update=False)
def get_concurrent_update_cache_data():
    time.sleep(3)
    return {}


@k3cacheable.cache("mutex_update_cache_data", capacity=100, timeout=60, is_deepcopy=False, mutex_update=True)
def get_mutex_update_cache_data():
    time.sleep(3)
    return {}


need_cache_data = {
    "key1": {"tm": 0},
    "key2": {"tm": 0},
    "key3": {"tm": 0},
    "key4": {"tm": 0},
}
