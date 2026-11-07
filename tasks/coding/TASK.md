# Coding task: repair a dependency scheduler

The supplied `scheduler.py` has several interacting defects. Repair its public
function `schedule(tasks)` without changing the API. Python standard library only.

## Contract

`tasks` is a list of dictionaries with exactly the required keys `id`, `duration`,
and `deps` (additional keys may be ignored). IDs are unique nonempty strings.
Duration is an int or float, excluding bool, convertible to a finite nonnegative
binary64 float. Convert durations to float and use floating-point scheduling
arithmetic; reject conversion overflow with ValueError. `deps` is a list
of IDs of tasks in the same input. Dependencies can appear later in the input.
Repeated dependencies are allowed and mean the same thing as one dependency.
Reject malformed inputs, unknown dependencies, self-edges, and any directed
cycle with `ValueError`. Do not mutate any part of the input.

There is unlimited worker capacity; this is an earliest-start dependency
schedule, not resource-constrained scheduling. Tasks without dependencies start
at 0. Each other task starts at the maximum finish time of its dependencies.
Return `{id: {"start": number, "finish": number}, ...}`. Dictionary iteration
order must be the lexicographically smallest topological ordering: at each
step, choose the smallest ID among all currently dependency-ready tasks. This
ordering is independent of start time. Empty input returns `{}`. Zero durations
are valid. If a computed start/finish becomes nonfinite, raise `ValueError`.

Support at least a chain of 2,000 tasks without recursion failure. Avoid
enumerating all schedules or allocating a dense task-by-task matrix. A graph
algorithm with O(V+E) storage and O((V+E) log V) or better time is expected.

## Deliverables

- Fixed `scheduler.py`.
- `test_solution.py`: regression tests including malformed data, graph corner
  cases, input immutability, and a chain long enough to expose recursion limits.
- `report.md`: describe defects, fixes, actual commands/results, and complexity.
- `execution.md` as required by the experiment instructions.

Run the supplied smoke test with `python3 -m unittest discover -s tests -v`.
It is deliberately incomplete. Do not assume passing it establishes correctness.
Scoring: evaluator contract tests 80 points; independent regression evidence and
explanation 20 points. Tests may use different inputs satisfying this contract.
