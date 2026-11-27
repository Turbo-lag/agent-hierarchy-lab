"""Independent regression tests for the dependency scheduler contract."""

import copy
import math
import sys
import unittest

from scheduler import schedule


_DEFAULT_DEPS = object()


def task(identifier, duration=1, deps=_DEFAULT_DEPS, **extra):
    return dict(id=identifier, duration=duration,
                deps=[] if deps is _DEFAULT_DEPS else deps, **extra)


class ScheduleContractTests(unittest.TestCase):
    def assert_rejected(self, tasks):
        with self.assertRaises(ValueError):
            schedule(tasks)

    def test_empty(self):
        self.assertEqual(schedule([]), {})

    def test_forward_dependencies_and_latest_predecessor_finish(self):
        tasks = [task("join", 3, ["slow", "fast"]),
                 task("slow", 7), task("fast", 2)]
        self.assertEqual(schedule(tasks), {
            "fast": {"start": 0.0, "finish": 2.0},
            "slow": {"start": 0.0, "finish": 7.0},
            "join": {"start": 7.0, "finish": 10.0},
        })

    def test_order_is_ready_id_order_independent_of_start_time(self):
        result = schedule([task("z", 0), task("a", 1, ["b"]),
                           task("b", 10)])
        self.assertEqual(list(result), ["b", "a", "z"])
        self.assertEqual(result["a"]["start"], 10.0)
        self.assertEqual(result["z"]["start"], 0.0)

    def test_newly_ready_tasks_compete_immediately(self):
        result = schedule([task("z"), task("c"),
                           task("b", 1, ["z"]), task("a", 1, ["b"])])
        self.assertEqual(list(result), ["c", "z", "b", "a"])

    def test_independent_tasks_have_unlimited_capacity(self):
        result = schedule([task("z", 100), task("a", 2), task("m", 3)])
        self.assertEqual(list(result), ["a", "m", "z"])
        self.assertTrue(all(value["start"] == 0 for value in result.values()))

    def test_duplicate_dependencies_are_one_edge(self):
        result = schedule([task("c", 2, ["a", "b", "a", "b"]),
                           task("b", 3, ["a", "a"]), task("a", 4)])
        self.assertEqual(list(result), ["a", "b", "c"])
        self.assertEqual(result["c"], {"start": 7.0, "finish": 9.0})

    def test_zero_durations_and_disconnected_components(self):
        result = schedule([task("z", 0), task("b", -0.0, ["a"]),
                           task("a", 0), task("c", 1, ["z"])])
        self.assertEqual(list(result), ["a", "b", "z", "c"])
        self.assertEqual(result["b"], {"start": 0.0, "finish": 0.0})
        self.assertEqual(result["c"], {"start": 0.0, "finish": 1.0})

    def test_ids_are_nonempty_strings_not_trimmed(self):
        result = schedule([task("é"), task("a"), task(" "), task("A")])
        self.assertEqual(list(result), sorted(["é", "a", " ", "A"]))

    def test_top_level_must_be_list(self):
        for value in (None, {}, (), "", 1, True, set()):
            with self.subTest(value=repr(value)):
                self.assert_rejected(value)

    def test_each_task_must_be_dictionary_with_required_keys(self):
        for value in (None, 1, "task", [], (), {},
                      {"id": "a", "duration": 1},
                      {"id": "a", "deps": []},
                      {"duration": 1, "deps": []}):
            with self.subTest(value=repr(value)):
                self.assert_rejected([value])

    def test_invalid_and_duplicate_ids(self):
        for identifier in ("", None, 1, True, [], {}, ["a"]):
            with self.subTest(identifier=repr(identifier)):
                self.assert_rejected([task(identifier)])
        self.assert_rejected([task("a"), task("a", 3)])

    def test_duration_type_and_range_validation(self):
        invalid = [None, True, False, "1", [], {}, complex(1, 0),
                   -1, -0.001, math.inf, -math.inf, math.nan, 10 ** 400]
        for duration in invalid:
            with self.subTest(duration=repr(duration)):
                self.assert_rejected([task("a", duration)])

    def test_dependencies_must_be_list_of_valid_ids(self):
        for deps in (None, "a", ("a",), {"a"}, {"a": 1}, 1):
            with self.subTest(deps=repr(deps)):
                self.assert_rejected([task("a"), task("b", deps=deps)])
        for dep in (None, 1, True, [], {}, "", "unknown"):
            with self.subTest(dep=repr(dep)):
                self.assert_rejected([task("a"), task("b", deps=[dep])])

    def test_self_edges_and_cycles(self):
        cases = [
            [task("a", deps=["a"])],
            [task("a", deps=["b"]), task("b", deps=["a"])],
            [task("a", deps=["b"]), task("b", deps=["c"]),
             task("c", deps=["a"])],
            [task("free"), task("tail", deps=["a"]),
             task("a", deps=["b", "b"]), task("b", deps=["a"])],
        ]
        for tasks in cases:
            with self.subTest(tasks=tasks):
                self.assert_rejected(tasks)

    def test_float_conversion_precedes_scheduling(self):
        # Exact integer arithmetic would produce 9007199254740994 at b.
        # Required binary64 conversion rounds a first, then rounds a + 1.
        result = schedule([task("a", 2 ** 53 + 1), task("b", 1, ["a"])])
        expected = float(2 ** 53 + 1)
        self.assertEqual(result["a"]["finish"], expected)
        self.assertEqual(result["b"]["finish"], expected + 1.0)
        self.assertIsInstance(result["a"]["finish"], float)
        self.assertIsInstance(result["b"]["finish"], float)

    def test_finite_float_extremes_and_fractional_durations(self):
        maximum = sys.float_info.max
        result = schedule([task("a", maximum), task("b", 0, ["a"])])
        self.assertEqual(result["b"]["finish"], maximum)
        tiny = float.fromhex("0x0.0000000000001p-1022")
        self.assertEqual(schedule([task("tiny", tiny)])["tiny"]["finish"], tiny)
        result = schedule([task("a", 0.1), task("b", 0.2, ["a"])])
        self.assertEqual(result["b"]["finish"], 0.1 + 0.2)

    def test_computed_finish_overflow_is_value_error(self):
        maximum = sys.float_info.max
        self.assert_rejected([task("a", maximum), task("b", maximum, ["a"])])

    def test_valid_input_and_nested_extra_values_are_unchanged(self):
        deps = ["z", "z"]
        metadata = {"nested": [1, {"keep": [2, 3]}]}
        first = task("z", 3, metadata=metadata)
        second = task("a", 2, deps, metadata=metadata)
        tasks = [first, second]
        before = copy.deepcopy(tasks)
        schedule(tasks)
        self.assertEqual(tasks, before)
        self.assertIs(tasks[0], first)
        self.assertIs(tasks[1], second)
        self.assertIs(second["deps"], deps)
        self.assertIs(first["metadata"], metadata)
        self.assertIs(second["metadata"], metadata)

    def test_invalid_inputs_are_unchanged(self):
        cases = [
            [task("z"), task("a", -1)],
            [task("z"), task("a", deps=["missing", "missing"])],
            [task("z", deps=["a"]), task("a", deps=["z"])],
            [task("z"), {"id": "a", "deps": []}],
            [task("z"), task(1), task("a")],
            [task("z"), {"duration": 1, "deps": []}, task("a")],
            [task("z"), task("a", deps=[["z"]])],
            [task("z", 10 ** 400), task("a")],
            [task("z", sys.float_info.max),
             task("a", sys.float_info.max, ["z"])],
        ]
        for tasks in cases:
            with self.subTest(tasks=tasks):
                before = copy.deepcopy(tasks)
                original_objects = list(tasks)
                self.assert_rejected(tasks)
                self.assertEqual(tasks, before)
                for original, actual in zip(original_objects, tasks):
                    self.assertIs(actual, original)

    def test_chain_exceeding_recursion_limit(self):
        length = 2501
        tasks = [task(f"n{index:04d}", 1,
                      [] if index == 0 else [f"n{index - 1:04d}"])
                 for index in reversed(range(length))]
        before = copy.deepcopy(tasks)
        result = schedule(tasks)
        self.assertEqual(list(result), [f"n{index:04d}" for index in range(length)])
        for index, timing in enumerate(result.values()):
            self.assertEqual(timing, {"start": float(index),
                                      "finish": float(index + 1)})
        self.assertEqual(tasks, before)


if __name__ == "__main__":
    unittest.main()
