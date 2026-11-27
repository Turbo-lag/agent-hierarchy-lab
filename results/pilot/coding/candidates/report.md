# Dependency scheduler repair

`schedule(tasks)` now returns finite, floating-point earliest-start times in the
lexicographically smallest topological order without mutating input. The API is
unchanged. Final verification passed 28 regression tests, 8 independent selector
checks, and the supplied smoke test under Python 3.14.8.

## Defects and fixes

The starter sorted the caller's task list in place and treated alphabetical ID
order as a dependency order. This mutated input and failed on forward references.
It also used the minimum predecessor finish, allowing a task to start before all
its dependencies finished. Validation was incomplete, duplicate IDs could
silently overwrite results, durations were not converted to float, and cycles
and nonfinite arithmetic were not handled correctly.

The repair validates the outer list, task dictionaries, required fields, unique
nonempty string IDs, duration types, and dependency lists/IDs. Additional fields
are ignored. Boolean durations, negative/nonfinite values, conversion failures,
unknown dependencies, and self-edges raise `ValueError`. Durations are converted
to float before arithmetic. Repeated dependencies are copied into sets so they
represent one edge. References are resolved after all IDs are collected.

An iterative Kahn traversal maintains a min-heap of all dependency-ready tasks.
Removing the smallest ID at each step gives the required dictionary insertion
order, including when a newly ready ID precedes an existing ready ID. Every
completed predecessor contributes its finish time to the maximum start time
of its children. A child enters the heap only after all its distinct dependencies
have been processed. Independent tasks start at `0.0`; capacity is unlimited.
Every computed start and finish is checked for finiteness. An incomplete traversal
signals a cycle, including a cycle in a disconnected component. Separate graph
state preserves caller-owned lists, dictionaries, dependency lists, and extra
fields on success and rejection. No recursion is used.

## Selection and integration

Three independent candidates were completed before comparison. The root inspected
their actual implementations and test coverage, reran each regression suite,
and ran the same eight independent checks against all three. All passed.
Candidate 3 was selected as the base because its delivered suite includes an
independent permutation oracle for every four-vertex simple directed graph,
a 3,000-task chain, and 1,000-way fan-out/fan-in. This was a coverage-based choice
among implementations passing the shared checks, not a claim of measured runtime
superiority.

An additional concrete probe found that candidates 2 and 3 leaked `TypeError`
when an `int` subclass's float conversion failed; candidate 1 already normalized
it. The root repaired candidate 3's conversion exception handler and added a
regression for valid and unconvertible `int`/`float` subclasses. These are the
only implementation/test changes from the selected base. Full selection and
handoff evidence appears in execution.md.

## Actual verification

All final commands ran locally in:
`.`.

| Command | Observed result | Retained output |
| --- | --- | --- |
| `python3.14 -B -m unittest -v test_solution` | 28 tests passed, 0.047 s | `scratch/selector/final_regressions.txt` |
| `python3.14 -B scratch/selector/check_candidates.py scheduler.py` | 8 checks passed, 0.084 s | `scratch/selector/final_selector_checks.txt` |
| `python3 -m unittest discover -s tests -v` with the function below | 1 test passed, 0.000 s | `scratch/selector/final_smoke.txt` |

The default `/usr/bin/python3` failed with an unavailable Xcode developer-tools
error. The installed `python3.14` is Python 3.14.8. The required smoke command was
run with a process-local shell function forwarding to that available runtime:

```sh
python3() { python3.14 "$@"; }
python3 -m unittest discover -s tests -v
```

No interpreter was installed or system setting changed. To reproduce on a host
with a working Python 3.11+ named `python3`, run the smoke command directly and
`python3 -m unittest -v test_solution`.

The delivered regressions cover malformed inputs, missing keys, duplicate IDs,
unknown/self dependencies, cycles, repeated edges, forward references, dynamic
lexical ordering, joins, independent components, immutability, ignored extra
fields, zero/fractional durations, binary64 rounding, subnormal and maximum finite
values, conversion and addition overflow, and long/wide graphs. Its permutation
oracle independently identifies the first valid order among 24 permutations for
all 4,096 four-vertex simple directed graphs: 543 DAGs and 3,553 cyclic graphs.

The root's independent checks additionally exercise all 4,096 graphs with repeated
dependency entries, 100 seeded random 60-task DAGs against a repeated-scan oracle,
a 5,000-task chain, and 5,000 simultaneously ready tasks. All inputs are synthetic
regression cases; no empirical performance benchmark is claimed. Three selected
root checks failed on the original starter (one assertion failure, two errors),
while its supplied smoke test passed. Hidden evaluator tests were not accessed.

## Complexity and assumptions

Let V be the number of tasks and E the number of supplied dependency entries,
including repetitions. Validation and graph construction take expected O(V + E)
time with dictionaries/sets. Every task enters and leaves the heap once, and
every distinct edge is traversed a constant number of times. Total expected time
is O(V + E + V log V), within the required bound; storage is O(V + E). These
bounds use the usual unit-cost assumptions for ID comparisons and hash operations.
The implementation neither enumerates schedules nor allocates a dense matrix.
The small exhaustive enumeration exists only in tests.

Python `float` supplies the requested binary64 arithmetic on the tested host.
Negative zero is accepted as nonnegative. Standard numeric subclasses are
accepted when conversion succeeds, while booleans remain excluded. No Python
versions other than 3.14.8 were executed. External personal skills were disabled
by the experiment and their checks are not claimed.
