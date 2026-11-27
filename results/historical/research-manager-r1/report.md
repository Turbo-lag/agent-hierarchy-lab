# Conditional recommendations for the three scenarios

Choose CG first for A, compare restarted GMRES and BiCGStab in B, and choose flexible GMRES first for C. These are conditional recommendations, not measured performance rankings. The claim that BiCGStab is always best because of memory use is unsupported: admissibility, convergence, operation costs, and complete memory consumption all matter. The supplied sources support selection principles but contain no timings for these scenarios. [S1][S2][S3][S4][S5][S6]

**Evidence boundary.** “Direct support” below means the supplied author paraphrase explicitly states the property; it does not mean a quotation or independent inspection of the underlying reference. “Inference” identifies our recommendation or proposed methodology. “Assumptions” identify the synthetic scenario inputs. No experiment has been run, and no synthetic assumption is an observed dataset.

## A: SPD diffusion with a fixed SPD preconditioner

**Assumptions:** The matrix is real symmetric positive definite (SPD), the available preconditioner is fixed and SPD, and applying the matrix or its transpose is not expensive. There are no timings.

**Direct support:** This is the standard admissible CG setting in the digest: symmetry and definiteness conditions apply to both matrix and preconditioner. PETSc's documented CG implementation uses left preconditioning. Mathematical appropriateness does not imply a measured runtime advantage. [S1]

**Inference:** Use CG as the initial choice because the supplied structural assumptions meet its requirements. Verify those assumptions in the eventual implementation, particularly that the applied preconditioner preserves the stated properties. Do not extend the recommendation to a changed, nonsymmetric, or variable preconditioner merely because the original diffusion matrix was SPD. [S1]

Restarted GMRES and BiCGStab remain comparison candidates; the supplied evidence does not demonstrate that they beat CG here. BiCGStab's lack of a transpose requirement is no special deciding benefit under A's assumptions. Flexible GMRES can be considered if the preconditioner later becomes nonlinear or changes between iterations, but that capability is not needed by the stated fixed SPD setup. These are selection inferences from matrix requirements and available capabilities, not exclusions based on timing. [S3][S4][S6]

## B: nonsymmetric system with a 20-direction budget

**Assumptions:** The real matrix is nonsymmetric, the preconditioner is fixed and linear, matrix-vector multiplication is available, and transpose multiplication is unavailable. At most 20 basis vectors can be retained for GMRES orthogonalization; convergence is unknown. This restriction is expressly a basis budget, not a total-memory ceiling.

**Direct support:** Restarted GMRES exposes a restart parameter controlling the participating Krylov directions; those directions are only part of solver storage. Restarting limits storage but can impair convergence. BiCGStab uses short recurrences, handles nonsymmetric systems without a transpose product, and can suffer breakdown or poor convergence. PETSc presents it as an alternative when GMRES restart choices do not balance iteration expense and convergence satisfactorily. [S2][S3][S6]

**Inference:** Start a controlled comparison with restarted GMRES, using a restart parameter m <= 20 that respects the actual 20-vector orthogonalization budget, and BiCGStab. Nominal restart lengths such as 5, 10, and 20 are proposed test settings, not evidence-backed optimal choices. Check the selected implementation's allocation convention before accepting the 20 setting; do not confuse a parameter label with a verified count of live basis vectors. Measure auxiliary work vectors, preconditioner storage, and other allocations separately. [S2][S6]

Ordinary restarted GMRES is a candidate under the fixed linear preconditioner; confirming its use of the supplied matrix-product interface belongs in implementation verification. This is an admissibility inference from the described Krylov formulation; the digest explicitly confirms transpose-free operation for BiCGStab. CG's stated SPD admissibility conditions are not supplied for this nonsymmetric matrix, so it is not an admissible default. Flexible GMRES offers no necessary variable-preconditioning capability in B, though it can be retained as an optional comparator if resources permit. [S1][S2][S4][S6]

Choose between the two primary candidates only after observing their success and cost. A short GMRES cycle may lose useful accumulated information at restart; BiCGStab avoids the retained growing basis but can converge poorly or break down. Neither the basis restriction nor missing transpose establishes a universal winner. [S3][S6]

## C: a tolerance-stopped inner solve

**Assumptions:** The real matrix is nonsymmetric; an inner iterative solve supplies the preconditioner and stops at a tolerance. Its effective action can change between outer iterations. Memory supports a modest basis, but no timings exist.

**Direct support:** Ordinary GMRES requires a linear preconditioning operator. Flexible GMRES permits nonlinear preconditioning and changing preconditioners; an inner Krylov solve is generally nonlinear as a preconditioner. PETSc's flexible GMRES uses right preconditioning and provides a restart parameter. The digest establishes neither universal speed superiority nor storage equality with ordinary GMRES. [S4]

**Inference:** Use right-preconditioned flexible GMRES with a modest, measured restart choice. The changing action is the decisive reason; it directly matches the flexibility documented by S4. Do not assume that the inner solve defines a fixed linear operator merely because the outer matrix is fixed. Ordinary GMRES becomes a defensible alternative if the team changes and verifies the preconditioning procedure to provide a fixed linear action. [S4]

CG lacks the required SPD setting here. Standard BiCGStab is not justified for this variable-action setup by the digest; flexible variants are separate implementations and should not be silently substituted for the named ordinary algorithm. This is a limitation of the supported recommendation, not a claim that every variable-preconditioned BiCGStab execution must fail. [S1][S3][S4]

## Why the universal memory claim fails

**Direct support:** BiCGStab avoids explicitly retaining GMRES's growing basis, but restarted GMRES limits basis storage. Total storage includes more than those directions. Method choice also depends on matrix properties and the relative costs of products, preconditioner applications, vector work, and inner products. [S2][S3][S6]

**Inference:** Lower basis storage is a conditional advantage, not proof of lower total memory in every configuration or better time to solution. A method that fails to reach the required residual cannot win solely by allocating fewer basis vectors. A's CG admissibility and C's variable preconditioning already require considerations absent from the universal claim. No supplied source establishes any universal winner. [S1][S3][S4][S6]

## Concrete validation experiment

**Proposed methodology, not executed results:** For each scenario, fix the actual matrix, right-hand side, initial guess, arithmetic precision, hardware, solver version, and preconditioner configuration and side. Hold the side common where compatible, and label any changes. Compare A's CG with optional GMRES/BiCGStab alternatives, B's budget-compliant GMRES settings with BiCGStab, and C's flexible GMRES restart settings. Any fixed-linear C alternative is a separate preconditioner configuration whose changed setup and solve costs must be reported. [S1][S2][S4][S6]

Predeclare a common target, for example
`||b-Ax||_2 <= max(1e-8 ||b||_2, 1e-12)`.
These tolerances are explicit experimental assumptions, not supplied measurements. Recompute the true residual for the original, consistently scaled system at consistent checkpoints and before declaring success. Record solver-reported norms separately, since they can be preconditioned or approximate; S5 motivates this protocol rather than supplying a benchmark result. The absolute tolerance also covers a zero right-hand side. Use the same monitoring schedule and report validation overhead separately from the solve cost. [S5]

Measure setup and solve time separately, including inner-solve work in C. Use five timed repetitions per configuration after a declared warm-up, reporting median and range. Report matrix and preconditioner applications, inner iterations, orthogonalization work, peak total memory and its measurement method, basis counts, restarts, residual histories, final true residuals, and termination reasons. Predeclare time/work limits and record stagnation, breakdown, nonconvergence, and budget violations as outcomes rather than discarding them. [S2][S3][S6]

Rank successful configurations by comparable total cost for the team's intended setup-reuse pattern and memory constraints. Include variability across repeats. Do not select from unmatched outer iteration counts: operation costs and preconditioning expense differ, and C nests additional work inside an outer iteration. The evidence supports performing this experiment, not predicting its winner. [S5][S6]
