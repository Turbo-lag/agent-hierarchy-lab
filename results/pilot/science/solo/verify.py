#!/usr/bin/env python3.14
"""Generate reproducible manufactured-solution evidence using only stdlib."""

import json
import math
from pathlib import Path
import platform

from solver import solve


GRIDS = (16, 32, 64, 128)


def residuals(x, u, k, f):
    """Evaluate A_h u - f independently of the solver's elimination arrays."""
    n = len(x) - 1
    h = 1.0 / n
    return [
        (k((i - 0.5) / n) * (u[i] - u[i - 1])
         - k((i + 0.5) / n) * (u[i + 1] - u[i])) / (h * h)
        - f(x[i])
        for i in range(1, n)
    ]


def study(name, coefficient, source, exact, left, right):
    rows = []
    for n in GRIDS:
        x, u = solve(n, coefficient, source, left, right)
        errors = [abs(value - exact(node)) for node, value in zip(x, u)]
        row = {
            "n": n,
            "h": 1.0 / n,
            "max_error": max(errors),
            "l2_error": math.sqrt(math.fsum(e * e for e in errors[1:-1]) / n),
            "max_order": None,
            "l2_order": None,
            "max_algebraic_residual": max(map(abs, residuals(x, u, coefficient, source))),
            "boundary_error": max(abs(u[0] - left), abs(u[-1] - right)),
        }
        if rows:
            for norm in ("max", "l2"):
                row[norm + "_order"] = math.log2(rows[-1][norm + "_error"] / row[norm + "_error"])
        rows.append(row)
    return {"name": name, "grids": rows}


def invalid_checks():
    checks = {}
    base = {"n": 8, "k": lambda x: 1.0, "f": lambda x: 0.0}
    bad_inputs = [
        ("n_bool", {"n": True}), ("n_float", {"n": 8.0}),
        ("n_small", {"n": 1}), ("k_not_callable", {"k": 1}),
        ("f_not_callable", {"f": None}),
    ]
    for label, value in (("nan", math.nan), ("infinity", math.inf),
                         ("negative_infinity", -math.inf), ("bool", True),
                         ("complex", 1j), ("string", "1"), ("none", None)):
        for argument in ("k", "f", "left", "right"):
            replacement = (lambda x, v=value: v) if argument in ("k", "f") else value
            bad_inputs.append((argument + "_" + label, {argument: replacement}))
    for label, value in (("zero", 0.0), ("negative", -1.0)):
        bad_inputs.append(("k_" + label, {"k": lambda x, v=value: v}))
    for label, overrides in bad_inputs:
        try:
            solve(**(base | overrides))
        except ValueError:
            checks[label] = True
        else:
            checks[label] = False
    return checks


def build_verification():
    pi = math.pi
    cases = [
        study("constant_k_sine", lambda x: 1.0,
              lambda x: pi * pi * math.sin(pi * x),
              lambda x: math.sin(pi * x), 0.0, 0.0),
        study("linear_k_sine_plus_x", lambda x: 1.0 + x,
              lambda x: (1 + x) * pi * pi * math.sin(pi * x) - pi * math.cos(pi * x) - 1,
              lambda x: math.sin(pi * x) + x, 0.0, 1.0),
    ]
    affine = []
    for n in (2, 16, 128):
        x, u = solve(n, lambda x: 1 + x, lambda x: -3.0, 2.0, 5.0)
        error = max(abs(value - (2 + 3 * node)) for node, value in zip(x, u))
        affine.append({"n": n, "max_error": error,
                       "boundary_error": max(abs(u[0] - 2), abs(u[-1] - 5))})
    invalid = invalid_checks()
    checks = {
        "boundaries_exact": all(row["boundary_error"] == 0 for case in cases for row in case["grids"]),
        "second_order": all(1.8 < row[key] < 2.2 for case in cases
                            for row in case["grids"][1:] for key in ("max_order", "l2_order")),
        "small_algebraic_residual": all(row["max_algebraic_residual"] < 1e-8
                                        for case in cases for row in case["grids"]),
        "affine_solution": all(row["max_error"] < 1e-10 and row["boundary_error"] == 0
                               for row in affine),
        "invalid_inputs_rejected": all(invalid.values()),
    }
    return {
        "schema_version": 1,
        "data_kind": "numerically computed errors against analytical manufactured solutions; not experimental data",
        "python_version": platform.python_version(),
        "error_definitions": {
            "max_error": "max over all nodes of abs(u_h - u_exact)",
            "l2_error": "sqrt(h * sum of squared interior nodal errors)",
            "order": "log2(error on previous grid / error on current grid); first grid null",
            "max_algebraic_residual": "max over interior nodes of abs(A_h u_h - f); original equations include 1/h^2",
        },
        "cases": cases,
        "affine_case": {"k": "1+x", "u": "2+3*x", "f": "-3", "grids": affine},
        "invalid_input_checks": invalid,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }


def main():
    result = build_verification()
    destination = Path(__file__).resolve().with_name("verification.json")
    destination.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote {destination.name}; all checks passed: {result['all_checks_passed']}")
    if not result["all_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
