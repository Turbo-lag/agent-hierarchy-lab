"""Conservative, linear-work solver for a one-dimensional elliptic equation."""

from decimal import Decimal
import math
from numbers import Real


def _finite_real(value, name):
    """Accept real numeric scalars, including Decimal, but never bool/string."""
    if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):
        raise ValueError(f"{name} must be a finite real number, excluding bool")
    try:
        result = float(value)
    except (ValueError, OverflowError, TypeError) as exc:
        raise ValueError(f"{name} must be representable as a finite float") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def solve(n, k, f, left=0.0, right=0.0):
    """Solve -(k u')' = f on [0, 1] with specified Dirichlet boundaries.

    Return ordinary lists of nodes and solution values. Coefficients are sampled
    only at the n face midpoints; sources only at the n-1 interior nodes.
    The positive-coefficient tridiagonal system uses O(n) time and storage.
    Invalid inputs raise ValueError; exceptions from k or f propagate unchanged.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError("n must be an integer >= 2, excluding bool")
    if not callable(k) or not callable(f):
        raise ValueError("k and f must be callable")
    left = _finite_real(left, "left")
    right = _finite_real(right, "right")
    h = 1.0 / n
    x = [i / n for i in range(n + 1)]
    faces = []
    for j in range(n):
        coefficient = _finite_real(k((j + 0.5) / n), "k at a face")
        if coefficient <= 0.0:
            raise ValueError("k must be strictly positive at every face")
        faces.append(coefficient)

    # Multiply the PDE stencil by h**2 before assembling the system.
    diagonal = [faces[j] + faces[j + 1] for j in range(n - 1)]
    rhs = [h * h * _finite_real(f(x[i]), "f at an interior node")
           for i in range(1, n)]
    rhs[0] += faces[0] * left
    rhs[-1] += faces[-1] * right

    # Thomas elimination: off-diagonal (j, j-1) is -faces[j].
    for j in range(1, n - 1):
        multiplier = -faces[j] / diagonal[j - 1]
        diagonal[j] += multiplier * faces[j]
        rhs[j] -= multiplier * rhs[j - 1]

    u = [left] + [0.0] * (n - 1) + [right]
    u[n - 1] = rhs[-1] / diagonal[-1]
    for j in range(n - 3, -1, -1):
        u[j + 1] = (rhs[j] + faces[j + 1] * u[j + 2]) / diagonal[j]
    return x, u
