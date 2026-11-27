"""Earliest-start scheduling with deterministic dependency-ready ordering."""

import heapq
import math


def schedule(tasks):
    """Return an earliest-start schedule in lexicographic topological order.

    Inputs are validated without mutation. Invalid data, cyclic dependencies,
    and nonfinite timing arithmetic raise ValueError.
    """
    if not isinstance(tasks, list):
        raise ValueError('tasks must be a list')

    durations = {}
    dependencies = {}
    for task in tasks:
        if not isinstance(task, dict) or not {'id', 'duration', 'deps'} <= task.keys():
            raise ValueError('each task must be a dictionary with id, duration, and deps')
        task_id = task['id']
        if not isinstance(task_id, str) or not task_id:
            raise ValueError('task IDs must be nonempty strings')
        if task_id in durations:
            raise ValueError('duplicate task ID')

        duration = task['duration']
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise ValueError('duration must be an int or float, excluding bool')
        try:
            duration = float(duration)
        except (OverflowError, ValueError, TypeError) as exc:
            raise ValueError('duration cannot be converted to a finite float') from exc
        if not math.isfinite(duration) or duration < 0:
            raise ValueError('duration must be finite and nonnegative')

        deps = task['deps']
        if not isinstance(deps, list):
            raise ValueError('deps must be a list')
        if any(not isinstance(dep, str) or not dep for dep in deps):
            raise ValueError('dependencies must be nonempty string IDs')
        durations[task_id] = duration
        dependencies[task_id] = set(deps)

    successors = {task_id: [] for task_id in durations}
    indegree = {}
    for task_id, deps in dependencies.items():
        indegree[task_id] = len(deps)
        for dep in deps:
            if dep not in durations:
                raise ValueError('unknown dependency')
            if dep == task_id:
                raise ValueError('self-dependency')
            successors[dep].append(task_id)

    ready = [task_id for task_id, count in indegree.items() if count == 0]
    heapq.heapify(ready)
    starts = {task_id: 0.0 for task_id in durations}
    result = {}
    while ready:
        task_id = heapq.heappop(ready)
        start = starts[task_id]
        finish = start + durations[task_id]
        if not math.isfinite(start) or not math.isfinite(finish):
            raise ValueError('computed schedule time is nonfinite')
        result[task_id] = {'start': start, 'finish': finish}
        for successor in successors[task_id]:
            starts[successor] = max(starts[successor], finish)
            indegree[successor] -= 1
            if indegree[successor] == 0:
                heapq.heappush(ready, successor)

    if len(result) != len(durations):
        raise ValueError('dependency cycle')
    return result
