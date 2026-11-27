# Dependency scheduler repair

The repaired implementation provides the required behavior for `schedule(tasks)` while preserving its API. It validates the input before traversal, normalizes durations to binary64 floats, and schedules tasks with an iterative dependency-graph algorithm. Input objects are never modified.

## Defects and fixes

The starter sorted the caller's task list in place and assumed lexical ID order was dependency order. This mutated input and failed on valid forward references. It also used the minimum prerequisite finish, which started tasks before all dependencies completed. Duplicate IDs could overwrite results, invalid references leaked `KeyError`, and malformed data, cycles, nonfinite values, and overflow were not handled as specified.

The replacement first validates the list, task dictionaries, required fields, unique nonempty string IDs, numeric durations, and dependency lists. It accepts additional fields without examining or copying them. Durations exclude booleans and are converted to floats before arithmetic; nonfinite, negative, and conversion-overflow values raise `ValueError`. Dependencies are copied into sets, so repeated entries represent one edge. A second pass validates references and self-edges after all IDs are known.

Kahn's topological traversal uses a min-heap of currently ready IDs. Each newly ready task immediately joins the heap, giving the lexicographically smallest topological dictionary order independently of start time. Task starts are the maximum prerequisite finish, or `0.0` without prerequisites. Nonfinite computed times raise `ValueError`. A remaining unprocessed task indicates a cycle, including cycles in disconnected components. Traversal uses no recursion.

## Regression evidence

The authored `test_solution.py` contains 27 test methods, covering malformed containers and fields, invalid and overflowing durations, unknown and repeated dependencies, self-edges and disconnected cycles, forward references, fan-in and diamonds, lexical priority, independent start-time order, float normalization, zero durations, extra fields, and immutability on both successful and failed calls. A reverse-input chain of 2,500 tasks checks recursion safety and every expected time. An independent small-graph oracle checks all 64 edge subsets of a four-node construction in two input orders, enumerating valid permutations only in the test and calculating timing through prerequisite paths.

Author checks ran locally from `scratch/author/` using the installed Python 3.14.8 interpreter:

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 -m unittest -v test_solution
```

Result: exit 0; **27 tests passed in 0.008s**.

The supplied smoke test also ran against the candidate through `unittest` discovery of `../../tests`, after asserting that `scheduler.__file__` resolved to `scratch/author/scheduler.py`. Result: exit 0; **1 test passed in 0.000s**. The full command and output summary are in `scratch/author/commands.md`.

The reviewer found no supported defects and recommended integration unchanged. Five independent reviewer tests passed, covering all 4,096 four-vertex directed graphs without self-edges, 150 deterministic randomized DAGs, a 10,000-task chain and 10,000-root join, numeric boundaries, and input aliasing. The reviewer also reran all 27 authored regressions and the smoke test successfully. Exact evidence is in `scratch/reviewer/findings.md`, `commands.md`, and the adjacent logs.

The coordinator integrated the reviewed scheduler and regression suite unchanged, then ran these commands locally from the workspace root:

```sh
export PATH="$PWD/scratch/coordinator/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
python3 -m unittest discover -s tests -v
python3 -m unittest -v test_solution
```

Final results: smoke **1 test passed in 0.000s**, regressions **27 tests passed in 0.010s**, both exit 0. Output logs are `scratch/coordinator/smoke.log` and `scratch/coordinator/regressions.log`. The local launcher resolves `python3` to `/opt/homebrew/bin/python3.14` because the host's default `/usr/bin/python3` fails without Apple developer tools.

`PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.14 scratch/coordinator/check_integration.py` also passed (exit 0). It verifies the root import path, byte-for-byte identity of the integrated implementation/tests with the reviewed candidate, and unchanged SHA-256 fingerprints for `AGENTS.md`, `PROMPT.md`, `TASK.md`, and `tests/test_smoke.py`. Its output is `scratch/coordinator/integration.log`.

All checks above are actual local execution results on supplied or synthetic regression inputs. They do not claim exhaustive correctness or an evaluator score.

## Complexity and assumptions

Let V be the number of tasks and E the number of supplied dependency entries, including duplicates. Validation and graph work take expected O(V + E) dictionary/set operations, and the heap takes O(V log V) operations. Total expected time is O(V + E + V log V), within the requested bound; storage is O(V + E). There is no dense matrix and production does not enumerate schedules. These conventional graph bounds treat string hashing/comparisons as key operations.

Container and numeric types use ordinary `isinstance` semantics: lists and dictionaries may be subclasses, durations may be int/float subclasses, and bool is explicitly excluded. Error message wording is not part of the API. Negative zero is valid. External personal skill files were intentionally unavailable under the measured-run workspace boundary, so no external skill checks are claimed.
