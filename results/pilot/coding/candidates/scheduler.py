"""Validate and compute deterministic earliest-start dependency schedules."""

import heapq
import math


def schedule(tasks):
    """Return an earliest-start schedule in lexicographic topological order.

    Invalid task data, graph cycles, and nonfinite scheduling arithmetic raise
    ValueError. The supplied list and its dictionaries/dependency lists are
    never modified.
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
        except (OverflowError, TypeError, ValueError) as error:
            raise ValueError("duration cannot be converted to a finite float") from error
        if not math.isfinite(duration) or duration < 0:
            raise ValueError("duration must be finite and nonnegative")

        deps = task["deps"]
        if not isinstance(deps, list):
            raise ValueError("deps must be a list")
        unique_deps = set()
        for dep in deps:
            if not isinstance(dep, str) or not dep:
                raise ValueError("dependency IDs must be nonempty strings")
            if dep == task_id:
                raise ValueError("a task cannot depend on itself")
            unique_deps.add(dep)
        durations[task_id] = duration
        dependencies[task_id] = unique_deps

    children = {task_id: [] for task_id in durations}
    remaining = {}
    for task_id, deps in dependencies.items():
        remaining[task_id] = len(deps)
        for dep in deps:
            if dep not in durations:
                raise ValueError("unknown dependency")
            children[dep].append(task_id)

    ready = [task_id for task_id, count in remaining.items() if count == 0]
    heapq.heapify(ready)
    starts = dict.fromkeys(durations, 0.0)
    result = {}
    while ready:
        task_id = heapq.heappop(ready)
        start = starts[task_id]
        finish = start + durations[task_id]
        if not math.isfinite(start) or not math.isfinite(finish):
            raise ValueError("schedule contains a nonfinite time")
        result[task_id] = {"start": start, "finish": finish}
        for child in children[task_id]:
            starts[child] = max(starts[child], finish)
            remaining[child] -= 1
            if remaining[child] == 0:
                heapq.heappush(ready, child)

    if len(result) != len(durations):
        raise ValueError("dependency graph contains a cycle")
    return result
