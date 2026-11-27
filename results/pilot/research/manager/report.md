# Conditional solver recommendations from bounded evidence

BiCGStab is not established as universally best by its storage advantage. The supplied digest says it avoids explicitly retaining GMRES's growing basis, but also identifies possible breakdown and poor convergence. Restarting bounds GMRES's basis storage and may impair convergence. Method choice therefore depends on admissibility, convergence, storage, and the costs of matrix products, preconditioning, vector operations, and inner products. Lower basis storage alone cannot determine the best solver. [S2][S3][S6]

All three matrices, preconditioners, and resource constraints below are **synthetic assumptions**, not measured datasets. **Direct support** means a statement in the supplied author-paraphrased notes, not a quotation from a full paper. The recommendations and validation design are **inferences** from those notes. No source supplies scenario timings, and no experiments have been performed here. [S1][S2][S4][S6]

## A: Exploit the SPD structure

**Assumptions:** A is real symmetric positive definite (SPD), with a fixed SPD preconditioner; matrix and transpose applications are inexpensive. **Direct support:** this is the standard admissible preconditioned-CG setting in the digest. The documented PETSc CG implementation supports left preconditioning. [S1]

**Recommendation—inference:** start with preconditioned CG because its stated mathematical conditions are satisfied. This is a structure-based default, not a measured claim that CG wins on runtime. The cheap transpose does not establish an advantage for another solver, and BiCGStab's comparison with GMRES storage supplies no reason to discard admissible CG. [S1][S3][S6]

Restarted GMRES and BiCGStab are reasonable comparison alternatives, using supported left or right preconditioning, if CG's observed cost or convergence is unsatisfactory. Flexible GMRES is also a candidate, but its allowance for changing or nonlinear preconditioners addresses no stated need here. These are conditional alternatives; the digest does not rank them for this SPD problem. Preserve the fixed SPD preconditioner assumptions when testing CG, and investigate any violation before interpreting a failure as an unfavorable solver comparison. [S1][S2][S3][S4][S6]

## B: Compare bounded-restart GMRES and BiCGStab

**Assumptions:** B is nonsymmetric, a fixed linear preconditioner and matrix-vector product exist, no transpose operation exists, and GMRES has a budget of at most 20 orthogonalization basis vectors. Convergence is unknown. **Direct support:** BiCGStab handles nonsymmetric systems without a transpose product. Restarted GMRES offers a configurable number of directions for orthogonalization; its directions are only part of total solver storage. [S2][S6]

**Recommendation—inference:** evaluate restarted GMRES within that basis budget alongside BiCGStab. Use nominal restart lengths such as 5, 10, and 20 only after checking the implementation's basis-count convention and allocated orthogonalization vectors; reduce a setting if it exceeds 20. Work vectors, preconditioner storage, and other allocations must still be reported, but the scenario does not impose a total-memory cap. The largest feasible restart is not automatically optimal: longer cycles retain more information while increasing basis storage and orthogonalization work; restarting can damage convergence. [S2][S6]

BiCGStab is particularly attractive if feasible GMRES restarts give an unsatisfactory cost/convergence balance, exactly the conditional motivation described by its documentation. Its short recurrences and lack of a transpose requirement fit B, but do not guarantee success or lower time to the target residual. [S3][S6]

Standard CG lacks its required symmetry/definiteness justification for this nonsymmetric matrix. Flexible GMRES can accommodate the stated fixed linear preconditioner, but its additional flexibility is not required by B; include it only with a concrete implementation or cost reason. Ordinary GMRES is compatible with the fixed linear action, and the absence of a transpose does not rule out these GMRES methods. This operation-compatibility statement is an algorithmic inference, not an explicit statement in the digest; verify that the chosen implementation accepts the supplied operations. These admissibility conclusions are not performance rankings. [S1][S2][S4][S6]

## C: Match the changing preconditioner

**Assumptions:** C is nonsymmetric and its preconditioner is an inner iterative solve stopped at a tolerance. Its effective action may change between outer iterations; memory permits a modest basis. **Direct support:** ordinary GMRES requires a linear preconditioning operator, whereas flexible GMRES accommodates nonlinear action and changes between iterations. The digest explicitly identifies an inner Krylov solve as generally nonlinear when used as a preconditioner. PETSc FGMRES supports right preconditioning and restarting. [S4]

**Recommendation—inference:** choose right-preconditioned flexible GMRES as the initial candidate, with a documented modest restart. Reusing the same inner code and stopping tolerance does not establish a fixed linear operator. The scenario matches the flexibility requirement, but supplies no evidence that FGMRES will be fastest or will converge satisfactorily. Its storage must be measured rather than assumed identical to ordinary GMRES. [S4]

CG lacks admissibility for the stated nonsymmetric matrix. Ordinary GMRES becomes a defensible alternative if the effective preconditioning action is demonstrably fixed and linear; that would be a changed experimental configuration, not the original C. Likewise, the supplied notes do not establish ordinary BiCGStab as appropriate for this changing inner solve: flexible variants are separate implementations. Do not silently replace ordinary BiCGStab with one of those variants and attribute the result to the original choice. [S1][S3][S4]

## A concrete comparison to resolve the unknowns

The following is a **proposed protocol**, not a source-supplied experiment. For each scenario, record the matrix, right-hand side, initial guess, numeric precision, hardware, implementation, and preconditioning side. Hold these fixed across comparable candidates and document every exception. Use identical fixed preconditioner setups in A and B; in C record inner method, tolerance, iteration limits, and actual inner work. A fixed-action alternative in C must be reported as a separate configuration. Costs depend on these operations and cannot be recovered from outer iteration counts alone. [S4][S6]

Choose one common true-residual target before running, for example

`||b - A*x||_2 <= max(1e-8 * ||b||_2, 1e-12)`.

These tolerances are proposed choices, not measured or universally appropriate values; the absolute floor also covers a zero right-hand side. Recompute the true residual explicitly at final acceptance for every solver, with a common diagnostic cadence if comparing residual histories. Record solver-reported norms separately: they can be preconditioned or approximate, and therefore should not automatically be read as `||b-A*x||`. Report monitoring and final-verification overhead consistently; even with the documented norm equivalence for right preconditioning, explicit verification makes the achieved criterion inspectable. [S5]

Measure setup time separately from solve time, and report both one-system total cost and any explicitly defined amortization over repeated solves. Count matrix products, preconditioner applications, inner iterations, and outer iterations; report elapsed time and variability over five timed repetitions on the same environment. Iteration counts alone are not matched units of work across these methods, and fewer iterations can be offset by expensive setup or applications. [S6]

Record restart lengths and completed cycles, actual retained basis counts, solver-workspace and preconditioner memory, and peak total memory using a consistent measurement scope. Enforce B's basis cap independently of those totals. Predeclare common elapsed-time and work limits; record breakdown, stagnation, exhaustion of limits, and missed residual targets as failures rather than successful timings. Compare target-reaching configurations by total cost and memory, with reliability visible. Favor CG in A and FGMRES in C provisionally on admissibility grounds; select between feasible GMRES restarts and BiCGStab in B from these measurements. No universal winner follows from the available evidence. [S1][S2][S3][S4][S6]
