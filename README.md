# Agent Hierarchy Lab

Reproducible experiments comparing five prompted agent organizations in local
Codex, with GPT-6 Astra held fixed across three tasks.

**Status: preparation only. No pilot runs or model-generated results yet.**
Repository visibility: private; public release is a separate decision.

## Experiment v0.1

| Task | Deliverable | Evaluation |
| --- | --- | --- |
| `coding` | Repair a dependency scheduler | Contract tests (80), review evidence (20) |
| `science` | Solve a 1D variable-coefficient elliptic PDE | Numerical/contract checks (80), verification report (20) |
| `research` | Recommend iterative solvers for three scenarios | Evidence-based manual rubric (100) |

Architectures: `solo`, `pipeline`, `manager`, `candidates`, `hierarchy`.
The first pilot is 15 runs (one per cell). A later replication phase contains
30 additional runs for three observations per cell in total. One task per
category is a case study, not evidence of general superiority across a domain.

## Before starting a run

Requires Python 3.11+ and Git; no third-party Python packages or API key.
All commands below are local, from this repository root.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/lab.py plan
python3 scripts/lab.py prepare --run-id coding-solo-r1
```

`prepare` only creates files. It never starts Codex or any agent. It refuses to
overwrite an existing run. It creates an agent workspace and a separate operator
folder under ignored `runs/<run-id>/`. Preparation requires a clean committed
repository so the experiment inputs have an unambiguous revision.

When ready to run: follow [the operator procedure](docs/PROTOCOL.md), open a
**fresh Codex chat rooted at the generated `workspace/`**, select Astra / High,
and paste `workspace/PROMPT.md`. Fill the operator record and start the timer at
submission. Stop at completion or 30 minutes, whichever comes first. Do not run
from this authoring chat. No chat is started by this repository's scripts.

## After a run (commands provided for later use)

```sh
python3 scripts/lab.py evaluate --run-dir runs/coding-solo-r1
# Fill operator/manual-score.json and operator/record.json using the rubric.
python3 scripts/lab.py summarize --run-dir runs/coding-solo-r1
```

Evaluation executes submitted Python code. Use the same constrained local
environment as the run; the evaluator is not a security sandbox. `summarize`
requires completed scores with evidence and explicit validity decisions. Missing
scores remain incomplete, never zero-filled or reported as a finished result.

## Contents

- [Protocol and run checklist](docs/PROTOCOL.md)
- [Architecture definitions](prompts/) and shared controls
- [Three task bundles](tasks/), including a frozen research source digest
- [Scoring criteria](evaluation/RUBRIC.md) and executable grading cases
- [Randomized run schedule](experiments/pilot.csv) and [fixed settings](experiments/config.json)
- [Preparation evidence](docs/PREPARATION.md)

The code/science tasks are authored benchmark fixtures. Science verification is
analytical, not physical validation. Research scenarios are synthetic; source
notes are attributed paraphrases of real technical references. No performance
measurements are supplied or invented. The fixed research digest, rather than
live browsing, is the v0.1 evidence corpus.

Results will be added under `results/` after measured runs and a privacy check.
Raw working directories, local paths, and chat exports are ignored by default.

## Reproducibility and limitations

The complete task/prompt/rubric bundle is hashed for each run. Requested and
observed models, reasoning settings, hierarchy, elapsed time, and usage are
recorded separately. Prompt instructions are not proof of actual orchestration.
Fresh chats reduce carryover but do not guarantee absence of account memories
or backend model drift. The protocol addresses these limits explicitly.

No license has been selected yet; private preparation does not grant a public
reuse license. Before public release, choose a license and review source notices.
