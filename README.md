# Agent Hierarchy Lab

When does a team of AI agents produce a better answer than one agent working alone? This project tests that question by giving different agent organizations the same problem, model, tools and scoring rules.

**[Explore the pilot on GitHub Pages](https://turbo-lag.github.io/agent-hierarchy-lab/)** · [Browse submissions and scores](results/) · [Download the data](docs/data/pilot.csv)

## The 15 isolated runs

Five workflows using GPT-6 Astra (High) completed one coding repair, one scientific computing task and one research synthesis each. Fourteen submissions reached the scoring ceiling. The clearest differences in this pilot were elapsed time, token use and one violation of the worker assignment rules.

| Architecture | Research /100 | Science /100 | Coding /100 | Eligible runs | Total elapsed¹ |
|---|---:|---:|---:|---:|---:|
| Solo | 97.92 | 100 | 100 | 3/3 | 603.6 s |
| Manager–workers | 100 | 100 | 100 | 3/3 | 637.0 s |
| Sequential pipeline | 100 | 100 | 100 | 3/3 | 1,334.9 s |
| Independent candidates | 100 | 100 † | 100 | 2/3 | 971.4 s |
| Two-level hierarchy | 100 | 100 | 100 | 3/3 | 1,013.1 s |

¹ Sum of the three measured runs, including ineligible attempts. † A science worker created a shared Python cache inside the workspace but outside its assigned directory. The submission earned 100 for its artifact and was excluded from the primary quality comparison. Solo research lost 2.08 points because one claim lacked sufficient support in the supplied sources.

Solo used the fewest input and output tokens on each task. It completed the coding repair in 196.7 seconds, with the same score as the sequential pipeline at 479.2 seconds. Manager–workers was the fastest eligible full-score workflow on research and science. Each cell represents one observation.

## How the experiment works

- **Assign a workflow.** The [five architecture prompts](prompts/) specify who plans, implements, verifies and integrates. All runs used a fresh isolated workspace and a common 30-minute ceiling.
- **Freeze one submission.** The operator stopped the clock at CLI exit, preserved the artifacts and checked session records for actual delegation and workspace compliance.
- **Grade outside the run.** Coding and science allocate 80 points to executable checks and 20 to review. Research uses a 100-point source-grounded rubric. Two AI raters assessed manual criteria. The results include raw score, eligibility, elapsed seconds and token usage for every run. [Measured pilot method](docs/PILOT.md) · [Rubric](evaluation/RUBRIC.md)

## Explore the evidence

| Task | What the agent had to deliver | Pilot artifacts |
|---|---|---|
| [Coding](tasks/coding/TASK.md) | Repair a dependency scheduler and test ordering, arithmetic and input preservation | [Five repairs and test suites](results/pilot/coding/) |
| [Scientific computing](tasks/science/TASK.md) | Implement a variable-coefficient elliptic solver and check convergence against two exact solutions | [Five solvers and verification datasets](results/pilot/science/) |
| [Research](tasks/research/TASK.md) | Recommend iterative solvers for three scenarios using a fixed six-source digest | [Five reports and claim ledgers](results/pilot/research/) |

## Research direction

Our hypothesis is that larger inference budgets will make hierarchy more useful on difficult problems whose parts can be solved independently and then integrated. The pilot compared whole workflows under equal time ceilings. Token budgets differed and scores clustered at the maximum. The proposed next study varies difficulty, decomposability and team-wide inference budget on held-out problems. [Study design and limits](docs/PILOT.md#the-next-experiment)

## Run the benchmark kit

From a clean checkout with Python 3.11+ and Git, run:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/lab.py plan
python3 scripts/lab.py prepare --run-id coding-solo-r1
```

Preparation creates a workspace and operator files. To inspect the exact measured inputs, use [the frozen source revision](https://github.com/Turbo-lag/agent-hierarchy-lab/tree/380526b8c613be6ed46e23e2af24d47f25c04f2c). The [original operator procedure](docs/PROTOCOL.md) and [pilot method](docs/PILOT.md) describe setup, execution and evaluation. The public dataset and submissions can be explored without running a model.
