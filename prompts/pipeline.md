# A2: Sequential pipeline

You are the coordinator and final integrator. Spawn exactly three subagents in
sequence, waiting for each to finish before starting the next. Each receives the
task, shared controls, and only the designated preceding artifact; avoid copying
the full coordinator chat when fresh contexts are supported. No nested spawning.

1. Planner: inspect inputs and return a concrete plan, risks, and verification
   cases. Write only in scratch/planner/. Do not implement the final solution.
2. Author: receive the plan and starter; implement or write a complete candidate
   and local checks in scratch/author/. Return it to the coordinator.
3. Reviewer: inspect that candidate against TASK.md; independently test or audit
   it. Return findings and suggested corrections in scratch/reviewer/.

Integrate the candidate, resolve supported findings, and run final checks. Do not
spawn further agents or use overlapping stage work. Log all three handoffs.
