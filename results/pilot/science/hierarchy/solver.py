"""Conservative finite differences for a one-dimensional elliptic equation."""

import math
from numbers import Real


def _real_finite(value, name):
    """Normalize an evaluated real scalar, rejecting bool and complex values."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real scalar (not bool)")
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite real scalar") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def solve(n, k, f, left=0.0, right=0.0):
    """Solve -(k u')'=f on [0, 1] with prescribed endpoint values.

    Coefficients are evaluated only at face midpoints, and sources only at
    interior nodes. The symmetric tridiagonal system uses O(n) work/storage.
    Callable exceptions propagate; invalid returned values raise ValueError.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError("n must be an integer >= 2 (not bool)")
    if not callable(k) or not callable(f):
        raise ValueError("k and f must be callable")
    left = _real_finite(left, "left")
    right = _real_finite(right, "right")
    h = 1.0 / n
    x = [i / n for i in range(n + 1)]
    faces = []
    for j in range(n):
        coefficient = _real_finite(k((j + 0.5) / n), "k at a face")
        if coefficient <= 0.0:
            raise ValueError("k must be strictly positive at every face")
        faces.append(coefficient)
    rhs = [_real_finite(f(x[i]), "f at an interior node") * h * h
           for i in range(1, n)]
    rhs[0] += faces[0] * left
    rhs[-1] += faces[-1] * right

    # Eliminate the lower diagonal. Positive faces imply positive pivots.
    diagonal = [faces[j] + faces[j + 1] for j in range(n - 1)]
    for j in range(1, n - 1):
        factor = faces[j] / diagonal[j - 1]
        diagonal[j] -= factor * faces[j]
        rhs[j] += factor * rhs[j - 1]

    u = [left] + [0.0] * (n - 1) + [right]
    # Boundary contributions already entered rhs; start with the last unknown.
    u[n - 1] = rhs[-1] / diagonal[-1]
    for j in range(n - 3, -1, -1):
        u[j + 1] = (rhs[j] + faces[j + 1] * u[j + 2]) / diagonal[j]
    return x, u
