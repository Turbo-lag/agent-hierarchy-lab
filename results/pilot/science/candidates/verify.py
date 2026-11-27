#!/usr/bin/env python3
"""Generate reproducible manufactured-solution verification beside this file."""

import json
import math
from pathlib import Path

from solver import solve


GRIDS = (16, 32, 64, 128)


def study(name, k, f, exact, left, right):
    rows = []
    for n in GRIDS:
        x, u = solve(n, k, f, left, right)
        h = 1.0 / n
        errors = [ui - exact(xi) for xi, ui in zip(x, u)]
        maximum = max(abs(e) for e in errors)
        l2 = math.sqrt(h * math.fsum(e * e for e in errors[1:-1]))
        residual = max(abs((k((i - 0.5) * h) * (u[i] - u[i - 1])
                            - k((i + 0.5) * h) * (u[i + 1] - u[i]))
                           / h**2 - f(x[i])) for i in range(1, n))
        row = {
            "n": n, "h": h, "max_abs_error": maximum,
            "discrete_l2_error": l2,
            "max_error_order": (math.log2(rows[-1]["max_abs_error"] / maximum)
                                if rows else None),
            "l2_error_order": (math.log2(rows[-1]["discrete_l2_error"] / l2)
                               if rows else None),
            "max_abs_algebraic_residual": residual,
            "boundary_error": max(abs(u[0] - left), abs(u[-1] - right)),
        }
        rows.append(row)
    return {"name": name, "left": left, "right": right, "grids": rows}


def run_checks():
    x, u = solve(73, lambda x: 2.5, lambda x: 0.0, -2.0, 3.0)
    affine_error = max(abs(ui - (-2.0 + 5.0 * xi)) for xi, ui in zip(x, u))
    invalid_calls = {
        "bool_n": lambda: solve(True, lambda x: 1, lambda x: 0),
        "small_n": lambda: solve(1, lambda x: 1, lambda x: 0),
        "float_n": lambda: solve(4.0, lambda x: 1, lambda x: 0),
        "noncallable_k": lambda: solve(4, 1, lambda x: 0),
        "noncallable_f": lambda: solve(4, lambda x: 1, 0),
        "zero_k": lambda: solve(4, lambda x: 0, lambda x: 0),
        "negative_k": lambda: solve(4, lambda x: -1, lambda x: 0),
        "nan_k": lambda: solve(4, lambda x: math.nan, lambda x: 0),
        "infinite_f": lambda: solve(4, lambda x: 1, lambda x: math.inf),
        "bool_f": lambda: solve(4, lambda x: 1, lambda x: False),
        "complex_f": lambda: solve(4, lambda x: 1, lambda x: 1j),
        "nan_left": lambda: solve(4, lambda x: 1, lambda x: 0, left=math.nan),
        "bool_right": lambda: solve(4, lambda x: 1, lambda x: 0, right=True),
    }
    rejected = {}
    for name, call in invalid_calls.items():
        try:
            call()
        except ValueError:
            rejected[name] = True
        else:
            rejected[name] = False
    return {
        "affine": {"n": 73, "k": 2.5, "left": -2.0, "right": 3.0,
                   "max_abs_error": affine_error, "tolerance": 1e-11,
                   "passed": affine_error < 1e-11},
        "invalid_inputs_rejected": rejected,
    }


def main():
    pi = math.pi
    cases = [
        study("constant_k_sine", lambda x: 1.0,
              lambda x: pi**2 * math.sin(pi * x),
              lambda x: math.sin(pi * x), 0.0, 0.0),
        study("linear_k_sine_plus_x", lambda x: 1.0 + x,
              lambda x: (1.0 + x) * pi**2 * math.sin(pi * x)
              - pi * math.cos(pi * x) - 1.0,
              lambda x: math.sin(pi * x) + x, 0.0, 1.0),
    ]
    checks = run_checks()
    checks["boundaries_exact"] = all(row["boundary_error"] == 0.0
                                     for case in cases for row in case["grids"])
    checks["second_order"] = all(1.9 < row[key] < 2.1
                                  for case in cases for row in case["grids"][1:]
                                  for key in ("max_error_order", "l2_error_order"))
    result = {
        "data_kind": "analytical manufactured solutions; computed numerical errors",
        "method": "conservative centered face-midpoint finite differences",
        "error_definition": "computed u minus analytical u at nodes",
        "l2_definition": "sqrt(h * sum(interior nodal errors squared))",
        "residual_definition": "max_i abs((k_left*(u_i-u_previous) - k_right*(u_next-u_i))/h^2 - f_i)",
        "order_definition": "log2(error at n / error at 2n); first entry null",
        "physical_validation": False,
        "cases": cases, "checks": checks,
    }
    passed = (checks["affine"]["passed"] and checks["boundaries_exact"]
              and checks["second_order"] and all(checks["invalid_inputs_rejected"].values()))
    result["all_checks_passed"] = passed
    output = Path(__file__).resolve().with_name("verification.json")
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {output}; all_checks_passed={passed}")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
