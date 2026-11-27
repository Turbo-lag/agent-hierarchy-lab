"""Independent regression coverage for the public schedule contract."""

import copy
import itertools
import math
import sys
import unittest

from scheduler import schedule


def task(task_id="a", duration=1, deps=None, **extra):
    return {"id": task_id, "duration": duration, "deps": [] if deps is None else deps, **extra}


class ScheduleTests(unittest.TestCase):
    def assert_invalid(self, tasks):
        with self.assertRaises(ValueError):
            schedule(tasks)

    def test_empty(self):
        self.assertEqual(schedule([]), {})

    def test_duration_conversion_and_extra_fields(self):
        result = schedule([task("a", 2, metadata={"items": [1]}), task("b", 0.25, ["a"])])
        self.assertEqual(result, {"a": {"start": 0.0, "finish": 2.0},
                                  "b": {"start": 2.0, "finish": 2.25}})
        for times in result.values():
            for value in times.values():
                self.assertIsInstance(value, float)

    def test_zero_durations(self):
        result = schedule([task("a", -0.0), task("b", 0, ["a", "a"])])
        self.assertEqual(list(result), ["a", "b"])
        self.assertTrue(all(times == {"start": 0.0, "finish": 0.0} for times in result.values()))

    def test_forward_dependencies(self):
        result = schedule([task("a", 3, ["z"]), task("z", 2)])
        self.assertEqual(list(result), ["z", "a"])
        self.assertEqual(result["a"], {"start": 2.0, "finish": 5.0})

    def test_fan_in_and_diamond(self):
        result = schedule([task("d", 4, ["b", "c"]), task("c", 7, ["a"]),
                           task("b", 2, ["a"]), task("a", 1)])
        self.assertEqual(list(result), ["a", "b", "c", "d"])
        self.assertEqual(result["d"], {"start": 8.0, "finish": 12.0})

    def test_duplicate_dependencies(self):
        result = schedule([task("a", 2), task("b", 5), task("c", 1, ["a", "b", "a", "b"])])
        self.assertEqual(result["c"], {"start": 5.0, "finish": 6.0})

    def test_newly_ready_task_takes_lexical_priority(self):
        result = schedule([task("z"), task("a", deps=["b"]), task("b")])
        self.assertEqual(list(result), ["b", "a", "z"])

    def test_order_is_independent_of_start_time(self):
        result = schedule([task("c", 0), task("b", 1, ["a"]), task("a", 10)])
        self.assertEqual(list(result), ["a", "b", "c"])
        self.assertEqual([times["start"] for times in result.values()], [0.0, 10.0, 0.0])

    def test_disconnected_components_and_lexical_strings(self):
        result = schedule([task("z", deps=["a"]), task("a"), task("10"),
                           task("2"), task("A"), task("é")])
        self.assertEqual(list(result), ["10", "2", "A", "a", "z", "é"])

    def test_long_chain(self):
        count = 2500
        tasks = [task(f"t{i:04d}", 1, [] if i == 0 else [f"t{i - 1:04d}"])
                 for i in range(count)]
        result = schedule(tasks[::-1])
        self.assertEqual(list(result), [f"t{i:04d}" for i in range(count)])
        for i, times in enumerate(result.values()):
            self.assertEqual(times, {"start": float(i), "finish": float(i + 1)})

    def test_largest_finite_duration(self):
        for duration in [sys.float_info.max, int(sys.float_info.max)]:
            with self.subTest(duration=duration):
                result = schedule([task(duration=duration)])
                self.assertEqual(result["a"]["finish"], sys.float_info.max)

    def test_computed_overflow(self):
        self.assert_invalid([task("a", 1e308), task("b", 1e308, ["a"])])

    def test_binary64_arithmetic(self):
        result = schedule([task("a", 2**53), task("b", 1, ["a"]), task("c", 1, ["b"])])
        self.assertEqual(result["c"]["finish"], float(2**53))
        self.assertIsInstance(result["a"]["finish"], float)

    def test_outer_input_must_be_list(self):
        for value in [None, {}, (), "", 0, iter([])]:
            with self.subTest(value=value):
                self.assert_invalid(value)

    def test_task_record_must_be_dictionary(self):
        for record in [None, [], (), "a", 1]:
            with self.subTest(record=record):
                self.assert_invalid([record])

    def test_required_keys(self):
        for key in ["id", "duration", "deps"]:
            record = task()
            del record[key]
            with self.subTest(missing_key=key):
                self.assert_invalid([record])

    def test_malformed_ids(self):
        for task_id in ["", None, 1, True, [], {}, b"a"]:
            with self.subTest(task_id=task_id):
                self.assert_invalid([task(task_id)])

    def test_duplicate_ids(self):
        self.assert_invalid([task("a", 2), task("a", 3)])

    def test_invalid_durations(self):
        for duration in [-1, -0.1, True, False, "1", None, 1j, [], {},
                         math.nan, math.inf, -math.inf, 10**1000, -(10**1000)]:
            with self.subTest(duration=duration):
                self.assert_invalid([task(duration=duration)])

    def test_dependencies_must_be_list(self):
        for deps in [None, "a", (), set(), {}, 1]:
            record = task()
            record["deps"] = deps
            with self.subTest(deps=deps):
                self.assert_invalid([record])

    def test_dependency_entries_must_be_strings(self):
        for dep in [None, 1, True, [], {}, b"a"]:
            with self.subTest(dep=dep):
                self.assert_invalid([task("a"), task("b", deps=[dep])])

    def test_unknown_dependency(self):
        for dep in ["missing", ""]:
            with self.subTest(dep=dep):
                self.assert_invalid([task(deps=[dep])])

    def test_self_edge(self):
        self.assert_invalid([task(deps=["a"])])

    def test_cycles(self):
        examples = [
            [task("a", deps=["b"]), task("b", deps=["a"])],
            [task("a", deps=["c", "c"]), task("b", deps=["a"]), task("c", deps=["b"])],
            [task("free"), task("a", deps=["b"]), task("b", deps=["a"])],
        ]
        for tasks in examples:
            with self.subTest(tasks=tasks):
                self.assert_invalid(tasks)

    def test_valid_input_is_unchanged(self):
        tasks = [task("z", 2, ["a", "a"], metadata={"nested": [1, 2]}), task("a", 1)]
        before = copy.deepcopy(tasks)
        records = list(tasks)
        deps = [record["deps"] for record in tasks]
        metadata = tasks[0]["metadata"]
        schedule(tasks)
        self.assertEqual(tasks, before)
        for i, record in enumerate(records):
            self.assertIs(tasks[i], record)
            self.assertIs(tasks[i]["deps"], deps[i])
        self.assertIs(tasks[0]["metadata"], metadata)

    def test_invalid_input_is_unchanged(self):
        examples = [
            [task("z"), task("a", -1)],
            [task("z"), {"id": "a"}],
            [task("z"), task("a", deps=["b"]), task("b", deps=["a"])],
            [task("z", 1e308), task("a", 1e308, ["z"])],
        ]
        for tasks in examples:
            before = copy.deepcopy(tasks)
            records = list(tasks)
            deps = [record.get("deps") for record in tasks]
            with self.subTest(tasks=tasks):
                self.assert_invalid(tasks)
                self.assertEqual(tasks, before)
                for i, record in enumerate(records):
                    self.assertIs(tasks[i], record)
                    self.assertIs(tasks[i].get("deps"), deps[i])

    def test_small_dags_against_exhaustive_independent_oracle(self):
        # Enumerate orders only in this small test oracle, never in production.
        # The construction order deliberately differs from lexical ID order.
        ids = ["d", "b", "a", "c"]
        possible_edges = list(itertools.combinations(ids, 2))
        for mask in range(1 << len(possible_edges)):
            edges = [edge for i, edge in enumerate(possible_edges) if mask & (1 << i)]
            tasks = [task(task_id, i + 1, [a for a, b in edges if b == task_id])
                     for i, task_id in enumerate(ids)]
            valid_orders = [order for order in itertools.permutations(ids)
                            if all(order.index(a) < order.index(b) for a, b in edges)]
            expected_order = min(valid_orders)

            # Times are longest path lengths, computed by independently walking
            # every prerequisite path in these tiny acyclic fixtures.
            duration = {record["id"]: float(record["duration"]) for record in tasks}

            def finish(task_id):
                parents = [a for a, b in edges if b == task_id]
                return duration[task_id] + max((finish(parent) for parent in parents), default=0.0)

            for input_order in [tasks, tasks[::-1]]:
                with self.subTest(mask=mask, input_ids=[record["id"] for record in input_order]):
                    result = schedule(input_order)
                    self.assertEqual(tuple(result), expected_order)
                    for task_id in ids:
                        self.assertEqual(result[task_id], {"start": finish(task_id) - duration[task_id],
                                                          "finish": finish(task_id)})


if __name__ == "__main__":
    unittest.main()
