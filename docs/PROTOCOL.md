# Protocol v0.1.0

## Question and limits

Compare final artifact quality under a common 30-minute wall-clock ceiling,
with model and reasoning effort fixed, while measuring coordination compliance
and available resource usage. The five treatments include different roles,
context separation, and communication rules. This compares complete prompted
workflows; it does not isolate graph topology as a sole causal variable.

Three tasks, five architectures: 15 first-pilot runs. The checked-in randomized
order is fixed before outcomes exist. Replications 2 and 3 are separately
randomized blocks, not repeated attempts chosen after seeing failures. If a
pilot reveals a broken task/evaluator, version the correction and restart the
affected comparison. Do not silently substitute an easier task or retain only
favorable attempts. Report each task separately; any aggregate is secondary.

## Preflight for each run

1. Use the same machine, Python executable, Codex client version, permissions,
   tools, and task version across the pilot. Record version changes if unavoidable.
   Start from a clean committed repository and follow `experiments/pilot.csv`.
2. Prepare the run with `scripts/lab.py prepare`. It copies only the selected
   task, common instructions, and selected architecture into the agent workspace.
   The source repository, evaluation code, reference controls, other tasks, and
   previous outputs are not part of the provided workspace.
3. Open a new chat with that workspace as its project root. Do not fork this
   preparation conversation or reuse previous task chats. Use Astra / High for
   root and every subagent, and verify actual settings where the client exposes
   them. Do not substitute another model or effort silently.
4. Record enabled skills, relevant instructions, tool availability, memory state,
   and the observed maximum agent concurrency. Disable optional memories for
   experimental chats where the client permits it; otherwise record the exposure.
   Do not alter personal global settings automatically. Do not attach past runs.
5. Confirm the environment supports the requested topology within four live
   agents including the root. If spawning/depth is unsupported, record the run
   as a setup failure; do not replace agents with simulated role-play.
6. The operator/evaluator files are intentionally outside the provided workspace.
   This is procedural separation, not a claim of securely hidden tests: the
   repository and filesystem may still be readable. Reading them violates the
   protocol. Stronger isolation can be a later version of the experiment.

## Start, stop, and interventions

The operator starts a monotonic timer at prompt submission and records UTC
timestamps. The agent may check elapsed time, but a prompt is not an enforced
timeout. At 30 minutes the operator stops the run, including active subagents,
and preserves the partial output. Record observed duration and stop reason.
Preparation, external evaluation, and human review are outside this interval;
agent planning, tool use, local tests, spawning, and handoffs are inside it.

No browsing, external package installation, reading outside the workspace,
or extra human hints during a run. Agents may use the supplied Python standard
library environment, shell, editor, and collaboration tools. If asked a task
clarification, reply only: "Use the provided task contract and state assumptions."
Record that intervention. Permission dialogs may be answered consistently with
the predeclared policy; log interruptions and their duration. Do not pause the
clock for ordinary tool latency. Infrastructure outages are retained as flagged
runs; any replacement gets a new run ID and a documented reason.

Existing optional personal requirements for independent subagent review are
overridden **only during the measured run** by its assigned architecture.
All architectures self-check; outside evaluators review all artifacts afterward.
Host-enforced policies always prevail, with conflicts recorded as deviations.

## Evidence and evaluation

Save final files, diff, command/test output, and a reviewed export or capture of
visible agent events. Capture actual agent IDs, parent IDs, model/effort when
available, delegation messages, completion, and handoffs. Agent-written
`execution.md` helps navigation but is self-report, not independent proof.
No private chain-of-thought is requested. Keep raw chats local until sanitized.

Fill `operator/record.json`: observed settings, timing, agent count, deviations,
and trace references. Missing telemetry is `null`, never a fabricated estimate.
Architecture and environment validity each have `true`, `false`, or `null`.
`null` means unverified. Raw task scores can be recorded for every run; only
explicitly valid runs enter the conditional quality comparison. Co-primary
outcomes are completion rate and architecture-validity rate over ALL assigned
runs, including setup/topology failures. Show these beside conditional quality,
plus every raw score and failure reason. Do not rank an architecture solely by
the quality of its few compliant successes. No invented zero-score penalty is
needed to disclose reliability. An artifact captured after the time ceiling is
not eligible unless it is the version frozen at the ceiling with that timing.

Freeze the artifact before evaluation. Run `lab.py evaluate`; code/science
cases execute individually with bounded subprocess timeouts. Manual rubric
items need a score and specific artifact/line/command evidence. For research,
automated checks only validate deliverable structure; all 100 points require
source-grounded human/external review. Do not let the producing agent grade itself.
Prefer anonymous artifact labels and a second independent rater for research;
record who rated and disagreements. If only one rater is available, disclose it.

Evaluate before providing feedback to future runs. Compute task score separately
from elapsed time, tokens, intervention count, and compliance. Do not convert
subscription usage to API dollars. A fixed wall-clock ceiling is not equal
compute: multi-agent treatments can spend more tokens. Report this tradeoff.
With three repetitions, show every observation, median and range; avoid claims
of statistical significance or domain-wide ranking.

## Archiving and extending

Use `results/<version>/<run-id>/` for sanitized artifacts, scores, and records.
Retain hashes and source revision. Never overwrite completed results. Before
sharing, remove secrets, unrelated content, personal paths, and account metadata.
Any change to tasks, source notes, prompts, rubrics, limits, or tools defines a
new experimental version. Expand task diversity before claiming generality.
