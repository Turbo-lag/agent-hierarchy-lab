"""Conservative centered solver for -(k u')' = f on the unit interval."""

import math
from numbers import Real


def _finite_real(value, name):
    """Return a floating-point real scalar or raise the contract's ValueError."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number (excluding bool)")
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite real number")
    return result


def solve(n, k, f, left=0.0, right=0.0):
    """Return node and solution lists for n equal intervals.

    k is evaluated only at the n face midpoints; f only at interior nodes.
    Evaluated values and boundaries must be finite real scalars, excluding
    bool, and the face coefficients must be strictly positive. The tridiagonal
    system is solved with Thomas elimination using O(n) work and storage.
    Exceptions raised by the supplied callables themselves propagate.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError("n must be an integer >= 2 (excluding bool)")
    if not callable(k) or not callable(f):
        raise ValueError("k and f must be callable")
    left = _finite_real(left, "left")
    right = _finite_real(right, "right")

    h = 1.0 / n
    x = [i / n for i in range(n + 1)]
    faces = []
    for i in range(n):
        coefficient = _finite_real(k((i + 0.5) / n), "k at a face midpoint")
        if coefficient <= 0.0:
            raise ValueError("k must be strictly positive at every face midpoint")
        faces.append(coefficient)

    interior_count = n - 1
    diagonal = [faces[i] + faces[i + 1] for i in range(interior_count)]
    rhs = [h * h * _finite_real(f(x[i]), "f at an interior node")
           for i in range(1, n)]
    # Eliminate known boundary entries after multiplying each equation by h^2.
    # For n=2 both contributions correctly enter the same sole interior row.
    rhs[0] += faces[0] * left
    rhs[-1] += faces[-1] * right

    # Positive face coefficients give a symmetric positive definite matrix,
    # hence positive pivots: pivoting is unnecessary in the supported range.
    for i in range(1, interior_count):
        multiplier = -faces[i] / diagonal[i - 1]
        diagonal[i] += multiplier * faces[i]
        rhs[i] -= multiplier * rhs[i - 1]

    rhs[-1] /= diagonal[-1]
    for i in range(interior_count - 2, -1, -1):
        rhs[i] = (rhs[i] + faces[i + 1] * rhs[i + 1]) / diagonal[i]
    return x, [left] + rhs + [right]
