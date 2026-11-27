"""Conservative second-order solver for -(k u')' = f on [0, 1]."""

import math
from decimal import Decimal
from numbers import Real


def _finite_real(value, name):
    """Accept real numeric scalars, but not booleans or numeric strings."""
    if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):
        raise ValueError(f"{name} must be a finite real number")
    try:
        value = float(value)
    except (OverflowError, ValueError, TypeError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite real number")
    return value


def solve(n, k, f, left=0.0, right=0.0):
    """Return plain node/value lists for the conservative centered scheme.

    Coefficients are evaluated only at faces; sources only at interior nodes.
    Invalid arguments or returned values raise ValueError. Exceptions from
    calling user functions propagate. Work and auxiliary storage are O(n).
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError("n must be an integer >= 2, excluding bool")
    if not callable(k) or not callable(f):
        raise ValueError("k and f must be callable")
    left = _finite_real(left, "left")
    right = _finite_real(right, "right")
    h = 1.0 / n
    x = [i * h for i in range(n + 1)]
    x[-1] = 1.0
    faces = []
    for j in range(n):
        value = _finite_real(k((j + 0.5) * h), "k(face)")
        if value <= 0.0:
            raise ValueError("k must be strictly positive at every face")
        faces.append(value)

    diagonal = [faces[i] + faces[i + 1] for i in range(n - 1)]
    rhs = [_finite_real(f(x[i]), "f(node)") * h * h
           for i in range(1, n)]
    rhs[0] += faces[0] * left
    rhs[-1] += faces[-1] * right

    # The tridiagonal Dirichlet matrix is symmetric positive definite.
    # Thomas elimination therefore needs no pivoting for valid coefficients.
    for row in range(1, n - 1):
        ratio = faces[row] / diagonal[row - 1]
        diagonal[row] -= ratio * faces[row]
        rhs[row] += ratio * rhs[row - 1]

    u = [left] + [0.0] * (n - 1) + [right]
    u[n - 1] = rhs[-1] / diagonal[-1]
    for row in range(n - 3, -1, -1):
        u[row + 1] = (rhs[row] + faces[row + 1] * u[row + 2]) / diagonal[row]
    return x, u
