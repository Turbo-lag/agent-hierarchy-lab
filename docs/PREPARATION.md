# Preparation evidence — 2026-11-07

Historical snapshot from November 7, 2026, before the first model run. The [completed pilot](../results/) has since been published.
Baseline: new empty repository on main. Reviewed scope is the initial project
commit containing this record. The frozen task/prompt/evaluator/protocol bundle
SHA-256 is `7916d9b7f48bb2580dd66868e4b2b037d74a3df6112d7474a1209425af49f176`. Each prepared run also records the source Git commit.

## Repository and configuration

Local macOS arm64 host; Python 3.14.8 from Homebrew; Git 2.56.0.
Codex CLI version probe: 0.167.0-alpha.3.2. That read-only probe emitted a sandbox
warning about creating PATH aliases; it still returned its version. No Codex
model session, config change, package install, or pilot execution was performed.
Python 3.11+ is the intended minimum; older supported interpreters were not
separately executed in this preparation.

The project uses only the Python standard library. Existing sibling projects
were not modified. GitHub destination is Turbo-lag/agent-hierarchy-lab, private,
main. Generated run workspaces and raw operator records are ignored by Git.

## Correctness checks

Local command, from the repository root:

```sh
python3 -W error::ResourceWarning -m unittest discover -s tests -v
```

Outcome: 16 tests passed. Coverage includes all 16 automatic scoring groups on
positive controls; broken starter failures; deliberate minimum/maximum, source
sign, and boundary-sign mutations; an independent discrete-sine eigenvector
oracle; multi-file and dataclass imports; optimized-environment resistance;
premature successful process exit; research structure without factual scoring;
clean-tree and no-overwrite preparation; complete 45-assignment schedule;
missing/manual/automatic score validation; artifact and protected-input changes;
and time-cap eligibility. Controlled sample scores in temporary test directories
are synthetic workflow checks, not pilot observations.

The positive numerical control was executed for n=16,32,64,128. Its constant-k
sine max error fell from 3.218964440079519e-3 to 5.020091591312337e-5, with final
observed order 2.0001303662649175. The variable-k manufactured case fell from
3.1866457845661778e-3 to 4.984430213639257e-5, with final order
1.9998345376915525. These are analytical numerical-verification controls, not
physical validation, not agent-generated solver results, and not speed benchmarks.

## Independent review

A separate reviewer inspected contracts, prompts, protocol, grading code,
controls, and preparation/scoring tooling against the empty-repository baseline.
Accepted findings were reproduced and resolved:

- Support submission-local helper imports and dataclass module registration.
- Bound duration arithmetic to finite binary64 conversion, including combined
  integer overflow cases.
- Keep Python optimization from disabling grading assertions.
- Require a case-completion marker; process exit zero alone is insufficient.
- Validate automatic records against canonical case coverage and scoring bounds.
- Fingerprint normative protocol and repository instructions.
- Report all-assignment completion/compliance rates beside conditional quality.

The reviewer rechecked the final fixes and reported no unresolved findings in
that reviewed scope. Meaningful regression controls accompany the code fixes.

## Resources and limits

The numerical control uses a tridiagonal O(n) method; no empirical scaling or
hardware-performance study was conducted. The long-chain and 4096-interval
cases are feasibility checks with per-case time limits. No package/build matrix,
GPU, MPI, live model, or full CI/CD campaign was run or needed for this kit.

The actual Codex ability to execute each topology, exposed telemetry, model
settings, and optional memory controls must be observed at run preflight. They
have deliberately not been tested with a pilot. A prompt is not proof of
compliance. Research factual scoring is manual; no inter-rater reliability has
yet been measured. The provided source digest is frozen and attributed, but is
not the full source literature. Evaluator separation is procedural and does not
provide a secure adversarial sandbox. Nothing here establishes which
architecture wins or how difficult Astra will find these tasks.
