# Variable-coefficient elliptic solver verification

Implemented the conservative centered discretization and an O(n) tridiagonal
solve. This study compares computed values with **analytical manufactured
solutions**; it provides numerical verification, not physical validation or
experimental data.

## Discretization and boundary treatment

Let h=1/n, x_i=i h and K_j=k((j+1/2)h). Multiplying the prescribed interior
equation by h² gives

    -K_(i-1) u_(i-1) + (K_(i-1)+K_i) u_i - K_i u_(i+1) = h² f(x_i).

The unknowns are u_1,...,u_(n-1). The first right-hand-side entry receives
K_0*left and the last receives K_(n-1)*right. Both contributions are added when
n=2. Boundary entries in the returned list are assigned directly. For positive
face coefficients the Dirichlet matrix is symmetric positive definite: its
quadratic form is the sum of K_j times squared adjacent differences, with
homogeneous endpoints. Thomas elimination and back substitution therefore
require no pivoting. Each loop takes O(n) work, and the node, face, diagonal,
right-hand-side and solution lists use O(n) memory; no dense matrix is formed.

All n face samples and n-1 interior source samples are validated. n must be an
int >=2 excluding bool; k and f must be callable. Evaluated coefficients must be
finite, real and strictly positive. Source and boundary values must be finite
real numbers excluding bool. Real numerical scalars (including Fraction and
Decimal) are converted to float; strings and complex values are rejected.
Callback exceptions propagate. k is never sampled at endpoints or interior nodes,
and f is never sampled at endpoints. No upper supported-range limit is imposed.

For smooth k and u, centered face gradients approximate face derivatives with
O(h²) error. The conservative divergence gives a consistent second-order
operator, and the stable elliptic solve gives O(h²) solution errors. Halving h
should reduce the error by roughly four, corresponding to refinement order two.

## Measured verification

Case 1 uses k=1, u=sin(pi*x), f=pi² sin(pi*x), with zero boundaries.
Case 2 uses k=1+x, u=sin(pi*x)+x,
f=(1+x)pi² sin(pi*x)-pi cos(pi*x)-1, with boundaries 0 and 1.
For both cases, the L2 column is sqrt(h*sum(interior nodal error²)). Max error
includes all nodes. Orders are log2(previous-grid error/current-grid error).
The residual is the maximum absolute interior residual of the original equation,
including division of flux differences by h². It measures algebraic solution
accuracy, whereas the two error norms compare with the analytical solution.

### constant_k_sine

| n | Max error | L2 error | Max order | L2 order | Max residual |
|---:|---:|---:|---:|---:|---:|
| 16 | 3.218964440e-03 | 2.276151584e-03 | — | — | 3.464e-14 |
| 32 | 8.035776794e-04 | 5.682152263e-04 | 2.002087 | 2.002087 | 2.025e-13 |
| 64 | 2.008218097e-04 | 1.420024634e-04 | 2.000522 | 2.000522 | 1.016e-12 |
| 128 | 5.020091591e-05 | 3.549740806e-05 | 2.000130 | 2.000130 | 7.228e-12 |

### linear_k_sine_plus_x

| n | Max error | L2 error | Max order | L2 order | Max residual |
|---:|---:|---:|---:|---:|---:|
| 16 | 3.186645785e-03 | 2.245501870e-03 | — | — | 1.403e-13 |
| 32 | 7.977286520e-04 | 5.605023073e-04 | 1.998069 | 2.002246 | 7.532e-13 |
| 64 | 1.993543433e-04 | 1.400711046e-04 | 2.000563 | 2.000561 | 3.578e-12 |
| 128 | 4.984430214e-05 | 3.501437322e-05 | 1.999835 | 2.000140 | 1.145e-11 |

Both cases show second-order convergence. Small departures from exactly two
come from higher-order truncation terms and, for the variable-coefficient max
norm, the changing location of the maximum on successive grids. They do not
indicate a loss of convergence. Residuals are approximately 1e-14 to 1e-11,
far below the solution errors. Residual growth on finer grids is consistent
with cancellation and roundoff amplified by h^-2. Finer meshes would eventually
reach a roundoff-dominated regime; this study does not quantify that threshold.

All eight solves enforce their assigned boundaries exactly. The nonzero-boundary
affine check u=-2+5x at n=73 and k=2.5 has maximum error
3.552713679e-15 (tolerance 1e-11). All 13 invalid-input examples in the JSON are
rejected. `test_solution.py` adds 14 tests covering all invalid-value positions,
callback propagation, exact sampling locations/counts, n=2, n=4096, quadratic
and other smooth manufactured solutions, and heterogeneous face coefficients
checked against an independent constant-flux resistance formula.

## Reproduction and limits

From the final workspace root, run:

```sh
PYTHONDONTWRITEBYTECODE=1 PATH=/opt/homebrew/bin:$PATH ./verify.py
/opt/homebrew/bin/python3.14 -B -m unittest -v test_solution
/opt/homebrew/bin/python3.14 -B -m unittest discover -s tests -v
```

On a host with working Python 3.11+, `python3` can replace the explicit
interpreter path. In this execution host, `/usr/bin/python3` fails because Xcode
developer tools are unavailable; the installed Homebrew Python 3.14.8 works.
The script writes `verification.json` beside itself and exits unsuccessfully
if its boundary, affine, invalid-input or convergence checks fail.

Candidate self-checks were run from `scratch/candidate3/`: all 14 numerical and
contract tests and the supplied smoke test passed. The smoke invocation used
an absolute path to the supplied workspace tests and disabled bytecode writes,
so only candidate files were written. Root selected this candidate after independent numerical and evidence checks;
final root verification results and selection details are recorded in `execution.md`. Only the standard library is used. Tests cover the
supported 2<=n<=4096, coefficients in [0.1,10], and source/boundary
magnitudes <=100, but do not establish accuracy
for arbitrary nonsmooth data or numerical behavior beyond the stated ranges.
No empirical timing benchmark is claimed; O(n) follows directly from the fixed
number of linear passes and linear-size lists. External personal skills were
disabled by the measured-run protocol and were not read.
