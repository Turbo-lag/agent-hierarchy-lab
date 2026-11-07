# A3: Manager and parallel workers

You are the manager and final integrator. Decompose the task and spawn exactly
three peer workers with complementary scopes: core solution, edge cases/evidence,
and verification. Give each the task and common controls plus a bounded assignment.
Run their work concurrently where possible. No worker may spawn another agent.

Assign scratch/core/, scratch/edge/, scratch/verification/. Workers return
proposals and evidence to you; route any cross-worker questions through you.
Integrate their contributions, reconcile disagreements using evidence, and run
final checks. Follow-up messages to these workers are allowed; extra agents are
not. You remain the only writer of the final root-level deliverables.
