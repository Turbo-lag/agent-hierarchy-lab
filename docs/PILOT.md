# How the isolated pilot was measured

The study compares five complete prompting and coordination strategies on the same three tasks. Its unit of observation is one final submission from one assigned workflow on one task. The isolated cohort contains 15 submissions, one per pairing. All 15 completed, all 15 passed the workspace boundary check, and 14 followed every architecture rule.

## Treatments

| Workflow | What happens during the run |
|---|---|
| [Solo](../prompts/solo.md) | One agent plans, solves, tests and reviews in one context. |
| [Sequential pipeline](../prompts/pipeline.md) | A coordinator passes work through a planner, author and reviewer in sequence, then integrates the result. |
| [Manager–workers](../prompts/manager.md) | A manager assigns three concurrent workers to the core solution, edge cases and verification, then integrates their proposals. |
| [Independent candidates](../prompts/candidates.md) | Three workers independently attempt the complete task. The root checks the candidates, selects a base and can repair it before submission. |
| [Two-level hierarchy](../prompts/hierarchy.md) | A root delegates to a team lead, who manages a construction worker and a verification worker. The lead reviews their work before handing it to the root. |

These treatments change roles, context sharing and communication together. The experiment measures their combined effect on these tasks. For each measured session the operator verified the model and effort settings, actual parentage, concurrency and visible file operations. A four-session pipeline, for example, used its three child sessions sequentially.

## Environment and timing

The frozen task, prompt and scoring bundle came from [commit 380526b](https://github.com/Turbo-lag/agent-hierarchy-lab/tree/380526b8c613be6ed46e23e2af24d47f25c04f2c). The isolated cohort is labeled **v0.1.1-isolation**. The [original protocol](PROTOCOL.md) and [schedule](../experiments/pilot.csv) describe preparation and planned repetitions. The isolated observations have their own run IDs and include supplemental runs and reruns. The measured runs were grouped by task. Within each task, the actual chronological order was:

| Task | First to last |
|---|---|
| Research | Sequential pipeline → manager–workers → solo → independent candidates → two-level hierarchy |
| Science | Independent candidates → solo → manager–workers → sequential pipeline → two-level hierarchy |
| Coding | Sequential pipeline → independent candidates → two-level hierarchy → manager–workers → solo |

Coding ran serially, with external grading completed before the next launch. The schedule and the service environment are sources of timing variation.

Each run used local Codex CLI 0.167.0-alpha.4.1 with GPT-6 Astra at High reasoning effort, Python 3.14.8 and at most four active agents including the root. Each started in a fresh task workspace. The runtime restricted task-file access to that workspace and disabled network access, external skills and account memories for the participants. Workers had assigned scratch directories and the root integrated the final artifacts. Runtime metadata and visible tool operations support the compliance assessment.

Elapsed time covers CLI launch through exit, including delegation, checks and integration. Preparation and external grading took place outside that interval. The cap was 1,800 seconds per attempt. Usage sums the final cumulative counters of distinct measured sessions. Input includes cached input, and output includes reasoning tokens. The release reports those components separately. The final two coding runs explicitly requested the original priority service tier after the user configuration default changed. The service tier actually delivered by the provider was unobserved.

## Scoring and independent checks

| Task | Scoring | What the evidence establishes |
|---|---|---|
| Coding | Eight executable contract groups × 10 points, plus 10 for regression evidence and 10 for explanation | All five passed all eight groups. Each submission's own test suite passed on its repair and failed on the original starter. All five also passed 113 additional unscored graph diagnostics. |
| Science | 80 executable points and 20 for the numerical study and derivation | The submitted solvers reproduced the expected second-order convergence for two manufactured solutions. These are analytical numerical checks. |
| Research | 30 for mathematical admissibility, 25 for source fidelity, 20 for tradeoffs, 15 for validation design and 10 for clarity | The assessment concerns recommendations justified by the frozen six-source digest. Timing comparisons between numerical solvers were outside this task. |

The operator froze submissions before grading. Automatic evaluation of code ran after the measured interval, with artifact hashes checked against the frozen copy. Manual criteria used two AI assessments. The first rater could see the architecture. The second worked from an artifact packet with execution details withheld, but some reports and one reviewer label revealed the organization. No human rater participated. Individual scores and checks are published in each submission's assessment file. [Scoring rubric](../evaluation/RUBRIC.md) · [Executable checks](../evaluation/checks.py)

## Eligibility and exceptions

- **Research, solo.** Eleven of twelve claims had sufficient source support. The initial ratings were 100 and 97.92. Adjudication accepted the source-fidelity deduction for claim C03, yielding 22.92/25 for evidence and 97.92 overall. The claim concerned operator requirements for GMRES under the no-transpose constraint. [Claim ledger](../results/pilot/research/solo/claims.json)
- **Science, independent candidates.** A worker created shared smoke-test bytecode outside its assigned scratch directory. The root later removed the file. The numerical submission scored 100 and the overall workspace boundary held, but the architecture check failed. The run counts in completion and workload totals. [Submission and score](../results/pilot/science/candidates/)
- **Coding, independent candidates.** A worker also invoked a shared smoke test. The retained cache timestamp predates that invocation and matches the root's earlier test. A replay on a copy reused the cache. No worker write to the shared cache was evidenced in this observation. [Submission and score](../results/pilot/coding/candidates/)
- **Two earlier research attempts.** The original manager and pipeline used v0.1.0 and remain outside all 15-run totals. Both scored 100. The manager completed in 183.2 seconds. The pipeline completed in 357.1 seconds and accessed an outside skill. Their summary records are included in the JSON download. [Historical submissions](../results/historical/)

## The next experiment

The pilot supports a narrow descriptive comparison. Each architecture saw one task in each domain, 14 raw scores reached the ceiling, and equal time caps permitted very different token usage. Model service latency, cache state and run order could affect timings. The small differences do not establish a general advantage for any workflow.

The proposed follow-up asks whether hierarchy improves verified solve rate as the **whole team** receives a larger inference budget. It would use held-out problems at multiple difficulties, including both independently solvable components and tightly dependent steps. Solo, independent candidates and manager–workers provide comparisons for extra attempts, parallel work and management depth. A proposed first round would cross 12 problems with five workflows and two budgets, after separate calibration. These are plans for future measurement.

[All measured results](../results/) · [Machine-readable observations](data/pilot.json)
