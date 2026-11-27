# Dependency scheduler repair

`scheduler.schedule(tasks)` now produces earliest-start schedules with the
lexicographically smallest dependency-ready insertion order, without mutating
the input. Its public API is unchanged; only Python standard-library modules
are used.

## Defects and repairs

| Starter defect | Repair |
| --- | --- |
| Sorts the caller's task list in place | Builds independent dictionaries, dependency sets, and adjacency lists |
| Treats sorted IDs as a valid dependency order; forward references can fail | Collects every ID before resolving references; traverses dependency-ready tasks |
| Uses the minimum dependency finish | Propagates the maximum predecessor finish to each successor |
| Cannot maintain the smallest currently ready ID | Uses a min-heap, including newly unlocked tasks immediately |
| Does not validate the full input or consistently raise `ValueError` | Validates containers, required fields, unique nonempty string IDs, duration types/range, and dependency IDs/references |
| Does not implement cycle rejection | Rejects self-edges directly and detects incomplete topological traversal |
| Uses supplied numeric types and permits nonfinite results | Converts durations to float, catches conversion overflow, and checks finite input/output times |

Repeated dependencies are deduplicated before counting graph edges. Scheduling
is iterative, so chain depth does not consume the Python call stack. All
independent tasks start at `0.0`; there is no resource-capacity restriction.
For example, with ready tasks `b` (duration 10) and `z` (duration 0), and `a`
depending on `b`, output order is `b, a, z`, even though `a` starts at 10 and
`z` starts at 0.

Validation follows the stated contract: additional keys are ignored, whitespace
and Unicode IDs are accepted when nonempty, negative zero is valid, and ordinary
Python string ordering determines lexical order. Failed calls also preserve
their inputs. Floating-point rounding is intentional, including conversion
before addition near `2**53`.

## Actual verification

All commands ran locally from
`.`.
The initial default `python3` command was a nonfunctional macOS developer-tools
stub. Shell command resolution found an installed Python 3.14.8 at
`/opt/homebrew/bin/python3`; command-local PATH selection used it without an
installation or external dependency.

Final commands (each exited 0):

```sh
PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_solution
PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 scratch/verification/verify_scheduler.py scheduler.py
```

| Check | Observed result | Evidence |
| --- | --- | --- |
| Supplied smoke suite | 1 test passed | smoke.log |
| Independent regression suite | 20 test methods passed | regression.log |
| Independent graph oracle | 4,670 cases passed: 976 valid, 3,694 rejected | oracle.log |

The regression suite covers malformed containers and fields, invalid numeric
values, conversion and computed overflow, forward/repeated dependencies,
cycles and disconnected components, lexical readiness independent of timing,
valid/invalid input immutability, float rounding/extremes, and all timestamps in
a reverse-input 2,501-task chain.

The oracle checks all 4,166 directed
loop-free labeled graphs on zero through four vertices, 500 seeded graph cases
up to six vertices, and four targeted numeric/order cases. It independently
finds the smallest valid topological permutation and evaluates dependency times
with a bounded recursive reference. Its deliberately expensive enumeration is
test machinery only; production scheduling never enumerates schedules.

Before integration, the supplied smoke test passed the defective starter.
The regression worker instead observed 20 failure subcases and 49 error
subcases across its 20 test methods; the oracle independently detected starter
input mutation on a two-vertex graph. See
baseline regression evidence and
verification notes. Root reviewed the proposals,
checked the corrected malformed-dependency test helper, and reran all three
checks against the final root-level implementation.

These are executed correctness checks, not performance measurements or proof
over all possible inputs. Runtime checks used Python 3.14.8, not every supported
Python release. The code uses features available in Python 3.11+. No external
evaluation inputs or personal skills were accessed.

## Complexity

Let V be the number of tasks, E the supplied dependency-entry count (including
duplicates), and U the number of distinct edges. Validation/deduplication and
graph construction take expected O(V + E) time with Python hash tables. Each
vertex enters/leaves the heap once, and each distinct edge is propagated once.
Total expected time is O(V + E + V log V), within the required bound, and
auxiliary storage is O(V + U), hence O(V + E). This assumes ordinary hash/ID
comparison costs; reading arbitrarily long IDs also has its inherent cost.
No dense matrix is allocated.

The execution log records organization, handoffs, model-setting
evidence, environmental limitations, and final artifact paths.
