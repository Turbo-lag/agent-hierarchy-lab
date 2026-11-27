# Solver recommendation from the frozen evidence digest

Recommend preconditioned CG for A, restarted GMRES with a bounded basis as the initial candidate for B, and flexible GMRES for C. These are conditional engineering choices, not measured winners. Reject “BiCGStab is always the best choice because it uses less memory than GMRES”: lower basis storage addresses one constraint, while admissibility, convergence, and total cost determine usefulness. The supplied notes explicitly support conditional selection and warn against universal performance conclusions. [S1] [S2] [S3] [S4] [S5] [S6]

This report uses only the author paraphrases in `sources.json`; it neither quotes nor independently verifies the underlying references. **Assumption** labels identify supplied synthetic conditions. **Direct support** identifies statements in the notes. **Inference** labels identify recommendations or proposed methodology. No scenario contains measured performance data.

## A: exploit the supplied SPD structure

**Assumption:** A is real symmetric positive definite (SPD), and its preconditioner is fixed and SPD. Matrix and transpose applications are inexpensive; timings are unavailable.

**Direct support:** This is the standard admissible setting for preconditioned CG in the digest. PETSc's documented CG supports left preconditioning and imposes symmetry and definiteness conditions on both matrix and preconditioner. Mathematical appropriateness does not establish runtime superiority. [S1]

**Inference:** Start with preconditioned CG, preserving those conditions in the implementation. This recommendation uses known structure rather than an unmeasured speed claim. Do not assume that multiplying an SPD matrix by an SPD preconditioner produces a Euclidean-symmetric matrix suitable for an arbitrary unpreconditioned-CG wrapper; use the intended preconditioned-CG formulation. [S1]

Restarted GMRES and BiCGStab are comparison candidates if CG's observed behavior or implementation constraints warrant them. Flexible GMRES is also possible with a fixed preconditioner, but the supplied scenario does not require its flexibility. These alternatives have no demonstrated performance advantage here. GMRES introduces basis storage and a restart choice; BiCGStab avoids that growing basis but does not thereby establish a faster solve. Availability of a transpose is not a reason to prefer BiCGStab. [S2] [S3] [S4] [S6]

## B: fit the basis budget and test convergence

**Assumption:** B is real nonsymmetric, with a fixed linear preconditioner and a matrix-vector product, no transpose operation, and capacity for at most 20 GMRES orthogonalization basis vectors. Convergence is unknown. This is not a total-memory cap.

**Direct support:** Restarted GMRES controls the number of directions used in orthogonalization through its restart parameter; these directions are only part of storage. Ordinary GMRES requires linear preconditioning. BiCGStab supports nonsymmetric systems without transpose products, uses short recurrences, and remains vulnerable to breakdown or poor convergence. [S2] [S3] [S4] [S6]

**Inference:** Use restarted GMRES as the first candidate, comparing BiCGStab under the same fixed preconditioner. GMRES's Arnoldi construction applies the operator to vectors and orthogonalizes the results; it does not require a transpose product. Thus the missing transpose does not force selection of BiCGStab. CG lacks its supplied symmetry guarantee on B, so it is not an admissible default. Flexible GMRES can handle the fixed preconditioner, but no varying action presently motivates it. [S1] [S2] [S4] [S6]

Enforce the budget on actual retained basis vectors, not just a parameter named “restart.” A length-m Arnoldi cycle can retain m+1 vectors including the next direction; this algorithmic accounting is an inference, not a vector count quoted from the digest. Start with restart 19 if that implementation counts all 20 vectors against the budget. Permit nominal restart 20 only if its documented allocation and the budget's accounting keep the counted basis at 20 or fewer. Count work vectors and preconditioner storage separately in total memory. [S2]

Restarting limits storage but may impair convergence. If the allowed restart choices stagnate or incur excessive orthogonalization cost, BiCGStab is a concrete alternative, not a guaranteed rescue. Its smaller basis requirement can matter even when GMRES fits; its failure risk can outweigh that saving. There is no evidence here to rank their elapsed times. [S3] [S6]

## C: match the changing inner solve

**Assumption:** C is real nonsymmetric. Its tolerance-stopped inner iterative preconditioner may change effective action between outer iterations. Memory permits a modest basis; timings are unavailable.

**Direct support:** Ordinary GMRES requires a linear preconditioning operator. Flexible GMRES permits nonlinear preconditioning and changes between iterations; an inner Krylov solve is generally nonlinear as a preconditioner. PETSc's flexible GMRES supports right preconditioning and restarting. [S4]

**Inference:** Choose right-preconditioned flexible GMRES with a modest restart, recording the inner stopping policy. A nominally identical inner tolerance does not prove a fixed linear action. Ordinary GMRES therefore lacks the required guarantee here; ordinary BiCGStab must not silently be treated as its separate flexible variant. CG also lacks the required matrix structure. [S1] [S3] [S4]

An alternative is to redesign and verify the preconditioner as fixed and linear, then compare ordinary GMRES and BiCGStab on that changed configuration. Merely prescribing a fixed number of inner Krylov steps does not establish linearity. Budget the actual flexible implementation's storage: the digest does not promise the same footprint as ordinary GMRES. Flexibility resolves admissibility, not a universal speed ranking. [S3] [S4]

## Why the universal claim fails

**Direct support:** GMRES retains a basis, restarting can harm convergence, and BiCGStab's short recurrences do not prevent breakdown or poor convergence. Selection also depends on matrix properties and the costs of products, preconditioner applications, vector operations, and inner products. [S6]

**Inference:** A memory advantage alone cannot imply “always best.” A offers structure supporting CG; B leaves convergence unresolved within a basis budget; C calls for flexibility absent from an ordinary-BiCGStab guarantee. These are failures of the proposed decision rule, not fabricated examples of measured BiCGStab defeats. Total memory also includes the matrix, preconditioner, and work arrays, so basis savings are not automatically an equal saving in overall footprint. [S1] [S2] [S3] [S4] [S6]

## Concrete validation before deployment

The following is a proposed experiment, not an executed benchmark. Obtain representative matrices and right-hand sides for each scenario and record their provenance, dimensions, precision, structural checks, hardware, software, and threading. Within each comparison, fix the matrix, right-hand side, initial guess, and preconditioner configuration. Report any altered preconditioner as a separate configuration. [S1] [S6]

Use one explicit success target for every solver: recompute r=b−Ax and require ||r||₂ ≤ max(10⁻¹², 10⁻⁸||b||₂). These tolerances are proposed choices, not evidence-derived constants. Inspect solver-reported residuals too, but do not substitute a preconditioned or approximate norm for this test. Verify every claimed convergence and periodically recompute residuals to detect drift or stagnation. This protocol follows from the distinction in S5; even with right preconditioning, explicit verification makes achieved accuracy inspectable. [S5]

For A, compare CG against restarted GMRES and BiCGStab using the fixed SPD preconditioner. For B, sweep restart lengths 5, 10, and 19, adding 20 only after verifying the basis count; compare BiCGStab. For C, test flexible GMRES across modest restarts and recorded inner tolerances, applying the same outer target. Compare ordinary methods only after separately establishing fixed linear preconditioning. [S1] [S2] [S3] [S4]

Measure preconditioner setup separately from solve time, and report their sum and any reuse across right-hand sides. Record peak total memory, basis allocation, restart cycles, matrix products, preconditioner applications, inner iterations, and orthogonalization work. Include residual-monitoring overhead consistently. Repeat timed solves five times after a disclosed warm-up; report median and range. [S2] [S5] [S6]

Predeclare common wall-time and work limits; log breakdown, stagnation, nonfinite values, and exhausted budgets with final true residuals. Retain failures in the comparison. Choose among successful configurations using time, memory, and reliability under the common target, never unmatched iteration counts alone. Residual agreement is not itself a forward-error guarantee. These are methodological inferences, and require execution before any performance winner can be named. [S5] [S6]

Source key (supplied digest): S1, PETSc KSPCG; S2, PETSc KSPGMRES; S3, PETSc KSPBCGS; S4, PETSc KSPFGMRES; S5, PETSc KSPMonitorTrueResidual; S6, Barrett et al., *Templates for the Solution of Linear Systems*, second edition.
