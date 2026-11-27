"""Contract regressions and small independent graph-oracle checks.

Run with: python3 -m unittest -v test_solution
"""

import copy
import itertools
import math
import random
import sys
import unittest

from scheduler import schedule


def task(task_id, duration=1, deps=None, **extra):
    return {'id': task_id, 'duration': duration,
            'deps': [] if deps is None else deps, **extra}


def reference_schedule(tasks):
    """Small-input oracle: rescan all remaining tasks, without graph bookkeeping."""
    remaining = {item['id']: item for item in tasks}
    result = {}
    while remaining:
        ready = [key for key, item in remaining.items()
                 if all(dep in result for dep in item['deps'])]
        if not ready:
            raise ValueError('cycle')
        key = min(ready)
        item = remaining.pop(key)
        start = max((result[dep]['finish'] for dep in item['deps']), default=0.0)
        result[key] = {'start': start, 'finish': start + float(item['duration'])}
    return result


class ValidationTests(unittest.TestCase):
    def test_malformed_containers_and_records(self):
        bad_inputs = [None, 3, 'tasks', {}, (), iter([]),
                      [None], [1], ['a'], [[]], [{}],
                      [{'id': 'a'}],
                      [{'id': 'a', 'duration': 1}],
                      [{'duration': 1, 'deps': []}],
                      [{'id': 'a', 'deps': []}]]
        for value in bad_inputs:
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                schedule(value)

    def test_invalid_and_duplicate_ids(self):
        for value in ['', None, 1, True, [], {}, b'a']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule([task(value)])
        with self.assertRaises(ValueError):
            schedule([task('same'), task('same', 2)])

    def test_invalid_durations(self):
        bad_durations = [True, False, None, '1', [], {}, 1 + 0j,
                         -1, -0.01, math.inf, -math.inf, math.nan,
                         10 ** 400, -(10 ** 400)]
        for value in bad_durations:
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule([task('a', value)])

    def test_invalid_dependencies(self):
        for deps in [None, 'a', ('a',), {'a'}, {'a': 1},
                     [None], [1], [True], [[]], [{}], [''], [b'a'], ['missing']]:
            with self.subTest(deps=deps), self.assertRaises(ValueError):
                schedule([{'id': 'b', 'duration': 1, 'deps': deps}])
        with self.assertRaises(ValueError):
            schedule([task('a', deps=['a', 'a'])])

    def test_cycles_including_disconnected_components(self):
        examples = [
            [task('a', deps=['b']), task('b', deps=['a'])],
            [task('a', 0, ['b']), task('b', 0, ['c']), task('c', 0, ['a'])],
            [task('free'), task('a', deps=['b']), task('b', deps=['a']),
             task('blocked', deps=['a'])],
        ]
        for tasks in examples:
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                schedule(tasks)

    def test_computed_overflow(self):
        largest = sys.float_info.max
        with self.assertRaises(ValueError):
            schedule([task('a', largest), task('b', largest, ['a'])])
        # Unlimited workers: independent large durations are not summed.
        result = schedule([task('b', largest), task('a', largest)])
        self.assertEqual(result['b']['finish'], largest)
        result = schedule([task('a', largest), task('b', 0, ['a'])])
        self.assertEqual(result['b']['finish'], largest)


class SchedulingTests(unittest.TestCase):
    def assert_schedule(self, tasks, expected):
        actual = schedule(tasks)
        self.assertEqual(actual, expected)
        self.assertEqual(list(actual), list(expected))
        for times in actual.values():
            self.assertIs(type(times['start']), float)
            self.assertIs(type(times['finish']), float)

    def test_empty_and_independent(self):
        self.assertEqual(schedule([]), {})
        self.assert_schedule([task('z', 2), task('a', 0.5)], {
            'a': {'start': 0.0, 'finish': 0.5},
            'z': {'start': 0.0, 'finish': 2.0},
        })

    def test_forward_dependencies_and_maximum_finish(self):
        self.assert_schedule([
            task('join', 0.5, ['slow', 'fast']),
            task('slow', 7, ['root']), task('root', 2),
            task('fast', 1, ['root']),
        ], {
            'root': {'start': 0.0, 'finish': 2.0},
            'fast': {'start': 2.0, 'finish': 3.0},
            'slow': {'start': 2.0, 'finish': 9.0},
            'join': {'start': 9.0, 'finish': 9.5},
        })

    def test_newly_ready_ids_precede_existing_ready_ids(self):
        # 'a' starts later than 'z' but must be emitted first once 'b' is done.
        self.assert_schedule([task('z', 0), task('a', 1, ['b']), task('b', 10)], {
            'b': {'start': 0.0, 'finish': 10.0},
            'a': {'start': 10.0, 'finish': 11.0},
            'z': {'start': 0.0, 'finish': 0.0},
        })

    def test_duplicate_edges_and_zero_duration(self):
        self.assert_schedule([task('c', 0, ['a', 'b', 'a', 'b']),
                              task('b', -0.0, ['a', 'a']), task('a', 0)], {
            'a': {'start': 0.0, 'finish': 0.0},
            'b': {'start': 0.0, 'finish': 0.0},
            'c': {'start': 0.0, 'finish': 0.0},
        })

    def test_binary64_conversion_and_fractional_arithmetic(self):
        rounded = float(2 ** 53 + 1)
        self.assert_schedule([task('a', 2 ** 53 + 1), task('b', 1, ['a'])], {
            'a': {'start': 0.0, 'finish': rounded},
            'b': {'start': rounded, 'finish': rounded + 1.0},
        })
        result = schedule([task('a', 0.1), task('b', 0.2, ['a'])])
        self.assertEqual(result['b']['finish'], 0.1 + 0.2)
        self.assertEqual(schedule([task('tiny', 5e-324)])['tiny']['finish'], 5e-324)

    def test_lexicographic_string_ids(self):
        ids = ['é', 'a', '2', '10', 'A', ' ']
        self.assertEqual(list(schedule([task(key) for key in ids])), sorted(ids))

    def test_input_immutability_and_no_output_aliasing(self):
        shared_deps = ['root', 'root']
        tasks = [task('z', 0.5, shared_deps, metadata={'nested': [1, 2]}),
                 task('a', 2, shared_deps), task('root', 1)]
        before = copy.deepcopy(tasks)
        task_objects = list(tasks)
        result = schedule(tasks)
        self.assertEqual(tasks, before)
        self.assertTrue(all(left is right for left, right in zip(tasks, task_objects)))
        self.assertIs(tasks[0]['deps'], shared_deps)
        self.assertIs(tasks[1]['deps'], shared_deps)
        result['a']['finish'] = -99
        self.assertEqual(tasks, before)
        self.assertEqual(schedule(tasks)['a']['finish'], 3.0)

    def test_invalid_input_also_remains_unchanged(self):
        for tasks in [[task('z'), task('a', deps=['missing'])],
                      [task('z'), task('a', -1)],
                      [task('z', deps=['a']), task('a', deps=['z'])]]:
            before = copy.deepcopy(tasks)
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                schedule(tasks)
            self.assertEqual(tasks, before)

    def test_long_reverse_input_chain(self):
        count = 5000
        tasks = [task(f't{i:05}', 0.5, [f't{i-1:05}'] if i else [])
                 for i in reversed(range(count))]
        result = schedule(tasks)
        self.assertEqual(list(result), [f't{i:05}' for i in range(count)])
        for i, times in enumerate(result.values()):
            self.assertEqual(times, {'start': i * 0.5, 'finish': (i + 1) * 0.5})

    def test_wide_fan_in_and_fan_out(self):
        leaves = [f'leaf{i:04}' for i in range(1000)]
        tasks = [task('sink', 1, leaves), task('root', 2)]
        tasks.extend(task(key, i / 2, ['root']) for i, key in enumerate(leaves))
        result = schedule(tasks)
        self.assertEqual(list(result), ['root', *leaves, 'sink'])
        self.assertEqual(result['sink'], {'start': 501.5, 'finish': 502.5})

    def test_all_three_vertex_graphs_against_oracle(self):
        ids = ['a', 'b', 'c']
        edges = [(source, target) for source in ids for target in ids if source != target]
        for mask in range(1 << len(edges)):
            tasks = [task(key, i + 0.5,
                          [source for bit, (source, target) in enumerate(edges)
                           if target == key and mask & (1 << bit)])
                     for i, key in enumerate(ids)]
            try:
                expected = reference_schedule(tasks)
            except ValueError:
                with self.subTest(mask=mask), self.assertRaises(ValueError):
                    schedule(tasks)
            else:
                for permutation in itertools.permutations(tasks):
                    with self.subTest(mask=mask, order=[t['id'] for t in permutation]):
                        self.assert_schedule(list(permutation), expected)

    def test_seeded_random_dags_against_oracle(self):
        rng = random.Random(20261113)
        for case in range(150):
            ids = [f't{i:02}' for i in range(rng.randrange(1, 30))]
            rng.shuffle(ids)
            tasks = []
            for i, key in enumerate(ids):
                deps = [dep for dep in ids[:i] if rng.random() < 0.2]
                if deps:
                    deps += rng.choices(deps, k=rng.randrange(4))
                tasks.append(task(key, rng.choice([0, 0.1, 0.25, 1, 3.5]), deps))
            expected = reference_schedule(tasks)
            rng.shuffle(tasks)
            with self.subTest(case=case):
                self.assert_schedule(tasks, expected)


if __name__ == '__main__':
    unittest.main()
