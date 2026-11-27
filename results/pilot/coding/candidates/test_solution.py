"""Contract regressions plus an exhaustive small-graph ordering oracle."""

import copy
import itertools
import math
import sys
import unittest
from decimal import Decimal
from fractions import Fraction
from scheduler import schedule


def task(task_id="a", duration=1, deps=None, **extra):
    return {"id": task_id, "duration": duration,
            "deps": [] if deps is None else deps, **extra}


class ValidationTests(unittest.TestCase):
    def test_bad_outer_container(self):
        for value in (None, {}, (), "", 1, iter([])):
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule(value)

    def test_bad_task_container(self):
        for value in (None, [], (), "a", 1, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule([value])

    def test_each_required_key(self):
        for key in ("id", "duration", "deps"):
            value = task()
            del value[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                schedule([value])

    def test_bad_ids(self):
        for value in ("", None, 1, True, [], {}, ("a",)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule([task(value)])

    def test_duplicate_ids(self):
        with self.assertRaises(ValueError):
            schedule([task(), task(duration=3)])

    def test_bad_duration_type(self):
        for value in (None, "1", True, False, [], {}, complex(1),
                      Decimal("1"), Fraction(1, 2)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule([task(duration=value)])

    def test_numeric_subclass_conversion(self):
        class ValidInt(int):
            pass

        class ValidFloat(float):
            pass

        class InvalidInt(int):
            def __float__(self):
                raise TypeError("not convertible")

        class InvalidFloat(float):
            def __float__(self):
                raise TypeError("not convertible")

        for value in (ValidInt(2), ValidFloat(2.5)):
            with self.subTest(value=value):
                result = schedule([task(duration=value)])
                self.assertEqual(result["a"]["finish"], float(value))
        for value in (InvalidInt(2), InvalidFloat(2.5)):
            with self.subTest(type=type(value).__name__), self.assertRaises(ValueError):
                schedule([task(duration=value)])

    def test_bad_duration_value(self):
        for value in (-1, -0.1, float("nan"), float("inf"), -float("inf"),
                      10 ** 1000, -(10 ** 1000)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule([task(duration=value)])

    def test_bad_deps_container(self):
        for value in (None, "a", (), {"a"}, {}, 1, True):
            value_task = task()
            value_task["deps"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule([value_task])

    def test_bad_dependency_ids(self):
        for value in ("", None, 1, True, [], {}, ("a",)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule([task(deps=[value])])

    def test_unknown_dependency(self):
        with self.assertRaises(ValueError):
            schedule([task(deps=["missing"])])

    def test_self_dependency(self):
        with self.assertRaises(ValueError):
            schedule([task(deps=["a", "a"])])

    def test_cycles_including_disconnected_cycle(self):
        cases = [
            [task("a", deps=["b"]), task("b", deps=["a"])],
            [task("a", deps=["c"]), task("b", deps=["a"]), task("c", deps=["b"])],
            [task("root"), task("a", deps=["b"]), task("b", deps=["a"])],
        ]
        for tasks in cases:
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                schedule(tasks)

    def test_arithmetic_overflow(self):
        with self.assertRaises(ValueError):
            schedule([task("a", sys.float_info.max), task("b", sys.float_info.max, ["a"])])


class SchedulingTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(schedule([]), {})

    def test_forward_reference_and_maximum_finish(self):
        result = schedule([task("join", 2.5, ["slow", "fast"]),
                           task("fast", 1), task("slow", 8)])
        self.assertEqual(result, {
            "fast": {"start": 0.0, "finish": 1.0},
            "slow": {"start": 0.0, "finish": 8.0},
            "join": {"start": 8.0, "finish": 10.5},
        })
        self.assertEqual(list(result), ["fast", "slow", "join"])

    def test_newly_ready_task_precedes_old_ready_task(self):
        result = schedule([task("z", 2), task("a", 1, ["b"]), task("b", 10)])
        self.assertEqual(list(result), ["b", "a", "z"])
        self.assertEqual([entry["start"] for entry in result.values()], [0, 10, 0])

    def test_duplicate_dependencies_and_diamond(self):
        result = schedule([task("d", 1, ["b", "c", "b", "c"]),
                           task("c", 4, ["a", "a"]),
                           task("b", 2, ["a"]), task("a", 3)])
        self.assertEqual(list(result), ["a", "b", "c", "d"])
        self.assertEqual(result["d"], {"start": 7.0, "finish": 8.0})

    def test_zero_and_negative_zero_durations(self):
        result = schedule([task("a", -0.0), task("b", 0, ["a"])])
        self.assertEqual(result, {"a": {"start": 0.0, "finish": 0.0},
                                  "b": {"start": 0.0, "finish": 0.0}})

    def test_disconnected_tasks_and_unicode_order(self):
        ids = ["é", "a", "A", "aa", " ", "0", "Ω"]
        result = schedule([task(value) for value in ids])
        self.assertEqual(list(result), sorted(ids))
        self.assertTrue(all(entry["start"] == 0 for entry in result.values()))

    def test_binary64_conversion_before_arithmetic(self):
        result = schedule([task("a", 2 ** 53 + 1), task("b", 1, ["a"])])
        self.assertEqual(result["a"]["finish"], float(2 ** 53))
        self.assertEqual(result["b"]["finish"], float(2 ** 53))
        for entry in result.values():
            for value in entry.values():
                self.assertIs(type(value), float)

    def test_floating_point_arithmetic(self):
        result = schedule([task("a", 0.1), task("b", 0.2, ["a"])])
        self.assertEqual(result["b"]["finish"], 0.1 + 0.2)

    def test_extreme_finite_values(self):
        tiny = math.nextafter(0.0, 1.0)
        result = schedule([task("tiny", tiny), task("max", sys.float_info.max),
                           task("end", 0, ["max"])])
        self.assertEqual(result["tiny"]["finish"], tiny)
        self.assertEqual(result["end"]["finish"], sys.float_info.max)

    def test_input_immutability_and_ignored_extra_keys(self):
        tasks = [task("z", 0, ["a", "a"], extra={"nested": [1, 2]}), task("a", 2)]
        snapshot = copy.deepcopy(tasks)
        original_tasks = list(tasks)
        original_deps = [entry["deps"] for entry in tasks]
        result = schedule(tasks)
        self.assertEqual(tasks, snapshot)
        for i in range(len(tasks)):
            self.assertIs(tasks[i], original_tasks[i])
            self.assertIs(tasks[i]["deps"], original_deps[i])
        result["a"]["finish"] = -10
        self.assertEqual(tasks, snapshot)
        self.assertEqual(schedule(tasks)["a"]["finish"], 2)

    def test_input_immutability_on_error(self):
        cases = [[task("z"), task("a", deps=["missing"])],
                 [task("z", deps=["a"]), task("a", deps=["z"])]]
        for tasks in cases:
            snapshot = copy.deepcopy(tasks)
            with self.assertRaises(ValueError):
                schedule(tasks)
            self.assertEqual(tasks, snapshot)

    def test_long_reverse_input_chain(self):
        size = 3000
        tasks = [task(f"t{i:04d}", 1, [f"t{i - 1:04d}"] if i else [])
                 for i in reversed(range(size))]
        result = schedule(tasks)
        self.assertEqual(list(result), [f"t{i:04d}" for i in range(size)])
        self.assertEqual(result[f"t{size - 1:04d}"],
                         {"start": float(size - 1), "finish": float(size)})

    def test_wide_fan_in_and_fan_out(self):
        leaves = [f"leaf{i:04d}" for i in range(1000)]
        tasks = [task("root", 3), task("sink", 2, leaves)]
        tasks.extend(task(value, i % 7, ["root"]) for i, value in enumerate(leaves))
        result = schedule(list(reversed(tasks)))
        self.assertEqual(list(result), ["root", *leaves, "sink"])
        self.assertEqual(result["sink"], {"start": 9.0, "finish": 11.0})

    def test_all_four_vertex_directed_graphs_against_permutation_oracle(self):
        # Only this test oracle enumerates permutations, never the scheduler.
        # All 4096 simple directed graphs include 543 DAGs and 3553 cycles.
        ids = ("a", "b", "c", "d")
        potential_edges = [(a, b) for a in ids for b in ids if a != b]
        orders = list(itertools.permutations(ids))
        positions = [{name: i for i, name in enumerate(order)} for order in orders]
        dags = 0
        for mask in range(1 << len(potential_edges)):
            edges = [edge for i, edge in enumerate(potential_edges) if mask & (1 << i)]
            expected_order = next((order for order, pos in zip(orders, positions)
                                   if all(pos[a] < pos[b] for a, b in edges)), None)
            tasks = [task(name, i / 2, [a for a, b in edges if b == name])
                     for i, name in reversed(list(enumerate(ids)))]
            with self.subTest(mask=mask):
                if expected_order is None:
                    with self.assertRaises(ValueError):
                        schedule(tasks)
                    continue
                dags += 1
                expected = {}
                for name in expected_order:
                    start = max((expected[a]["finish"] for a, b in edges if b == name),
                                default=0.0)
                    expected[name] = {"start": start, "finish": start + ids.index(name) / 2}
                result = schedule(tasks)
                self.assertEqual(list(result), list(expected_order))
                self.assertEqual(result, expected)
        self.assertEqual(dags, 543)


if __name__ == "__main__":
    unittest.main()
