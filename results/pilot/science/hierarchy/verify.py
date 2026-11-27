#!/usr/bin/env python3
"""Compute manufactured-solution errors and write reproducible JSON evidence."""

import argparse
import json
import math
from pathlib import Path

from solver import solve


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def measure(n, k, f, exact, left, right):
    x, u = solve(n, k, f, left, right)
    h = 1.0 / n
    errors = [u_i - exact(x_i) for x_i, u_i in zip(x, u)]
    residuals = [
        (k((i - 0.5) / n) * (u[i] - u[i - 1])
         - k((i + 0.5) / n) * (u[i + 1] - u[i])) / (h * h) - f(x[i])
        for i in range(1, n)
    ]
    boundary_error = max(abs(u[0] - left), abs(u[-1] - right))
    require(boundary_error == 0.0, "Boundary values were not enforced")
    return {
        "n": n,
        "h": h,
        "max_absolute_nodal_error": max(map(abs, errors)),
        "discrete_l2_error": math.sqrt(h * math.fsum(e * e for e in errors[1:-1])),
        "max_absolute_algebraic_residual": max(map(abs, residuals)),
        "max_absolute_boundary_error": boundary_error,
    }


def contract_checks():
    unit = lambda x: 1.0
    zero = lambda x: 0.0
    bad = [
        ("n_bool", (True, unit, zero), {}),
        ("n_float", (4.0, unit, zero), {}),
        ("n_too_small", (1, unit, zero), {}),
        ("k_noncallable", (4, 1.0, zero), {}),
        ("f_noncallable", (4, unit, 0.0), {}),
    ]
    for label, value in [("zero", 0.0), ("negative", -1.0),
                         ("nan", math.nan), ("infinity", math.inf),
                         ("bool", True), ("complex", 1 + 0j),
                         ("string", "1")]:
        bad.append((f"k_{label}", (4, lambda x, v=value: v, zero), {}))
    for label, value in [("nan", math.nan), ("infinity", math.inf),
                         ("bool", False), ("complex", 1 + 0j),
                         ("string", "1")]:
        bad.append((f"f_{label}", (4, unit, lambda x, v=value: v), {}))
        for endpoint in ("left", "right"):
            bad.append((f"{endpoint}_{label}", (4, unit, zero), {endpoint: value}))
    checked = []
    for label, args, kwargs in bad:
        try:
            solve(*args, **kwargs)
        except ValueError:
            checked.append(label)
        else:
            raise AssertionError(f"Invalid input accepted: {label}")

    def callback_failure(x):
        raise RuntimeError("intentional callback failure")

    for k, f in ((callback_failure, zero), (unit, callback_failure)):
        try:
            solve(4, k, f)
        except RuntimeError as exc:
            require(str(exc) == "intentional callback failure", "Wrong callback exception")
        else:
            raise AssertionError("Callback exception did not propagate")

    k_points, f_points = [], []

    def tracked_k(x):
        k_points.append(x)
        return 1.0 if x not in (0.0, 1.0) else -1.0

    def tracked_f(x):
        f_points.append(x)
        return 0.0

    solve(4, tracked_k, tracked_f)
    require(k_points == [0.125, 0.375, 0.625, 0.875], "Incorrect coefficient sampling")
    require(f_points == [0.25, 0.5, 0.75], "Incorrect source sampling")

    affine = []
    for n in (2, 16, 128):
        # u=-2+5x with k=1+x gives f=-5, including nonzero endpoints.
        row = measure(n, lambda x: 1 + x, lambda x: -5.0,
                      lambda x: -2 + 5 * x, -2.0, 3.0)
        require(row["max_absolute_nodal_error"] < 1e-10, "Affine check failed")
        affine.append(row)
    return {"invalid_input_checks_passed": checked,
            "callback_exception_propagation": "passed (k and f)",
            "sampling_locations": "passed",
            "nonzero_boundary_affine": affine}


def study():
    pi = math.pi
    cases = [
        ("constant_coefficient_sine", "k=1; u=sin(pi*x); f=pi^2*sin(pi*x)",
         lambda x: 1.0, lambda x: pi * pi * math.sin(pi * x),
         lambda x: math.sin(pi * x), 0.0, 0.0),
        ("variable_coefficient_sine_plus_x",
         "k=1+x; u=sin(pi*x)+x; f=(1+x)*pi^2*sin(pi*x)-pi*cos(pi*x)-1",
         lambda x: 1 + x,
         lambda x: (1 + x) * pi * pi * math.sin(pi * x) - pi * math.cos(pi * x) - 1,
         lambda x: math.sin(pi * x) + x, 0.0, 1.0),
    ]
    results = []
    for name, definition, k, f, exact, left, right in cases:
        rows = [measure(n, k, f, exact, left, right) for n in (16, 32, 64, 128)]
        for index, row in enumerate(rows):
            row["max_error_observed_order"] = None
            row["l2_error_observed_order"] = None
            if index:
                previous = rows[index - 1]
                row["max_error_observed_order"] = math.log2(
                    previous["max_absolute_nodal_error"] / row["max_absolute_nodal_error"])
                row["l2_error_observed_order"] = math.log2(
                    previous["discrete_l2_error"] / row["discrete_l2_error"])
                for key in ("max_error_observed_order", "l2_error_observed_order"):
                    require(1.8 < row[key] < 2.2, f"Unexpected refinement trend: {name}, {key}")
        results.append({"name": name, "definition": definition, "grids": rows})
    return {
        "provenance": "Computed against analytical manufactured solutions; not experimental data or physical validation.",
        "error_definitions": {
            "max_absolute_nodal_error": "max over all nodes |u_h-u_exact|",
            "discrete_l2_error": "sqrt(h*sum over interior nodes (u_h-u_exact)^2)",
            "observed_order": "log2(error at previous grid / error at current grid)",
            "max_absolute_algebraic_residual": "max interior |[k_left*(u_i-u_previous)-k_right*(u_next-u_i)]/h^2-f(x_i)|",
        },
        "cases": results,
        "checks": contract_checks(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("verification.json"))
    args = parser.parse_args()
    result = study()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}: two manufactured cases, four grids each; checks passed.")


if __name__ == "__main__":
    main()
