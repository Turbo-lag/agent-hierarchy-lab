# A5: Two-level hierarchy

You are the project lead and final integrator. Spawn exactly one team lead.
Instruct that team lead to spawn exactly two workers concurrently: one for
construction/authoring, one for verification/evidence. Total topology is root
→ team lead → two workers (four agents including you). No further delegation.

Give the team lead TASK.md and the common controls. The lead divides the work,
assigns scratch/implementation/ and scratch/verification/, reviews both workers'
outputs, and returns an integrated proposal plus unresolved issues in scratch/lead/.
Workers report to the team lead. You communicate through the team lead rather
than bypassing it to direct the workers. The lead may send follow-up messages.

Integrate the returned proposal and run final checks yourself. If nested
delegation is unavailable, report a topology/setup failure rather than flattening
the hierarchy. Log actual parent-child relationships.
