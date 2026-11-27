# Conservative elliptic solver verification

The two analytical manufactured solutions converge at approximately second order
in maximum nodal error and discrete L2 error. These are computed numerical errors
against analytical functions, not experimental observations or physical validation.
Full precision measurements and check outcomes are in `verification.json`.

## Discretization and boundaries

For `h=1/n` and `x_i=i*h`, evaluate `k` only at the `n` face midpoints
`(j+1/2)/n`, and `f` only at the `n-1` interior nodes. Approximate the flux
at a face by `k_(i+1/2)*(u_(i+1)-u_i)/h`. Subtract the right flux from the
left flux and divide by `h`. Multiplying the requested equation by `h^2`
gives the tridiagonal row

```
-k_(i-1/2)*u_(i-1) + (k_(i-1/2)+k_(i+1/2))*u_i
    - k_(i+1/2)*u_(i+1) = h^2*f(x_i).
```

Move the known left endpoint term into the first right-hand-side entry as
`+k_(1/2)*left`, and the known right endpoint term into the last entry as
`+k_(n-1/2)*right`. For `n=2`, both contributions enter the same entry.
Endpoint values are then inserted directly in the returned solution list.

The interior matrix is symmetric positive definite: its quadratic form is the
sum of positive face weights times squared neighboring differences, with zero
endpoint perturbations. Thomas elimination therefore needs no pivoting for these
positive coefficients. It stores the faces, transformed diagonal and right-hand
side, then back-substitutes. Assembly, elimination and back-substitution each
perform O(n) work and use O(n) storage. Both returned objects are plain lists
of length `n+1`.

Input validation requires integer `n>=2`, excluding bool; callable `k` and `f`;
and finite real, non-bool boundary and sampled values. Sampled `k` must be
strictly positive. Real scalars use the standard-library `numbers.Real`
interface and are converted to floating point; strings and complex values are
rejected. Invalid inputs raise `ValueError`. Exceptions raised by a callback
itself propagate. No coefficient samples outside the faces are required.

## Actual refinement measurements

The maximum norm includes all nodes. The discrete L2 norm is
`sqrt(h*sum(interior_error**2))`. Each reported order is
`log2(previous_error/current_error)`; the first grid has no order.

Case 1: `k=1`, `u=sin(pi*x)`, `f=pi^2*sin(pi*x)`, endpoint values `(0,0)`.

| n | Maximum error | L2 error | Max order | L2 order | Maximum algebraic residual |
|---:|---:|---:|---:|---:|---:|
| 16 | 3.218964440e-3 | 2.276151584e-3 | — | — | 3.463895837e-14 |
| 32 | 8.035776794e-4 | 5.682152263e-4 | 2.002087243 | 2.002087243 | 2.025046797e-13 |
| 64 | 2.008218097e-4 | 1.420024634e-4 | 2.000521534 | 2.000521534 | 1.016076112e-12 |
| 128 | 5.020091591e-5 | 3.549740806e-5 | 2.000130366 | 2.000130366 | 7.227995980e-12 |

Case 2: `k=1+x`, `u=sin(pi*x)+x`,
`f=(1+x)*pi^2*sin(pi*x)-pi*cos(pi*x)-1`, endpoint values `(0,1)`.
This source follows from `f=-k*u''-k'*u'`.

| n | Maximum error | L2 error | Max order | L2 order | Maximum algebraic residual |
|---:|---:|---:|---:|---:|---:|
| 16 | 3.186645785e-3 | 2.245501870e-3 | — | — | 1.403321903e-13 |
| 32 | 7.977286520e-4 | 5.605023073e-4 | 1.998068662 | 2.002245706 | 7.513989431e-13 |
| 64 | 1.993543433e-4 | 1.400711046e-4 | 2.000563058 | 2.000560940 | 3.577582675e-12 |
| 128 | 4.984430214e-5 | 3.501437322e-5 | 1.999834538 | 2.000140205 | 1.144684347e-11 |

For smooth coefficients and solutions, the centered face differences and flux
divergence have second-order truncation error; stability of this positive
elliptic system gives the expected second-order solution trend. Small deviations
from exactly two reflect higher-order discretization terms and, in the variable
case's maximum norm, sampling the continuous error peak on successive nodal
grids. No material departure from the expected trend is observed here.

The algebraic residual is the maximum interior absolute value of the original,
unscaled discrete left-hand side minus `f(x_i)`, evaluated on the computed
solution. It measures how well the finite-dimensional equations were solved.
Solution error instead compares that solution to the analytical continuum
solution; it remains around `5e-5` at `n=128` even when residuals are around
`1e-11`. Division by `h^2` amplifies cancellation and roundoff in residual
evaluation as the grid refines. A small algebraic residual does not establish
small discretization error.

## Reproduction and checks

From the deliverable directory, using Python 3.11 or newer:

```
python3 verify.py
python3 -m unittest discover -s tests -v
python3 -m unittest test_solution -v
```

`verify.py` has an executable shebang and accepts `--output PATH`, defaulting to
`verification.json` in the current directory. In this environment the actual
working interpreter was `/opt/homebrew/bin/python3`; the system `python3`
launcher was unavailable because its developer-tools setup was missing.
The executable entrypoint was also run successfully as
`PATH=/opt/homebrew/bin:$PATH ./verify.py`.

The study script checks exact endpoint enforcement for every reported solve;
27 invalid-input cases including nonfinite, bool, complex, noncallable and
invalid-grid inputs; exception propagation from each callback; and exact face
and interior-node sampling locations. It also checks the nonzero-boundary affine
solution `u=-2+5x`, `k=1+x`, `f=-5`, with endpoints `(-2,3)` for `n=2,16,128`.
Its largest measured affine error was `1.532107773982716e-14`. The executable
study passed all these checks. The accompanying independent `test_solution.py`
and the supplied smoke test are additional checks; final integration records
their results in `execution.md`.

## Limits

The stated supported operating range is `n<=4096`, face coefficients in
`[0.1,10]`, and source/boundary magnitudes at most 100. The solver validates
finiteness, realness and coefficient positivity but does not impose these
upper/lower supported-range bounds as extra input restrictions. No accuracy or
overflow guarantee is made outside that range. Error orders assume sufficient
smoothness; discontinuous coefficients or nonsmooth solutions need separate
analysis. Ordinary floating-point roundoff ultimately limits refinement.
The study covers the required grids and two manufactured cases, not every
possible valid coefficient function, and does not constitute physical validation.
