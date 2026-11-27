# Dependency scheduler repair

The scheduler now validates the complete input, builds a sparse dependency graph,
and returns an earliest-start schedule in the lexicographically smallest
currently-ready order. It preserves all caller-owned input containers.

## Defects and fixes

The starter sorted the caller's task list in place, confused alphabetical order
with dependency order, and used the minimum prerequisite finish rather than the
maximum. It also lacked complete type/schema validation, duplicate-ID detection,
dependency validation, cycle detection, finite-float conversion, and arithmetic
overflow checks.

The repair collects and validates all task records before resolving dependency
references, so later input entries may be prerequisites. It requires list/dict
containers, nonempty unique string IDs, int/float durations excluding bool, and
list dependencies. Durations are converted to float with conversion overflow
reported as ValueError; negative or nonfinite values are rejected. Additional
record fields are ignored. Duplicate dependency entries create only one edge.
Unknown dependencies, malformed dependency IDs, self-edges, and cycles raise
ValueError.

Iterative Kahn traversal uses a min-heap of currently ready IDs. A newly ready
smaller ID therefore precedes larger IDs already in the heap, independently of
start time. Successor start times accumulate the maximum predecessor finish;
all arithmetic uses floats and nonfinite computed times raise ValueError.
Unprocessed vertices after traversal indicate a directed cycle. The algorithm
uses no recursion, dense adjacency matrix, or schedule enumeration.

## Verification before root integration

All checks were local in the supplied workspace using Python 3.14.8, shell
login=false, and bytecode writing disabled. All test data are synthetic.

The independent regression suite has 35 methods covering malformed inputs,
forward references, repeated dependencies, graph corner cases, dynamic lexical
ordering, timing-independent order, floating-point rounding and overflow,
accepted/rejected-input immutability, a reversed 3,000-task chain, and a
5,000-task sparse graph. It includes 60 fixed-seed DAG cases checked against a
separate repeated-scan oracle. Against the starter, the suite reported 22
failures and 99 subtest errors across 35 methods. Against the construction
candidate, all 35 regression methods and the supplied smoke test passed.

Construction checks also exhaustively compared all 4,096 directed four-node
graphs without self-edges with a permutation oracle: all 543 acyclic graphs had
correct order/timing, and all 3,553 cyclic graphs were rejected. A reversed
5,000-task chain, input immutability, duration-conversion overflow, and arithmetic
overflow checks also passed. This small exhaustive oracle is test code only;
the production scheduler does not enumerate schedules.

The exact independent candidate command was:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B scratch/verification/run_candidate.py > scratch/verification/candidate-tests.log 2>&1
```

It exited 0 and reported 36 tests passed in 0.015 seconds. Construction used
`PYTHONDONTWRITEBYTECODE=1 python3 -B -` with the exact stdin script now retained
as `scratch/implementation/check_candidate.py`; its original output is
`scratch/implementation/checks.log`. Its file-form reproduction command is
`PYTHONDONTWRITEBYTECODE=1 python3 -B scratch/implementation/check_candidate.py`
(the construction worker did not rerun the file form).

Candidate harnesses and review notes are retained under these scratch paths.
These are candidate checks; root independently checked the installed final
files as recorded below.

## Final root validation

Root installed the reviewed proposal, then ran these local commands from the
workspace root with `login=false` and `PYTHONDONTWRITEBYTECODE=1`:

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest test_solution -v
```

Both exited 0. The supplied smoke suite passed 1 test in 0.000 seconds;
the final regression suite passed all 35 tests in 0.017 seconds. Full outputs
are retained in `scratch/root/final-smoke.log` and
`scratch/root/final-regressions.log`. The final implementation and regression
file byte-match the reviewed candidate. Hash checks confirm `TASK.md`,
`AGENTS.md`, `PROMPT.md`, and `tests/test_smoke.py` are unchanged.

## Complexity and limits

For V tasks and E supplied dependency entries (including duplicates), expected
time is O(E + V log V) and auxiliary storage is O(V + E), under normal
constant-time dictionary/set operations. ID hashing/comparison adds the usual
string-length cost. Distinct edges alone are retained in outgoing adjacency
lists. Python binary64 float rounding is intentional; no exact-decimal arithmetic
is promised. Standard builtin container/type behavior is assumed. External
skills, packages, services, repository history, and evaluator tests were not
consulted. No unresolved contract issue was found in review.
