# Conservative elliptic solver verification

The implementation solves the specified conservative tridiagonal system in linear work and storage. Both required analytical manufactured cases exhibit second-order solution convergence on n=16,32,64,128. The values below are measured numerical errors against analytical solutions, not experimental data or physical validation. Full-precision results are in `verification.json`.

## Discretization and boundary treatment

Let h=1/n, x_i=i/n, and a_j=k((j+1/2)/n) for j=0,...,n-1. The centered approximation to the face flux is q_(i+1/2)=a_i*(u_(i+1)-u_i)/h. Applying the conservative negative flux difference gives

    [a_(i-1)*(u_i-u_(i-1)) - a_i*(u_(i+1)-u_i)]/h² = f(x_i).

Multiplication by h² produces diagonal a_(i-1)+a_i and off-diagonals -a_(i-1), -a_i. Move known boundary terms to the right-hand side: add a_0*left to its first entry and a_(n-1)*right to its last. When n=2, both additions go into the same entry. Boundary entries are inserted directly into the returned solution list.

Strictly positive face coefficients make the Dirichlet tridiagonal matrix symmetric positive definite: its quadratic form is a sum of positive weighted squared differences with homogeneous boundary variations. Thomas elimination therefore has positive pivots in exact arithmetic and needs no pivot search in the supported range. Forward elimination and back substitution each use a single loop; coefficients, diagonal, right-hand side, grid, and solution each occupy O(n) storage. No dense matrices or external numerical packages are used.

The solver evaluates k exactly once at each face midpoint and f exactly once at each interior node. It does not inspect endpoints or other locations of either callable. Input validation accepts finite `numbers.Real` scalars and `decimal.Decimal`, converts them to Python floats, and rejects bool, strings, complex values, containers, and values not representable as finite floats. Every sampled coefficient must additionally be strictly positive. n must be an int >=2 excluding bool; k and f must be callable. Invalid values raise ValueError; exceptions originating in user callables propagate unchanged.

## Verification definitions and cases

1. k=1, u=sin(pi*x), f=pi²*sin(pi*x), with boundaries 0 and 0.
2. k=1+x, u=sin(pi*x)+x, f=(1+x)*pi²*sin(pi*x)-pi*cos(pi*x)-1, with boundaries 0 and 1.

Max error includes all nodes. Discrete L2 is sqrt(h*sum(e_i²)) over interior nodes only. Successive orders are log2(E_n/E_(2n)); the first grid has no order. The PDE residual is the maximum absolute interior value of the original stencil divided by h² minus f_i. It measures the accuracy of solving the discrete algebraic equations and is distinct from the solution error against u_exact.

### constant_coefficient_sine

| n | max nodal error | order | discrete L2 error | order | max PDE residual |
|---:|---:|---:|---:|---:|---:|
| 16 | 3.2189644401e-03 | — | 2.2761515840e-03 | — | 3.463896e-14 |
| 32 | 8.0357767937e-04 | 2.002087 | 5.6821522629e-04 | 2.002087 | 2.025047e-13 |
| 64 | 2.0082180970e-04 | 2.000522 | 1.4200246345e-04 | 2.000522 | 1.016076e-12 |
| 128 | 5.0200915913e-05 | 2.000130 | 3.5497408062e-05 | 2.000130 | 7.227996e-12 |

### variable_coefficient_sine_plus_x

| n | max nodal error | order | discrete L2 error | order | max PDE residual |
|---:|---:|---:|---:|---:|---:|
| 16 | 3.1866457846e-03 | — | 2.2455018697e-03 | — | 1.403322e-13 |
| 32 | 7.9772865199e-04 | 1.998069 | 5.6050230731e-04 | 2.002246 | 7.513989e-13 |
| 64 | 1.9935434334e-04 | 2.000563 | 1.4007110464e-04 | 2.000561 | 3.577583e-12 |
| 128 | 4.9844302136e-05 | 1.999835 | 3.5014373215e-05 | 2.000140 | 1.144684e-11 |

All returned boundaries equal their specified values exactly. The study also solves k=2.5, f=0, u=-2+5*x on n=37 with boundaries -2 and 3. Its measured maximum error is 2.8865798640e-15, below the checked absolute tolerance 1e-12. All 35 invalid-input study cases raise ValueError. The executable study requires every measured refinement order to lie in [1.9,2.1] and every PDE residual to be below 1e-8; all checks pass, and failures stop the workflow before writing new results.

For smooth coefficients and solutions, symmetric face interpolation and the conservative centered flux difference have second-order truncation error; stability of this positive-coefficient Dirichlet problem gives second-order solution convergence. Higher-order truncation terms explain the small departures from exactly 2. The variable-coefficient maximum norm also depends on where the largest error falls on each nodal grid. Residuals grow somewhat as h decreases because the PDE normalization amplifies floating-point cancellation by h^-2, but remain much smaller than the solution errors on these grids. Very fine grids can ultimately become limited by floating-point roundoff. No unexpected loss of convergence occurs in this study.

## Running and checks

From the integrated workspace root, local commands are:

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest -v test_solution
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 verify.py
```

The explicit interpreter is the available local Python 3.14.8; any working Python 3.11+ standard-library installation can be used instead. `verify.py` has an executable shebang and writes `verification.json` alongside itself. Re-running it regenerates the measured numbers. No packages, network, or services are needed.

Author-stage execution from `scratch/author/` passed all 16 methods in `test_solution.py` and the supplied one-test smoke suite, loaded via `runpy.run_path("../../tests/test_smoke.py", run_name="__main__")` so its solver import used the isolated candidate. The verification program ran successfully and its JSON parsed successfully. Root integration and final root checks are recorded separately in `execution.md`.

Additional tests cover a constant-coefficient quadratic with nonzero boundaries, an exact affine solution for variable k, an independent discrete resistance solution with a discontinuous coefficient, and u=exp(x) with k=2+x and f=-(3+x)*exp(x). They also check independently recomputed residuals, exact sampling locations, late invalid samples, callable exception propagation, Decimal/Fraction inputs, and n=4096 with coefficients 0.1 and 10. Tests of n=2 explicitly check that both boundary contributions survive. The maximum-grid tests use an absolute affine-error tolerance of 2e-8; no timing-based performance claim is made. Linear complexity follows from the implementation's fixed number of linear passes.

## Scope and limits

The supported numerical envelope specified by the task is n<=4096, evaluated k in [0.1,10], and source/boundary magnitude <=100. The code does not impose these as additional rejection thresholds, but accuracy or stability outside this envelope is not established. Nonfinite and other invalid values are rejected regardless. Smoothness is needed for the reported second-order convergence, not for accepting valid face samples or solving the algebraic system. This is numerical verification for the specified one-dimensional equation and Dirichlet boundary conditions; it establishes no experimental or physical validation. External personal skill files were disabled by the measured-run boundary and were not accessed or claimed as satisfied.
