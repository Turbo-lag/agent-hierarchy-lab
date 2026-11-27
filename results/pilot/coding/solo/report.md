# Dependency scheduler repair

`schedule(tasks)` now validates its input and returns earliest-start timings in
lexicographically smallest topological order. The API is unchanged, and all
implementation and test dependencies are in the Python standard library.

## Defects and fixes

- The starter sorted the caller's task list in place. The repair reads input
  objects and builds separate duration, dependency, and graph structures. Neither
  successful calls nor validation failures modify the input.
- Sorting all IDs once does not produce a dependency-respecting schedule. It also
  causes missing-result lookups when dependencies occur later. The repair first
  registers every task, then builds the graph and processes dependency-ready IDs
  through a minimum heap. Newly ready IDs compete immediately with existing ready
  IDs; task start times do not determine dictionary iteration order.
- The starter took the minimum dependency finish time. Each successor now
  accumulates the maximum finish time over its dependencies, and becomes ready
  only after every distinct dependency is processed. Independent tasks start at
  `0.0`, reflecting unlimited worker capacity.
- Missing validation allowed duplicate IDs to overwrite results, accepted invalid
  duration types, and leaked exceptions such as `KeyError` or `TypeError` for
  malformed records. The repair validates the outer list, task dictionaries,
  required keys, unique nonempty string IDs, duration types, dependency lists,
  and dependency ID types. Extra dictionary keys are ignored.
- Unknown dependencies and self-edges now raise `ValueError`. Deduplicated
  dependency sets ensure repeated edges count once. Unprocessed vertices after
  the iterative traversal detect directed cycles, including disconnected cycles.
- Durations are converted to float before arithmetic. Boolean durations,
  negative/nonfinite values, and integer-to-float conversion overflow raise
  `ValueError`. Computed nonfinite start/finish values also raise `ValueError`.
  Zero durations, finite very large values, and subnormal floats remain valid.

## Verification

All commands below ran locally from:

```text
.
```

The default `python3` resolved to `/usr/bin/python3` and failed before running
Python because the host lacks Xcode developer tools. Shell interpreter discovery
found an existing Homebrew interpreter; `/opt/homebrew/bin/python3 --version`
reported **Python 3.14.8**. No installation or network access was needed.

Final commands and observed results:

```sh
PATH=/opt/homebrew/bin:$PATH python3 -m unittest discover -s tests -v
# Ran 1 test in 0.000s; OK

PATH=/opt/homebrew/bin:$PATH python3 -m unittest -v test_solution
# Ran 18 tests in 0.021s; OK
```

Full final output is saved in scratch/smoke.log and
scratch/regression.log. These are measured local test
results, not performance benchmark claims or evaluator scores.

The regression suite covers malformed containers/records, invalid and duplicate
IDs, invalid durations, invalid dependencies, unknown IDs, self-edges, cycles,
disconnected components, finite and overflowing arithmetic, forward references,
maximal dependency finish times, newly ready heap ordering, duplicate edges,
zero durations, fractional arithmetic, integer rounding to binary64, Unicode ID
ordering, nested/shared input immutability, and independent output objects.
It checks every timing in a reverse-input **5,000-task chain**, plus output
ordering and final sink timing in a **1,000-leaf fan-out/fan-in graph**.

An independent small-input oracle repeatedly scans remaining tasks for satisfied
dependencies instead of using indegrees or a heap. It checks all 64 directed
three-vertex graphs without self-edges; every acyclic graph is tested in all six
input permutations, and cyclic graphs must fail. Another 150 seeded random DAGs
exercise shuffled IDs/input, duplicate dependencies, and varied durations.

The first regression run exposed a test-fixture error: the convenience helper
converted an intended `deps=None` to an empty list. The malformed-input case now
constructs its dictionary directly. No scheduler change was required for that
failure. Both suites were rerun successfully after the correction.

## Correctness and complexity

The indegree of an unprocessed task counts its distinct unprocessed dependencies.
Thus the heap contains exactly the dependency-ready tasks, and choosing its
minimum yields the required lexicographically smallest topological ordering.
Each processed dependency updates a successor's candidate start by maximum; when
that successor becomes ready, its start is the maximum finish over all of its
dependencies. Adding its converted duration yields the earliest possible finish.
An unfinished graph with no ready tasks contains a directed cycle.

Let V be the number of tasks and E the number of supplied dependency entries,
including repeats. Validation and graph construction take expected O(V + E)
time with Python hash tables. Each task enters/leaves the heap once, and each
unique edge is visited once, giving O(V + E + V log V) total time and O(V + E)
storage (under usual constant-cost ID comparison/hash assumptions). There is no
recursion, dense task matrix, or enumeration of schedules in the implementation.
The exhaustive checks exist only in the small regression tests.

## Assumptions and limits

Container/type checks use `isinstance`; ordinary subclasses of the specified
built-in types are accepted, except that bool is explicitly rejected as a
duration. Error message wording is not part of the contract. Timings are floats,
including zero, and arithmetic follows Python's binary64 behavior on this host.
Python 3.11 was not separately available for a runtime test; the implementation
uses syntax and standard-library APIs available in Python 3.11. External evaluator
tests were not accessed. Disabled external personal skills were not read, so
no claim is made that their separate review procedures were satisfied.
