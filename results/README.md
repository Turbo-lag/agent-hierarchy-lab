# Isolated pilot results

This release contains all 15 observations from v0.1.1-isolation. Follow an architecture link to inspect its submitted report, artifacts and criterion-level assessment. The score is the final artifact grade out of 100. Elapsed time and token counts include the measured agents only.

[Interactive results](https://turbo-lag.github.io/agent-hierarchy-lab/) · [CSV](../docs/data/pilot.csv) · [JSON](../docs/data/pilot.json) · [Method and rubric](../docs/PILOT.md)

| Task | Architecture | Score /100 | Seconds | Input tokens | Cached input | Output tokens | Eligible |
|---|---|---:|---:|---:|---:|---:|---|
| Research | [Solo](pilot/research/solo/) | 97.92 | 177.4 | 106,328 | 99,584 | 9,460 | Yes |
| Research | [Manager–workers](pilot/research/manager/) | 100 | 186.7 | 1,341,865 | 1,250,816 | 22,252 | Yes |
| Research | [Sequential pipeline](pilot/research/pipeline/) | 100 | 383.6 | 707,921 | 605,952 | 20,619 | Yes |
| Research | [Independent candidates](pilot/research/candidates/) | 100 | 273.1 | 884,078 | 806,528 | 29,283 | Yes |
| Research | [Two-level hierarchy](pilot/research/hierarchy/) | 100 | 383.3 | 1,963,152 | 1,815,040 | 29,522 | Yes |
| Science | [Solo](pilot/science/solo/) | 100 | 229.5 | 174,283 | 157,056 | 11,800 | Yes |
| Science | [Manager–workers](pilot/science/manager/) | 100 | 198.2 | 1,295,497 | 1,220,352 | 22,696 | Yes |
| Science | [Sequential pipeline](pilot/science/pipeline/) | 100 | 472.1 | 1,002,220 | 939,520 | 23,409 | Yes |
| Science | [Independent candidates](pilot/science/candidates/) | 100 | 361.7 | 1,490,736 | 1,344,896 | 41,874 | No † |
| Science | [Two-level hierarchy](pilot/science/hierarchy/) | 100 | 301.4 | 1,832,227 | 1,704,192 | 30,055 | Yes |
| Coding | [Solo](pilot/coding/solo/) | 100 | 196.7 | 164,705 | 136,192 | 8,692 | Yes |
| Coding | [Manager–workers](pilot/coding/manager/) | 100 | 252.1 | 1,334,491 | 1,248,640 | 24,398 | Yes |
| Coding | [Sequential pipeline](pilot/coding/pipeline/) | 100 | 479.2 | 970,732 | 913,152 | 22,592 | Yes |
| Coding | [Independent candidates](pilot/coding/candidates/) | 100 | 336.6 | 1,199,233 | 1,152,896 | 35,974 | Yes |
| Coding | [Two-level hierarchy](pilot/coding/hierarchy/) | 100 | 328.4 | 1,782,368 | 1,681,280 | 29,446 | Yes |

† The science candidates submission earned full numerical credit. A worker wrote a shared file outside its assigned scratch directory, which made the observation ineligible for the primary quality comparison. The workspace boundary held. All 15 observations are retained in the table.

## Files and field definitions

The CSV gives one row per isolated observation. The JSON includes the same rows, the frozen source revision and bundle digest, and two earlier v0.1.0 research attempts under `historical_excluded`. Their [submitted reports and scorecards](historical/) are archived separately. Those attempts are outside the isolated cohort. The preserved run IDs identify each source observation.

- `automatic`, `automatic_max`, `manual` and `score` are points on the task rubric. Research allocates all points to manual criteria. Each task has a maximum of 100. Scores have meaning within their task.
- `status` records completion. `architecture_valid` covers the required delegation structure and worker roles, `environment_valid` covers workspace restrictions, and `eligible` records the primary-comparison decision.
- `elapsed_seconds` measures wall time. `sessions` counts distinct participating agent sessions. `usage_complete` indicates final counters were available. Cached input is part of input and reasoning output is part of output. Total tokens are input plus output.
- Each `assessment.json` gives the manual criterion scores and original ratings (out of 100 for research or 20 for coding/science), the executable case results where applicable, and SHA-256 digests of the original frozen and published files.

The public submissions include research reports and claim ledgers, coding repairs and tests, and numerical solvers, tests, verification programs and measured convergence data. Publication copies of reports replace personal workspace paths with `.` and render links to private execution or scratch logs as text. The digests identify those editorial changes. Operator records, raw conversations and machine identifiers stay local.

To recheck a coding or science submission, copy its directory to a working location and run `python3 -B -m unittest -v test_solution` and `python3 -B -m unittest discover -s tests -v` there. The scientific verification programs can regenerate the convergence data. The task prompts, fixed evaluator and original run procedures are available from the [project overview](../README.md).
