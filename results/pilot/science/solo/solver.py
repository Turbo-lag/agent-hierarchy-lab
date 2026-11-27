"""Conservative, second-order solver for -(k u')' = f on [0, 1]."""

import math
from numbers import Real


def _finite_real(value, name):
    """Normalize real scalars while rejecting bool and nonfinite values."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real scalar, excluding bool")
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite real scalar") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def solve(n, k, f, left=0.0, right=0.0):
    """Return plain lists of nodes and values, including Dirichlet endpoints.

    ``n`` is an integer number of intervals, at least two (not bool).
    Coefficients are sampled only at faces and sources only at interior nodes.
    Invalid input values raise ValueError; exceptions from callbacks propagate.
    The Thomas tridiagonal algorithm uses O(n) work and storage.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError("n must be an int >= 2, excluding bool")
    if not callable(k) or not callable(f):
        raise ValueError("k and f must be callable")
    left = _finite_real(left, "left")
    right = _finite_real(right, "right")
    h = 1.0 / n
    x = [i / n for i in range(n + 1)]
    faces = []
    for i in range(n):
        coefficient = _finite_real(k((i + 0.5) / n), "k at face")
        if coefficient <= 0.0:
            raise ValueError("k must be strictly positive at every sampled face")
        faces.append(coefficient)

    # Multiply the finite-difference equations by h^2. Interior unknown j
    # corresponds to node i=j+1; the two adjacent faces are j and j+1.
    diagonal = [faces[j] + faces[j + 1] for j in range(n - 1)]
    rhs = [h * h * _finite_real(f(x[i]), "f at node")
           for i in range(1, n)]
    rhs[0] += faces[0] * left
    rhs[-1] += faces[-1] * right

    # Positive face coefficients make the Dirichlet matrix positive definite,
    # so elimination has positive pivots and needs no pivoting.
    for j in range(1, n - 1):
        factor = faces[j] / diagonal[j - 1]
        diagonal[j] -= factor * faces[j]
        rhs[j] += factor * rhs[j - 1]

    u = [left] + [0.0] * (n - 1) + [right]
    u[n - 1] = rhs[-1] / diagonal[-1]
    for j in range(n - 3, -1, -1):
        u[j + 1] = (rhs[j] + faces[j + 1] * u[j + 2]) / diagonal[j]
    return x, u
