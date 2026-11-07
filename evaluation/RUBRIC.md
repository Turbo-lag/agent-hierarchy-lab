# Frozen scoring criteria v0.1.0

Scores range from 0 to 100, reported separately by task. No pilot scores exist.
Machine-readable manual criteria and anchors are in `rubric.json`; operator
score templates are generated from that file, so they cannot drift independently.

## Coding: 80 automatic + 20 manual

Eight independently executed 10-point groups in `checks.py`: empty/diamond
timing; deterministic ready-set ordering; duplicate/unknown dependencies;
input validation; cycles; immutability including failure; 2,000-node chain;
fractional/zero durations and overflow. A group earns 10 only if all assertions
pass. Timeout, crash, import failure, or failed assertion earns 0 for that group.
Case diagnostics are retained. No partial credit inside a group. Manual criteria
cover actual regression evidence and explanation/complexity (10 each).

## Science: 80 automatic + 20 manual

Eight 10-point groups: affine nonzero boundaries; constant-coefficient polynomial;
sine convergence; variable-coefficient convergence and discrete residual;
independent exponential manufactured case; input validation; smallest grid;
4,096-interval feasibility. Cases reject nonfinite outputs. Each process has a
10-second wall-clock timeout; the last case is a bounded feasibility check, not
a claim of measured O(n) scaling. Manual criteria cover the submitted verification
study and mathematical explanation (10 each). Evaluators rerun verify.py and
independently compare its numbers to solver output. Do not infer physical validity.

## Research: 100 manual

The five anchored items in rubric.json total 100. The evaluator checks report
length and claim schema automatically but awards no factual points from format.
Use the frozen `sources.json`, not updated webpages or outside knowledge, to
audit source support. Credit alternative defensible recommendations; do not
require one exact narrative. Note digest limitations and underspecified cases.

The canonical reader expectations are: A supports CG when both operator and
preconditioner meet the SPD assumptions; B admits a measured comparison of
restarted GMRES and BiCGStab without a universal winner; C needs flexible
preconditioning support (FGMRES is one defensible choice). Claims of measured
superiority are unsupported because no timings were supplied. These expectations
do not excuse missing citations or turn a correctly named solver into full credit.

## Validity and missing data

Before accepting a score, complete the operator record, including explicit
architecture/environment validity and evaluator identity. `null` is pending.
Record actual hierarchy evidence, not only execution.md. Unsupported delegation,
extra agents, model substitutions, outside inputs, and unlogged human hints are
deviations. Preserve their raw scores but exclude them from the primary valid-run
conditional-quality comparison. Completion and architecture-validity rates over
all assigned runs are co-primary outcomes and appear beside quality. Record
setup failures and timeouts; do not rerun silently or hide failed assignments.

For manual items use the stated anchors, cite artifact locations and concrete
checks, and document subscore calculations. The script enforces numeric bounds
and evidence presence; it cannot verify a human judgment. Two raters are preferred
for research; if only one is available, disclose that limitation in the record.

## Evaluator qualification

`controls.py` supplies non-pilot positive controls. Automated tests also check
that the intentionally defective starter and controlled corruptions fail for the
intended reasons. Controls are excluded from agent workspaces. Publicly readable
evaluation code is not a secure hidden test set. Scoring correctness and pilot
model performance are different claims.
