#!/usr/bin/env python3
"""Reproduce analytical manufactured-solution checks using only the stdlib."""

import argparse
import json
import math
from pathlib import Path

from solver import solve


GRIDS = (16, 32, 64, 128)


def _grid_result(n, k, f, exact, left, right, previous):
    x, u = solve(n, k, f, left=left, right=right)
    if type(x) is not list or type(u) is not list:
        raise AssertionError("solve must return two plain lists")
    if len(x) != n + 1 or len(u) != n + 1:
        raise AssertionError("solve returned an incorrect node count")
    if x != [i / n for i in range(n + 1)]:
        raise AssertionError("solve returned an incorrect uniform grid")
    if not all(math.isfinite(value) for value in u):
        raise AssertionError("solve returned a nonfinite solution")
    h = 1.0 / n
    errors = [abs(value - exact(node)) for node, value in zip(x, u)]
    max_error = max(errors)
    l2_error = math.sqrt(h * math.fsum(e * e for e in errors[1:-1]))
    residuals = [
        (
            k((i - 0.5) * h) * (u[i] - u[i - 1])
            - k((i + 0.5) * h) * (u[i + 1] - u[i])
        ) / (h * h) - f(x[i])
        for i in range(1, n)
    ]
    return {
        "n": n,
        "h": h,
        "max_absolute_nodal_error": max_error,
        "discrete_l2_error": l2_error,
        "max_error_order": (
            None if previous is None else
            math.log2(previous["max_absolute_nodal_error"] / max_error)
        ),
        "l2_error_order": (
            None if previous is None else
            math.log2(previous["discrete_l2_error"] / l2_error)
        ),
        "max_absolute_algebraic_residual": max(abs(r) for r in residuals),
        "boundary_values": [u[0], u[-1]],
        "boundary_enforcement_passed": u[0] == left and u[-1] == right,
    }


def _invalid_input_checks():
    valid = {"n": 4, "k": lambda x: 1.0, "f": lambda x: 0.0}
    cases = []
    for label, value in (
        ("bool", True), ("float", 4.0), ("string", "4"),
        ("none", None), ("one", 1), ("zero", 0), ("negative", -4),
    ):
        cases.append(("n_" + label, {"n": value}))
    cases.extend((
        ("k_noncallable", {"k": 1.0}),
        ("f_noncallable", {"f": 0.0}),
        ("k_zero", {"k": lambda x: 0.0}),
        ("k_negative", {"k": lambda x: -1.0}),
    ))
    invalid_values = (
        ("nan", math.nan), ("positive_infinity", math.inf),
        ("negative_infinity", -math.inf), ("bool", True),
        ("complex", 1.0 + 0j), ("string", "1"), ("none", None),
    )
    for label, value in invalid_values:
        for name in ("k", "f", "left", "right"):
            replacement = (lambda x, value=value: value) if name in ("k", "f") else value
            cases.append((name + "_" + label, {name: replacement}))
    results = []
    for name, changes in cases:
        arguments = dict(valid)
        arguments.update(changes)
        try:
            solve(**arguments)
        except ValueError:
            results.append({"name": name, "passed": True})
        except Exception as error:
            results.append({"name": name, "passed": False,
                            "unexpected_exception": type(error).__name__})
        else:
            results.append({"name": name, "passed": False,
                            "failure": "invalid input accepted"})
    return results


def verify():
    """Compute fresh measurements; no stored reference errors are used."""
    pi = math.pi
    definitions = (
        ("constant_coefficient", "k=1; u=sin(pi*x); f=pi^2*sin(pi*x)",
         lambda x: 1.0, lambda x: pi * pi * math.sin(pi * x),
         lambda x: math.sin(pi * x), 0.0, 0.0),
        ("variable_coefficient", "k=1+x; u=sin(pi*x)+x; f=(1+x)*pi^2*sin(pi*x)-pi*cos(pi*x)-1",
         lambda x: 1.0 + x,
         lambda x: (1.0 + x) * pi * pi * math.sin(pi * x) - pi * math.cos(pi * x) - 1.0,
         lambda x: math.sin(pi * x) + x, 0.0, 1.0),
    )
    cases = []
    for name, formula, k, f, exact, left, right in definitions:
        rows = []
        for n in GRIDS:
            rows.append(_grid_result(n, k, f, exact, left, right,
                                     rows[-1] if rows else None))
        cases.append({"name": name, "formula": formula, "grids": rows})
    affine = _grid_result(64, lambda x: 1.0 + x, lambda x: -2.0,
                          lambda x: 2.0 * x - 0.75, -0.75, 1.25, None)
    affine.update({"formula": "k=1+x; u=2*x-0.75; f=-2",
                   "passed": affine["max_absolute_nodal_error"] < 1e-11
                   and affine["boundary_enforcement_passed"]})
    invalid = _invalid_input_checks()
    checks = {
        "all_manufactured_boundaries_exact": all(
            row["boundary_enforcement_passed"] for case in cases for row in case["grids"]),
        "all_observed_orders_between_1_9_and_2_1": all(
            1.9 < row[key] < 2.1 for case in cases for row in case["grids"][1:]
            for key in ("max_error_order", "l2_error_order")),
        "all_manufactured_algebraic_residuals_below_1e_8": all(
            row["max_absolute_algebraic_residual"] < 1e-8
            for case in cases for row in case["grids"]),
        "nonzero_boundary_affine": affine["passed"],
        "invalid_inputs_raise_value_error": all(result["passed"] for result in invalid),
    }
    return {
        "data_kind": "Computed numerical errors against analytical manufactured solutions; not experimental data or physical validation.",
        "error_definitions": {
            "max_absolute_nodal_error": "max over all nodes of abs(u_h-u_exact)",
            "discrete_l2_error": "sqrt(h * sum over interior nodes of (u_h-u_exact)^2)",
            "orders": "log2(previous_grid_error/current_grid_error); null on first grid",
            "max_absolute_algebraic_residual": "max interior abs(L_h(u_h)-f); unscaled differential-operator residual, distinct from solution error",
        },
        "manufactured_cases": cases,
        "affine_check": affine,
        "invalid_input_checks": invalid,
        "checks": checks,
        "passed": all(checks.values()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("verification.json"))
    arguments = parser.parse_args()
    result = verify()
    arguments.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote {arguments.output}: {'PASS' if result['passed'] else 'FAIL'}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
