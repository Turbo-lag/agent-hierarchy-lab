# Agent Hierarchy Lab

This repository prepares and evaluates experiments run manually in fresh local
Codex chats with GPT-6 Astra. Do not start pilot runs unless explicitly asked.
No API credentials, API calls, or model execution are required by the tooling.

Repository maintenance: use Python 3.11+ standard library only. Run
`python3 -m unittest discover -s tests -v` after substantive tooling changes.
Do not repair the intentionally defective coding starter or fill the science
starter: they are benchmark inputs. Evaluator controls live under `evaluation/`.

For measured runs, the generated workspace's AGENTS.md and PROMPT.md specify
the architecture. They explicitly override optional personal delegation/review
habits for that run. Mandatory host policies remain in force. Evaluations take
place outside the measured run. Never turn an unexecuted check into a pass.

Keep previous results immutable. Version changes to tasks, prompts, and scoring;
do not pool runs across versions. Do not publish raw chats or personal machine
metadata without reviewing them for unrelated/private content.
