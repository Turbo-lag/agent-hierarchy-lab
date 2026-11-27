# Conditional recommendations for the three systems

The claim “BiCGStab is always the best choice because it uses less memory than GMRES” is unsupported. Avoiding GMRES’s retained basis is a useful storage advantage, but does not establish minimum total memory, fastest time, or reliable convergence. BiCGStab can converge poorly or break down; restarting GMRES limits storage but can impair convergence. Selection also depends on matrix structure and the costs of products, preconditioning, and vector operations [S2] [S3] [S6]. My recommendations are CG for A, a budgeted restarted-GMRES trial alongside BiCGStab for B, and flexible GMRES for C. These are inferences from admissibility and resource constraints, not measured rankings.

Only the supplied frozen, paraphrased digest supports source claims below. “Direct support” identifies what its notes establish; “recommendation” and “proposed experiment” identify methodological inferences. The matrices, preconditioners, and resource descriptions are synthetic assumptions from the task. No supplied source provides scenario timings, and no numerical experiment has been run.

## A: exploit the specified SPD structure

**Scenario assumptions:** A is real symmetric positive definite (SPD), and its preconditioner is fixed and SPD. Matrix and transpose applications are inexpensive; their precise costs remain unknown.

**Direct support:** This is the standard admissible CG setting specified in S1, whose PETSc implementation supports left preconditioning. S1 explicitly separates mathematical appropriateness from measured runtime. General selection guidance makes matrix properties relevant alongside operation and storage costs [S1] [S6].

**Recommendation:** Start with left-preconditioned CG because the supplied assumptions meet its documented structural requirements. Check that the implemented operator and preconditioner actually preserve those properties; the label “diffusion” alone would not establish them. No transpose-based advantage determines this recommendation. Restarted GMRES and BiCGStab can be comparison alternatives, but their presence does not justify discarding the available SPD structure or claiming CG is fastest [S1] [S6]. Flexible GMRES offers a capability for variable or nonlinear preconditioning that this fixed-preconditioner scenario does not require [S4]. If implementation checks invalidate SPD assumptions, reconsider admissibility before interpreting a failed CG run.

## B: test the storage–convergence compromise

**Scenario assumptions:** B is nonsymmetric, has a fixed linear preconditioner and matrix-vector product, and provides no transpose product. At most 20 basis vectors may participate in GMRES orthogonalization. Convergence is unknown.

**Direct support:** Restarted GMRES’s restart parameter controls participating Krylov directions, which constitute only part of solver storage [S2]. Restarting bounds basis storage but may impair convergence [S6]. BiCGStab supports nonsymmetric systems without a transpose product, uses short recurrences, and remains vulnerable to breakdown or poor convergence [S6]. Its documentation specifically motivates it when GMRES restart choices give an unsatisfactory expense/convergence balance [S3]. Ordinary GMRES requires a linear preconditioning operator, which the scenario supplies [S4].

**Recommendation:** Use restarted GMRES as an initial baseline, testing restart settings 5, 10, and 20 against BiCGStab. BiCGStab’s no-transpose capability is explicit; the proposed GMRES baseline also requires confirming that the chosen implementation needs no unavailable operations [S6]. Configure restart at or below 20 and verify the implementation’s actual orthogonalization-direction allocation. If a nominal setting retains more than 20 basis vectors, reduce it before running; the budget takes precedence over the proposed settings. Do not equate a restart value with a total-vector limit: auxiliary vectors, workspace, and preconditioner storage require separate accounting [S2].

Prefer BiCGStab if it reaches the common accuracy target reliably with better measured cost, especially if allowed GMRES restarts stagnate. Prefer a successful GMRES configuration if BiCGStab fails or costs more. Neither outcome is established in advance [S3] [S6]. CG lacks its stated SPD justification for this nonsymmetric matrix [S1]. Flexible GMRES is an available alternative, but flexibility supplies no demonstrated benefit for the assumed fixed linear action and no documented universal speed advantage [S4].

## C: accommodate the changing inner solve

**Scenario assumptions:** C is nonsymmetric. Preconditioning uses an inner iterative solve stopped at a tolerance, so its effective action can change across outer iterations. Memory permits a modest basis.

**Direct support:** Ordinary GMRES requires linear preconditioning; an inner Krylov solve is generally nonlinear as a preconditioner. Flexible GMRES accommodates nonlinear preconditioning and changes between iterations. The documented implementation uses right preconditioning and supports restarting [S4].

**Recommendation:** Use right-preconditioned flexible GMRES, with a modest restart chosen by measured memory and convergence. It directly addresses the supplied variability; this establishes suitability, not superior runtime. Do not assume its storage equals ordinary GMRES’s storage [S4]. The digest offers no basis for treating ordinary BiCGStab as interchangeable with a flexible variant: S3 explicitly distinguishes those implementations. Accordingly, ordinary BiCGStab is not a justified default for this changing action, rather than being declared universally invalid [S3] [S4]. CG also lacks the required SPD justification [S1].

Ordinary GMRES becomes a defensible comparator only after establishing that the effective preconditioner is fixed and linear. Merely selecting a fixed number of inner Krylov iterations does not, from this digest, establish linearity. A redesigned fixed linear preconditioner would define a separate experimental condition, and its results must not be attributed to the original scenario [S4].

## Proposed experiment: comparable accuracy, complete costs

This is a protocol proposal inferred from S5’s residual distinction and S6’s cost guidance, not an existing benchmark. Before execution, obtain or construct representative matrices and document their provenance; none are supplied here. Freeze right-hand sides, initial guesses, precision, hardware, implementation versions, and preconditioner parameters. Document matrix dimensions and the checks supporting each scenario’s assumptions. Within each scenario, use identical inputs across candidates. Keep the fixed preconditioner identical for A/B; keep C’s inner tolerance and safeguards identical across flexible-GMRES configurations [S1] [S4] [S6].

Use the common success condition

`||b - A*x||_2 <= max(1e-12, 1e-8 * ||b||_2)`.

These tolerances are explicit experimental choices, requiring confirmation against application scaling. The absolute term covers a zero right-hand side. Recompute the true residual at termination and common checkpoints every ten outer matrix products, logging both true and solver-reported norms. A solver’s internal stopping flag alone is insufficient: its norm may be preconditioned or approximate [S5]. If it stops before meeting the true target, tighten its internal criterion and continue within the same budget; count all work. Record verification products and their overhead separately and consistently.

Test CG, GMRES(20), and BiCGStab for A; GMRES(5/10/20) and BiCGStab for B; and flexible GMRES(10/20), subject to measured memory, for C. Use compatible documented preconditioning sides: left for A comparisons, right for B and C [S1] [S2] [S3] [S4]. Predeclare per-run limits of 2,000 outer matrix products and 600 solve seconds, plus 20,000 inner matrix-vector products for C. Count inner work separately from outer work. These are proposed resource limits, not reported measurements; apply identical limits within comparisons.

Report preconditioner/setup time separately from solve time, and show setup-plus-solve totals for one right-hand side and any stated reuse workload. After one consistently handled warm-up, collect five measured repetitions per configuration, reporting median and range. Record actual peak solver and preconditioner storage, retained orthogonalization directions, restart events, matrix products, preconditioner applications, inner work, and residual histories. Classify breakdown, nonfinite arithmetic, budget exhaustion, memory violations, and target failures explicitly; preserve failed runs in the results [S2] [S3] [S6].

Choose among configurations that satisfy accuracy and resource constraints using reliability and measured total cost appropriate to the intended reuse. Iteration counts remain diagnostic: unequal work per iteration, restarts, setup expense, and different achieved residuals prevent an unmatched count from establishing a winner [S5] [S6].
