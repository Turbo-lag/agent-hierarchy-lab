"""Validate and construct an earliest-start dependency schedule."""

import heapq
import math


def schedule(tasks):
    """Return timing records in the smallest lexicographic topological order.

    Durations and times are binary64 floats. Invalid input, dependency cycles,
    and nonfinite durations or computed times raise ValueError. Input objects
    are never modified.
    """
    if not isinstance(tasks, list):
        raise ValueError("tasks must be a list")

    durations = {}
    dependencies = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("each task must be a dictionary")
        if not all(key in task for key in ("id", "duration", "deps")):
            raise ValueError("each task requires id, duration, and deps")

        task_id = task["id"]
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task IDs must be nonempty strings")
        if task_id in durations:
            raise ValueError("task IDs must be unique")

        duration = task["duration"]
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise ValueError("duration must be an int or float, excluding bool")
        try:
            duration = float(duration)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError("duration must convert to a finite float") from exc
        if not math.isfinite(duration) or duration < 0:
            raise ValueError("duration must be finite and nonnegative")
        if not isinstance(task["deps"], list):
            raise ValueError("deps must be a list")

        durations[task_id] = duration
        dependencies[task_id] = task["deps"]

    # Resolve edges only after all IDs have been collected, allowing forward
    # references. New adjacency lists and sets leave the caller's lists intact.
    successors = {task_id: [] for task_id in durations}
    indegrees = {}
    for task_id, deps in dependencies.items():
        unique_deps = set()
        for dep in deps:
            if not isinstance(dep, str) or not dep:
                raise ValueError("dependency IDs must be nonempty strings")
            if dep not in durations:
                raise ValueError("unknown dependency")
            if dep == task_id:
                raise ValueError("a task cannot depend on itself")
            unique_deps.add(dep)
        indegrees[task_id] = len(unique_deps)
        for dep in unique_deps:
            successors[dep].append(task_id)

    ready = [task_id for task_id, degree in indegrees.items() if degree == 0]
    heapq.heapify(ready)
    starts = {task_id: 0.0 for task_id in durations}
    result = {}
    while ready:
        task_id = heapq.heappop(ready)
        start = starts[task_id]
        finish = start + durations[task_id]
        if not math.isfinite(start) or not math.isfinite(finish):
            raise ValueError("computed schedule times must be finite")
        result[task_id] = {"start": start, "finish": finish}

        for successor in successors[task_id]:
            starts[successor] = max(starts[successor], finish)
            indegrees[successor] -= 1
            if indegrees[successor] == 0:
                heapq.heappush(ready, successor)

    if len(result) != len(durations):
        raise ValueError("dependencies contain a directed cycle")
    return result
