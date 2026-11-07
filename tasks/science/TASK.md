# Scientific task: verify a variable-coefficient elliptic solver

Implement `solve(n, k, f, left=0.0, right=0.0)` in `solver.py` for

    -(k(x) u'(x))' = f(x),  0 < x < 1,
    u(0) = left, u(1) = right.

`n` is the number of equal intervals, an int >= 2 excluding bool. Return two
plain lists `(x, u)`, each length n+1, including both boundary nodes. `k` and `f`
are callable real scalar functions. Use the conservative centered discretization

    [k_(i-1/2)(u_i-u_(i-1)) - k_(i+1/2)(u_(i+1)-u_i)] / h^2 = f(x_i).

Sample k at face midpoints and f at interior nodes. Validate finite strictly
positive k at those faces, finite f at interior nodes, and finite real boundary
values, excluding bool. Invalid n/values/noncallable k or f raise ValueError.
Exceptions raised inside otherwise callable user functions may propagate.
Do not require k to be positive at locations you never sample. Supported range
for valid evaluated coefficients is [0.1, 10], source/boundary magnitude <= 100,
and n <= 4096; behavior outside these finite ranges is not scored, except that
nonfinite/invalid inputs above must still be rejected. Use O(n) storage and O(n)
work; Python standard library only. Do not hard-code particular exact solutions.

## Verification study

Provide `verify.py` that writes `verification.json`. Compute actual errors for
n = 16, 32, 64, 128 for BOTH manufactured cases below:

1. k(x)=1; u(x)=sin(pi*x); f(x)=pi^2 sin(pi*x); zero boundaries.
2. k(x)=1+x; u(x)=sin(pi*x)+x; f(x)=(1+x)pi^2 sin(pi*x)-pi cos(pi*x)-1;
   left=0 and right=1.

For each case/grid report max absolute nodal error and discrete L2 error
sqrt(h * sum(interior_error^2)); compute observed refinement orders with log2 of
successive error ratios. Distinguish algebraic residual from solution error.
Check boundary enforcement, a nonzero-boundary affine solution, and invalid input.
Explain the expected second-order trend and any departure; do not claim physical
validation. These are analytical manufactured solutions, not experimental data.

## Deliverables

- `solver.py`, executable `verify.py`, generated `verification.json`.
- `test_solution.py` and `report.md` describing derivation, boundary treatment,
  O(n) implementation, commands, measured errors/orders, and limits.
- `execution.md` per experiment instructions.

Supplied smoke test: `python3 -m unittest discover -s tests -v`.
Scoring: numerical and contract checks 80 points; verification evidence 20.
Evaluators also use other smooth manufactured functions and coefficient values.
