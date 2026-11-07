"""Evaluator-positive controls. Never supplied to measured-run workspaces."""
import heapq
import math


def schedule(tasks):
    if not isinstance(tasks, list):
        raise ValueError('tasks must be a list')
    by_id = {}
    for item in tasks:
        if not isinstance(item, dict):
            raise ValueError('task must be dict')
        name, duration, deps = item.get('id'), item.get('duration'), item.get('deps')
        if not isinstance(name, str) or not name or name in by_id:
            raise ValueError('invalid or duplicate id')
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise ValueError('invalid duration')
        try:
            duration = float(duration)
            valid = math.isfinite(duration) and duration >= 0
        except OverflowError:
            valid = False
        if not valid or not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            raise ValueError('invalid duration or deps')
        by_id[name] = (duration, set(deps))
    successors = {name: [] for name in by_id}
    degrees = {}
    for name, (_, deps) in by_id.items():
        degrees[name] = len(deps)
        for dep in deps:
            if dep not in by_id:
                raise ValueError('unknown dependency')
            successors[dep].append(name)
    ready = [name for name, degree in degrees.items() if degree == 0]
    heapq.heapify(ready)
    out = {}
    while ready:
        name = heapq.heappop(ready)
        duration, deps = by_id[name]
        start = max((out[d]['finish'] for d in deps), default=0)
        finish = start + duration
        if not math.isfinite(finish):
            raise ValueError('nonfinite finish')
        out[name] = dict(start=start, finish=finish)
        for nxt in successors[name]:
            degrees[nxt] -= 1
            if degrees[nxt] == 0:
                heapq.heappush(ready, nxt)
    if len(out) != len(by_id):
        raise ValueError('cycle')
    return out


def real(v, positive=False):
    if isinstance(v, bool) or not isinstance(v, (float, int)):
        raise ValueError('expected real number')
    if not math.isfinite(v) or (positive and v <= 0):
        raise ValueError('invalid value')
    return float(v)


def solve(n, k, f, left=0., right=0.):
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError('invalid grid')
    if not callable(k) or not callable(f):
        raise ValueError('expected functions')
    left, right = real(left), real(right)
    face = [real(k((i+.5)/n), positive=True) for i in range(n)]
    # Equations scaled by h^2; boundary elimination precedes Thomas elimination.
    diag = [face[i]+face[i+1] for i in range(n-1)]
    rhs = [real(f((i+1)/n))/(n*n) for i in range(n-1)]
    rhs[0] += face[0]*left
    rhs[-1] += face[-1]*right
    for i in range(1, n-1):
        factor = -face[i]/diag[i-1]
        diag[i] -= factor*(-face[i])
        rhs[i] -= factor*rhs[i-1]
    interior = [0.]*(n-1)
    interior[-1] = rhs[-1]/diag[-1]
    for i in range(n-3, -1, -1):
        interior[i] = (rhs[i]+face[i+1]*interior[i+1])/diag[i]
    return [i/n for i in range(n+1)], [left, *interior, right]
