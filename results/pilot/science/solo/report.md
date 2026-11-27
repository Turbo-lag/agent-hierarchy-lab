# Conservative elliptic solver verification

The implementation passes the supplied smoke test and 15 additional tests.
Both required analytical manufactured solutions exhibit second-order nodal
convergence. These are computed numerical errors against analytical solutions,
not experimental measurements or physical validation. Full-precision results
and checks are in [verification.json](verification.json).

## Discretization and boundary treatment

Let `h=1/n`, `x_i=i/n`, and `a_j=k((j+1/2)/n)` for `j=0,...,n-1`.
Approximate the derivative at each face by `(u_(i+1)-u_i)/h`. The conservative
negative flux divergence gives

```text
-a_(i-1) u_(i-1) + (a_(i-1)+a_i) u_i - a_i u_(i+1) = h^2 f(x_i).
```

Only `i=1,...,n-1` are unknown. Add `a_0*left` to the first right-hand-side
entry and `a_(n-1)*right` to the last. For `n=2`, both contributions enter the
same equation. Return the prescribed endpoints directly. This also explains why
the source is never sampled at a boundary and the coefficient is sampled only
at face midpoints; positivity at other locations is irrelevant to this contract.

For a vector extended by zero at both endpoints, the scaled matrix satisfies
`v^T A v = sum_j a_j (v_(j+1)-v_j)^2 > 0` for nonzero `v`. It is symmetric
positive definite when the sampled coefficients are positive. Its tridiagonal
Thomas elimination therefore has positive pivots without pivoting. The solver
stores the faces, diagonal, right-hand side, nodes, and output as linear-length
lists and uses one forward elimination and one backward substitution. There
are exactly `n` coefficient calls and `n-1` source calls. Work and storage are
O(n), assuming constant-cost user callbacks. No dense matrix or external
package is used.

For sufficiently smooth `k` and `u`, the face derivative is
`u'(x_(i+1/2)) + h^2*u'''(x_(i+1/2))/24 + O(h^4)`.
Taking the centered divergence of the smoothly varying face flux errors leaves
an O(h^2) truncation error. Stability of the positive Dirichlet operator then
gives the expected second-order solution error for these smooth cases.

## Reproduction

All commands below are local, from
`.`:

```sh
./verify.py
python3.14 -m unittest discover -s tests -v
python3.14 -m unittest -v test_solution
```

The observed runtime is Python 3.14.8 on Darwin. The default `/usr/bin/python3`
launcher fails because Apple developer tools are unavailable. Therefore the
commands use the existing `python3.14` runtime. `verify.py` is executable and
its shebang selects that runtime. The source uses Python 3.11+ standard-library
features; on another host with Python 3.11 or newer, it can also be invoked as
`python3 verify.py`. Other Python versions were not executed here. The script
writes `verification.json` beside itself, rejects nonfinite JSON numbers, and
exits unsuccessfully if a verification check fails.

## Manufactured solutions and measured results

Case 1 uses `k=1`, `u=sin(pi*x)`, and `f=pi^2*sin(pi*x)`, with both boundaries
zero. Case 2 uses `k=1+x`, `u=sin(pi*x)+x`, and boundaries zero and one.
Differentiating `k*u'=(1+x)*(pi*cos(pi*x)+1)` gives
`f=(1+x)*pi^2*sin(pi*x)-pi*cos(pi*x)-1`.

The maximum error includes all nodes. The discrete L2 error is
`sqrt(h*sum_(i=1)^(n-1) (u_i-u_exact(x_i))^2)`. Each order is
`log2(E_previous/E_current)` for that norm; no order exists for the first grid.
The residual is `max_i |A_h u_h-f(x_i)|` in the original equations with the
`1/h^2` factor, evaluated independently from the elimination arrays.

| Case | n | Maximum error | Max order | Discrete L2 error | L2 order | Max algebraic residual |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 16 | 3.218964440e-3 | — | 2.276151584e-3 | — | 3.4639e-14 |
| 1 | 32 | 8.035776794e-4 | 2.002087 | 5.682152263e-4 | 2.002087 | 2.0250e-13 |
| 1 | 64 | 2.008218097e-4 | 2.000522 | 1.420024634e-4 | 2.000522 | 1.0161e-12 |
| 1 | 128 | 5.020091591e-5 | 2.000130 | 3.549740806e-5 | 2.000130 | 7.2280e-12 |
| 2 | 16 | 3.186645785e-3 | — | 2.245501870e-3 | — | 1.4033e-13 |
| 2 | 32 | 7.977286520e-4 | 1.998069 | 5.605023073e-4 | 2.002246 | 7.5140e-13 |
| 2 | 64 | 1.993543433e-4 | 2.000563 | 1.400711046e-4 | 2.000561 | 3.5776e-12 |
| 2 | 128 | 4.984430214e-5 | 1.999835 | 3.501437322e-5 | 2.000140 | 1.1447e-11 |

Errors decrease by approximately four when the grid spacing halves. The small
departures from order two are consistent with higher-order truncation terms
and, for the variable-coefficient maximum norm, changes in which sampled node
attains the maximum error. There is no observed loss of the expected order.
Residuals grow slightly with refinement because floating-point cancellation
is amplified by `1/h^2`; they remain many orders below the solution errors.
A small algebraic residual shows that the discrete equations were solved
accurately, but does not by itself establish accuracy relative to the
continuous differential equation. The solution-error study supplies that
separate evidence. Floating-point evaluation of `sin(pi)` need not be exactly
zero; boundary enforcement is checked against the supplied boundary values.

## Additional checks and limits

All eight study solves enforce the supplied endpoints exactly. For `k=1+x`,
`u=2+3*x`, and `f=-3`, with boundaries 2 and 5, the maximum affine-solution
errors at `n=2,16,128` are respectively `0`, `1.776356839e-15`, and
`2.087219286e-14`, with exact boundary enforcement. The midpoint scheme is
exact for this solution up to floating-point arithmetic.

The JSON includes 35 passing invalid-input checks. The test suite additionally
checks every face and interior node for invalid samples, callback exception
propagation, exact sampling locations and counts, fractional real inputs,
single- and two-unknown systems with independently computed answers, a quadratic
solution with a linear coefficient spanning the supported coefficient range,
and second-order convergence for `k=exp(x), u=exp(x), f=-2*exp(2*x)`.
It also checks constant-flux conservation with a discontinuous positive
coefficient, and affine solutions at `n=4096` with coefficients 0.1 and 10 and
boundary values -100 and 100. The discontinuous case is a discrete conservation
check; no smooth second-order claim is made for discontinuous coefficients.

Input real scalars are Python `numbers.Real` instances, excluding bool; they
are converted to finite floats. Strings, complex values (including zero
imaginary part), non-real objects, and nonfinite values are rejected with
`ValueError`. Positive coefficients are required at all sampled faces.
Source values may have either sign. Callback exceptions propagate unchanged.
The solver does not impose the scoring-range bounds as extra input restrictions.
Accuracy is assessed within the stated range: `n<=4096`, sampled coefficients
in `[0.1,10]`, and source/boundary magnitudes at most 100. Extreme values outside
that range may overflow or cause poor conditioning even if initially finite.
Convergence claims depend on smoothness, and roundoff can dominate on much
finer grids. No performance timing study or physical validation is claimed;
linear complexity follows from the implementation's arrays and loop bounds.
