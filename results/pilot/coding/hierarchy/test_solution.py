"""Contract regressions for the earliest-start dependency scheduler.

Run from the workspace root with: python3 -m unittest test_solution -v
All fixtures are synthetic; the randomized DAG oracle uses a fixed seed.
"""

import copy
import math
import random
import sys
import unittest

from scheduler import schedule


_DEFAULT_DEPS = object()


def task(identifier, duration=1, deps=_DEFAULT_DEPS):
    return {"id": identifier, "duration": duration,
            "deps": [] if deps is _DEFAULT_DEPS else deps}


class ValidationTests(unittest.TestCase):
    def test_requires_list(self):
        for value in (None, (), {}, "", 42, True, iter([])):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    schedule(value)

    def test_requires_dictionary_tasks(self):
        for value in (None, [], (), "a", 1, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    schedule([value])

    def test_requires_each_field(self):
        for key in ("id", "duration", "deps"):
            value = task("a")
            del value[key]
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    schedule([value])

    def test_ids_are_nonempty_strings(self):
        for identifier in ("", None, 0, False, [], {}, b"a"):
            with self.subTest(identifier=identifier):
                with self.assertRaises(ValueError):
                    schedule([task(identifier)])

    def test_duplicate_ids(self):
        with self.assertRaises(ValueError):
            schedule([task("a"), task("a", 4)])

    def test_durations_require_int_or_float_excluding_bool(self):
        for duration in (None, True, False, "1", [], {}, complex(1, 0)):
            with self.subTest(duration=duration):
                with self.assertRaises(ValueError):
                    schedule([task("a", duration)])

    def test_negative_and_nonfinite_durations(self):
        for duration in (-1, -0.5, -5e-324, math.inf, -math.inf, math.nan):
            with self.subTest(duration=duration):
                with self.assertRaises(ValueError):
                    schedule([task("a", duration)])

    def test_integer_conversion_overflow(self):
        for duration in (10 ** 400, -(10 ** 400)):
            with self.subTest(positive=duration > 0):
                with self.assertRaises(ValueError):
                    schedule([task("a", duration)])

    def test_dependencies_require_list(self):
        for deps in (None, (), "a", {"a"}, {}, iter([])):
            with self.subTest(deps=repr(deps)):
                with self.assertRaises(ValueError):
                    schedule([task("a", deps=deps)])

    def test_dependency_ids_and_unknown_references(self):
        for dep in ("missing", "", None, False, 1, [], {}, b"a"):
            with self.subTest(dep=dep):
                with self.assertRaises(ValueError):
                    schedule([task("a"), task("b", deps=[dep])])

    def test_self_edge(self):
        with self.assertRaises(ValueError):
            schedule([task("a", deps=["a"])])

    def test_extra_fields_are_ignored(self):
        value = task("a", 2)
        value["metadata"] = {"items": [object()]}
        self.assertEqual(schedule([value]),
                         {"a": {"start": 0.0, "finish": 2.0}})


class GraphTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(schedule([]), {})

    def test_forward_dependency_and_nonlexical_topology(self):
        tasks = [task("a", 3, ["z"]), task("z", 4)]
        actual = schedule(tasks)
        self.assertEqual(list(actual), ["z", "a"])
        self.assertEqual(actual["a"], {"start": 4.0, "finish": 7.0})

    def test_fanin_uses_maximum_finish(self):
        actual = schedule([task("a", 2), task("b", 8),
                           task("c", 3, ["a", "b"])])
        self.assertEqual(actual["c"], {"start": 8.0, "finish": 11.0})

    def test_unlimited_worker_capacity(self):
        actual = schedule([task("b", 5), task("a", 9)])
        self.assertEqual(actual["a"]["start"], 0.0)
        self.assertEqual(actual["b"]["start"], 0.0)

    def test_repeated_dependencies_are_one_edge(self):
        actual = schedule([task("b", 3, ["a", "a", "a"]), task("a", 2)])
        self.assertEqual(actual,
                         {"a": {"start": 0.0, "finish": 2.0},
                          "b": {"start": 2.0, "finish": 5.0}})

    def test_ready_tasks_use_global_lexicographic_minimum(self):
        tasks = [task("z"), task("y"), task("b", deps=["y"]),
                 task("a", deps=["z"])]
        self.assertEqual(list(schedule(tasks)), ["y", "b", "z", "a"])

    def test_order_is_independent_of_start_time(self):
        tasks = [task("a", 1, ["b"]), task("b", 100), task("c", 2)]
        actual = schedule(tasks)
        self.assertEqual(list(actual), ["b", "a", "c"])
        self.assertEqual([actual[key]["start"] for key in actual],
                         [0.0, 100.0, 0.0])

    def test_string_order_including_unicode_and_whitespace(self):
        ids = ["é", "a", "A", "10", "2", " ", "β"]
        self.assertEqual(list(schedule([task(name) for name in ids])), sorted(ids))

    def test_two_node_cycle(self):
        with self.assertRaises(ValueError):
            schedule([task("a", deps=["b"]), task("b", deps=["a"])])

    def test_disconnected_cycle_with_valid_component(self):
        with self.assertRaises(ValueError):
            schedule([task("a"), task("b", deps=["c"]),
                      task("c", deps=["d"]), task("d", deps=["b"])])

    def test_cycle_with_outgoing_tail_and_incoming_source(self):
        with self.assertRaises(ValueError):
            schedule([task("source"), task("a", deps=["source", "b"]),
                      task("b", deps=["a"]), task("tail", deps=["b"])])

    def test_long_chain_is_iterative(self):
        count = 3000
        tasks = [task(f"t{i:05d}", 0.5,
                      [] if i == 0 else [f"t{i - 1:05d}"])
                 for i in range(count)]
        tasks.reverse()
        actual = schedule(tasks)
        self.assertEqual(len(actual), count)
        self.assertEqual(list(actual), [f"t{i:05d}" for i in range(count)])
        self.assertEqual(actual[f"t{count - 1:05d}"],
                         {"start": (count - 1) * 0.5, "finish": count * 0.5})

    def test_wide_sparse_graph(self):
        count = 2500
        tasks = [task(f"s{i:04d}", i % 7) for i in range(count)]
        tasks += [task(f"a{i:04d}", 0.25,
                       [f"s{i:04d}", f"s{(i + 1) % count:04d}"])
                  for i in range(count)]
        tasks.reverse()
        actual = schedule(tasks)
        self.assertEqual(len(actual), 2 * count)
        for i in range(count):
            expected_start = float(max(i % 7, ((i + 1) % count) % 7))
            self.assertEqual(actual[f"a{i:04d}"],
                             {"start": expected_start,
                              "finish": expected_start + 0.25})

    def test_random_dags_against_independent_scan_oracle(self):
        rng = random.Random(15793)
        for case in range(60):
            identifiers = [f"n{i:02d}" for i in range(rng.randrange(1, 19))]
            rng.shuffle(identifiers)
            tasks = []
            for i, identifier in enumerate(identifiers):
                deps = [earlier for earlier in identifiers[:i] if rng.random() < 0.22]
                if deps and rng.random() < 0.5:
                    deps.append(rng.choice(deps))
                tasks.append(task(identifier, rng.choice([0, 0.125, 1, 2.5, 7]), deps))
            rng.shuffle(tasks)
            pending = {value["id"]: value for value in tasks}
            expected = {}
            while pending:
                ready = [identifier for identifier, value in pending.items()
                         if all(dep in expected for dep in value["deps"])]
                identifier = min(ready)
                value = pending.pop(identifier)
                start = max((expected[dep]["finish"] for dep in value["deps"]),
                            default=0.0)
                expected[identifier] = {"start": start,
                                        "finish": start + float(value["duration"])}
            with self.subTest(case=case):
                actual = schedule(tasks)
                self.assertEqual(actual, expected)
                self.assertEqual(list(actual), list(expected))


class FloatingPointTests(unittest.TestCase):
    def test_integer_inputs_use_float_results(self):
        actual = schedule([task("a", 2), task("b", 3, ["a"])])
        for times in actual.values():
            self.assertIsInstance(times["start"], float)
            self.assertIsInstance(times["finish"], float)

    def test_duration_is_converted_before_addition(self):
        actual = schedule([task("a", 2 ** 53 + 1), task("b", 1, ["a"]),
                           task("c", 1, ["b"])])
        self.assertEqual(actual["a"]["finish"], float(2 ** 53))
        self.assertEqual(actual["b"]["finish"], float(2 ** 53))
        self.assertEqual(actual["c"]["finish"], float(2 ** 53))

    def test_fractional_addition_uses_binary64(self):
        actual = schedule([task("a", 0.1), task("b", 0.2, ["a"])])
        self.assertEqual(actual["b"]["finish"], 0.1 + 0.2)

    def test_zero_and_negative_zero_are_valid(self):
        actual = schedule([task("a", -0.0), task("b", 0, ["a"])])
        self.assertEqual(actual, {"a": {"start": 0.0, "finish": 0.0},
                                  "b": {"start": 0.0, "finish": 0.0}})

    def test_smallest_subnormal_is_valid(self):
        actual = schedule([task("a", 5e-324), task("b", 5e-324, ["a"])])
        self.assertEqual(actual["b"]["finish"], 1e-323)

    def test_largest_finite_duration_and_zero_successor(self):
        actual = schedule([task("a", sys.float_info.max), task("b", 0, ["a"])])
        self.assertEqual(actual["b"]["finish"], sys.float_info.max)

    def test_computed_finish_overflow(self):
        with self.assertRaises(ValueError):
            schedule([task("a", 1e308), task("b", 1e308, ["a"])])


class ImmutabilityTests(unittest.TestCase):
    def test_success_preserves_entire_input_and_references(self):
        deps = ["a", "a"]
        metadata = {"notes": ["preserve", {"nested": True}]}
        tasks = [task("b", 2, deps), task("a", 3)]
        tasks[0]["metadata"] = metadata
        before = copy.deepcopy(tasks)
        original_tasks = tuple(tasks)
        first = schedule(tasks)
        self.assertEqual(tasks, before)
        self.assertTrue(all(left is right for left, right in zip(tasks, original_tasks)))
        self.assertIs(tasks[0]["deps"], deps)
        self.assertIs(tasks[0]["metadata"], metadata)
        first["b"]["finish"] = -999
        self.assertEqual(schedule(tasks)["b"]["finish"], 5.0)
        self.assertEqual(tasks, before)

    def test_rejected_input_is_not_modified(self):
        cases = [
            [task("z"), task("a", -1)],
            [task("z"), task("a", deps=["unknown", "unknown"])],
            [task("z", deps=["a"]), task("a", deps=["z"])],
            [task("z", 1e308, ["a"]), task("a", 1e308)],
            [task("z"), task("a", deps=[[]])],
        ]
        for number, tasks in enumerate(cases):
            before = copy.deepcopy(tasks)
            original_tasks = tuple(tasks)
            with self.subTest(case=number):
                with self.assertRaises(ValueError):
                    schedule(tasks)
                self.assertEqual(tasks, before)
                self.assertTrue(all(left is right
                                    for left, right in zip(tasks, original_tasks)))


if __name__ == "__main__":
    unittest.main()
