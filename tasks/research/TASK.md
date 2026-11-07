# Research task: an evidence-grounded iterative-solver recommendation

Use only `sources.json`, a frozen digest of real technical references, and the
synthetic scenarios below. No browsing or additional sources. The digest uses
author paraphrases rather than full papers; this task measures bounded evidence
synthesis, not exhaustive literature search or experimental performance.

Advise a team choosing among CG, restarted GMRES, BiCGStab, and flexible GMRES.
Evaluate the claim: "BiCGStab is always the best choice because it uses less
memory than GMRES." Do not fabricate benchmarks, timings, or cited quotations.

## Synthetic scenarios (assumptions, not measured datasets)

A. Real SPD diffusion matrix; a fixed SPD preconditioner is available. Neither
the matrix nor its transpose is expensive to apply. No solver timings exist.

B. Real nonsymmetric advection-diffusion matrix; a fixed linear preconditioner
and matrix-vector product are available, but no transpose operation. The team
can afford at most 20 basis vectors for GMRES orthogonalization (this is a basis
budget, not a total-memory limit). Convergence behavior is unknown.

C. Real nonsymmetric coupled-system matrix. The preconditioner is an inner
iterative solve stopped at a tolerance; its effective action can change between
outer iterations. Enough memory is available for a modest basis. No timing data.

## Deliverables

1. `report.md`, 900-1400 words: scenario recommendations, admissibility,
   alternatives, memory/convergence tradeoffs, the universal claim, and a concrete
   experiment to resolve unknowns. Cite source IDs [S1] etc next to supported
   claims. Separate direct source support, your inference, and scenario assumptions.
2. `claims.json`: JSON list of 8-12 objects with keys `id`, `claim`, `source_ids`
   (nonempty list drawn from S1-S6), `support` (`direct` or `inference`),
   `rationale`, `limitation`. Each rationale must explain how the referenced
   note supports that claim; merely naming a source is insufficient.
3. `execution.md` as specified by the experiment.

Your validation proposal must compare a common true-residual target, report
setup and solve costs separately, account for memory/restarts and failures,
and avoid choosing a winner from unmatched iteration counts alone.

Scoring is a 100-point anchored external-review rubric: mathematical admissibility
(30), evidence and citation fidelity (25), tradeoffs/uncertainty (20), validation
design (15), and clarity/completeness (10). Deliverable checks do not establish
that the claims are true. A defensible conditional recommendation is preferable
to an unsupported universal ranking.
