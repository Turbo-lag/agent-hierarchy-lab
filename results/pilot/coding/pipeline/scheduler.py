"""Validate and schedule dependency graphs with unlimited worker capacity."""

import heapq
import math


def schedule(tasks):
    """Return earliest task times in the smallest lexical topological order.

    Invalid input, cycles, and nonfinite scheduling arithmetic raise ValueError.
    Caller-owned lists, dictionaries, and dependency lists are never modified.
    """
    if not isinstance(tasks, list):
        raise ValueError("tasks must be a list")

    durations = {}
    dependencies = {}
    for task in tasks:
        if not isinstance(task, dict) or not {"id", "duration", "deps"} <= task.keys():
            raise ValueError("each task must contain id, duration, and deps")
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
        except (OverflowError, ValueError) as exc:
            raise ValueError("duration cannot be converted to a finite float") from exc
        if not math.isfinite(duration) or duration < 0:
            raise ValueError("duration must be finite and nonnegative")

        deps = task["deps"]
        if not isinstance(deps, list):
            raise ValueError("deps must be a list")
        if any(not isinstance(dep, str) for dep in deps):
            raise ValueError("dependency IDs must be strings")
        durations[task_id] = duration
        dependencies[task_id] = set(deps)

    dependents = {task_id: [] for task_id in durations}
    indegrees = {}
    for task_id, deps in dependencies.items():
        indegrees[task_id] = len(deps)
        for dep in deps:
            if dep not in durations:
                raise ValueError("unknown dependency")
            if dep == task_id:
                raise ValueError("a task cannot depend on itself")
            dependents[dep].append(task_id)

    ready = [task_id for task_id, degree in indegrees.items() if degree == 0]
    heapq.heapify(ready)
    result = {}
    while ready:
        task_id = heapq.heappop(ready)
        start = max((result[dep]["finish"] for dep in dependencies[task_id]), default=0.0)
        finish = start + durations[task_id]
        if not math.isfinite(start) or not math.isfinite(finish):
            raise ValueError("computed schedule times must be finite")
        result[task_id] = {"start": start, "finish": finish}
        for dependent in dependents[task_id]:
            indegrees[dependent] -= 1
            if indegrees[dependent] == 0:
                heapq.heappush(ready, dependent)

    if len(result) != len(durations):
        raise ValueError("dependency graph contains a cycle")
    return result
