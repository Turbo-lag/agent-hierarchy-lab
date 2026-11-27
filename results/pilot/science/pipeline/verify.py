#!/usr/bin/env python3
"""Run analytical manufactured-solution verification and write measured JSON."""

import json
import math
from pathlib import Path

from solver import solve


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run_study():
    pi = math.pi
    cases = [
        ("constant_coefficient_sine", "k=1; u=sin(pi*x); f=pi^2*sin(pi*x)",
         lambda x: 1.0, lambda x: math.sin(pi * x),
         lambda x: pi * pi * math.sin(pi * x), 0.0, 0.0),
        ("variable_coefficient_sine_plus_x",
         "k=1+x; u=sin(pi*x)+x; f=(1+x)*pi^2*sin(pi*x)-pi*cos(pi*x)-1",
         lambda x: 1.0 + x, lambda x: math.sin(pi * x) + x,
         lambda x: (1 + x) * pi * pi * math.sin(pi * x)
         - pi * math.cos(pi * x) - 1, 0.0, 1.0),
    ]
    records = []
    boundary_pass = True
    residual_tolerance = 1e-8
    for name, formula, coefficient, exact, source, left, right in cases:
        grids = []
        previous = None
        for n in (16, 32, 64, 128):
            x, u = solve(n, coefficient, source, left, right)
            h = 1.0 / n
            errors = [abs(ui - exact(xi)) for xi, ui in zip(x, u)]
            maximum = max(errors)
            l2 = math.sqrt(h * math.fsum(e * e for e in errors[1:-1]))
            residual = max(abs((coefficient((i - 0.5) / n) * (u[i] - u[i - 1])
                                - coefficient((i + 0.5) / n) * (u[i + 1] - u[i]))
                               / (h * h) - source(x[i])) for i in range(1, n))
            boundary_error = max(abs(u[0] - left), abs(u[-1] - right))
            boundary_pass = boundary_pass and boundary_error == 0.0
            row = {"n": n, "h": h, "max_abs_nodal_error": maximum,
                   "discrete_l2_error": l2,
                   "max_error_order": None if previous is None else
                   math.log2(previous["max_abs_nodal_error"] / maximum),
                   "l2_error_order": None if previous is None else
                   math.log2(previous["discrete_l2_error"] / l2),
                   "max_abs_pde_residual": residual,
                   "max_abs_boundary_error": boundary_error}
            require(residual < residual_tolerance, f"Large residual: {name}, n={n}")
            if previous is not None:
                for field in ("max_error_order", "l2_error_order"):
                    require(1.9 <= row[field] <= 2.1,
                            f"Unexpected convergence order: {name}, n={n}, {field}")
            grids.append(row)
            previous = row
        records.append({"name": name, "formula": formula,
                        "left": left, "right": right, "grids": grids})

    require(boundary_pass, "Boundary values were not enforced exactly")
    x, u = solve(37, lambda x: 2.5, lambda x: 0.0, -2.0, 3.0)
    affine_error = max(abs(ui - (-2.0 + 5.0 * xi)) for xi, ui in zip(x, u))
    affine_tolerance = 1e-12
    require(affine_error < affine_tolerance, "Nonzero-boundary affine check failed")

    one = lambda x: 1.0
    zero = lambda x: 0.0
    invalid = [("bool n", (True, one, zero)),
               ("small n", (1, one, zero)),
               ("float n", (4.0, one, zero)),
               ("noncallable k", (4, 1.0, zero)),
               ("noncallable f", (4, one, 0.0))]
    bad_real = (True, float("nan"), float("inf"), -float("inf"),
                1j, "1", None)
    for index, value in enumerate(bad_real):
        invalid.extend([
            (f"left invalid scalar {index}", (4, one, zero, value, 0.0)),
            (f"right invalid scalar {index}", (4, one, zero, 0.0, value)),
            (f"k invalid scalar {index}", (4, lambda x, v=value: v, zero)),
            (f"f invalid scalar {index}", (4, one, lambda x, v=value: v)),
        ])
    for value in (0.0, -1.0):
        invalid.append((f"nonpositive k {value}",
                        (4, lambda x, v=value: v, zero)))
    passed = []
    for name, arguments in invalid:
        try:
            solve(*arguments)
        except ValueError:
            passed.append(name)
        else:
            raise AssertionError(f"Invalid input accepted: {name}")

    return {
        "provenance": "Analytical manufactured solutions; errors measured by running solver.py. No experimental data or physical validation.",
        "error_definitions": {
            "max_abs_nodal_error": "max over all nodes of abs(u_numerical-u_exact)",
            "discrete_l2_error": "sqrt(h * sum of squared interior nodal errors)",
            "observed_order": "log2(previous grid error / current grid error)",
            "max_abs_pde_residual": "max interior abs((k_left*(u_i-u_previous)-k_right*(u_next-u_i))/h^2-f_i); algebraic residual, not solution error",
        },
        "cases": records,
        "checks": {
            "exact_boundary_enforcement": {"passed": boundary_pass},
            "nonzero_boundary_affine": {"passed": True, "n": 37,
                "formula": "k=2.5; f=0; u=-2+5*x", "max_abs_error": affine_error,
                "absolute_tolerance": affine_tolerance},
            "invalid_input": {"passed": True, "count": len(passed), "cases": passed},
            "second_order": {"passed": True, "order_interval": [1.9, 2.1]},
            "pde_residual": {"passed": True, "absolute_tolerance": residual_tolerance},
        },
        "interpretation": "Both smooth cases should converge at second order. Small deviations from order 2 reflect higher-order truncation terms and floating-point effects. Small algebraic residuals establish that the discrete equations were solved, not physical accuracy.",
    }


def main():
    result = run_study()
    destination = Path(__file__).resolve().with_name("verification.json")
    destination.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                           encoding="utf-8")
    print(f"Wrote {destination}")
    print("Passed: two four-grid convergence studies, boundaries, affine solution, "
          f"and {result['checks']['invalid_input']['count']} invalid-input cases.")


if __name__ == "__main__":
    main()
