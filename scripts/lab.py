#!/usr/bin/env python3
"""Prepare and evaluate manual Codex experiments. Never invokes a model."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.checks import CASES, research_structure


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def files_hash(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()
            and '__pycache__' not in p.parts and '.git' not in p.parts
            and p.suffix not in ('.pyc', '.pyo')}


def bundle_hash():
    hashes = {}
    for name in ('tasks', 'prompts', 'evaluation', 'experiments', 'scripts'):
        hashes[name] = files_hash(ROOT / name)
    for name in ('docs/PROTOCOL.md', 'AGENTS.md'):
        hashes[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def rows():
    with (ROOT / 'experiments/pilot.csv').open() as stream:
        return list(csv.DictReader(stream))


def prepare(run_id, destination=None):
    row = next((r for r in rows() if r['run_id'] == run_id), None)
    if row is None:
        raise ValueError('Unknown run ID; consult plan')
    if git('status', '--porcelain'):
        raise ValueError('Commit or resolve authoring changes before preparing runs')
    revision = git('rev-parse', 'HEAD')
    dest = Path(destination) if destination else ROOT / 'runs' / run_id
    if dest.exists():
        raise ValueError(f'Refusing to overwrite {dest}')
    kind, architecture = row['task'], row['architecture']
    workspace, operator = dest / 'workspace', dest / 'operator'
    dest.mkdir(parents=True)
    shutil.copytree(ROOT / 'tasks' / kind, workspace,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    operator.mkdir()
    prompt = (ROOT / 'prompts/common.md').read_text() + '\n' + (ROOT / 'prompts' / f'{architecture}.md').read_text()
    (workspace / 'PROMPT.md').write_text(prompt)
    (workspace / 'AGENTS.md').write_text(
        '# Measured-run workspace\n\nFollow PROMPT.md and TASK.md. The assigned '
        'architecture overrides optional personal delegation/review habits for '
        'this measured run. No extra agents. In solo mode do not delegate at all. '
        'Use only this workspace; do not inspect operator files, evaluation code, '
        'reference controls, or previous runs. Mandatory host policies prevail.\n')
    protected = {p: h for p, h in files_hash(workspace).items()
                 if p in ('TASK.md', 'PROMPT.md', 'AGENTS.md', 'sources.json')}
    write(operator / 'manifest.json', {
        **row, 'source_revision': revision, 'bundle_sha256': bundle_hash(),
        'config': read(ROOT / 'experiments/config.json'), 'protected_files': protected,
        'initial_workspace_sha256': files_hash(workspace), 'state': 'prepared_not_started'})
    write(operator / 'record.json', {
        'run_id': run_id, 'status': 'not_started', 'started_at_utc': None,
        'ended_at_utc': None, 'elapsed_seconds': None, 'stop_reason': None,
        'host': None, 'python_version': None, 'codex_version': None,
        'observed_root_model': None, 'observed_root_effort': None,
        'observed_agents': [], 'trace_evidence': None,
        'architecture_valid': None, 'environment_valid': None,
        'validity_explanation': None, 'memory_and_skills': None,
        'input_tokens': None, 'output_tokens': None, 'usage_scope': None,
        'interventions': [], 'deviations': [], 'raters': [],
        'rater_limitations': None})
    write(operator / 'manual-score.json', [
        {**item, 'score': None, 'evidence': None}
        for item in read(ROOT / 'evaluation/rubric.json')[kind]])
    (operator / 'README.md').write_text(
        '# Operator-only record\n\nNo run has started. Follow docs/PROTOCOL.md in '
        'the authoring repository. Record timing externally and retain actual '
        'visible agent events. Do not expose this folder to the measured chat. '
        'Use null for unavailable usage. Agent self-report alone cannot verify '
        'topology. Fill manual-score.json against the canonical rubric after '
        'external evaluation; do not edit the rubric maxima or manifest.\n')
    return dest


def evaluate_workspace(kind, workspace):
    workspace = Path(workspace).resolve()
    if kind == 'research':
        return {'automatic_score': 0, 'automatic_max': 0,
                'structure_issues': research_structure(workspace), 'cases': []}
    cases = []
    for case in CASES[kind]:
        name = case.__name__
        try:
            completed = subprocess.run(
                [sys.executable, '-I', '-B', str(ROOT / 'evaluation/checks.py'), kind,
                 str(workspace), name], cwd=workspace, capture_output=True,
                text=True, timeout=10)
            marker = f'CASE_COMPLETED:{name}'
            passed = (completed.returncode == 0 and
                      completed.stdout.splitlines()[-1:] == [marker])
            diagnostic = (completed.stdout + completed.stderr)[-6000:]
            if completed.returncode == 0 and not passed:
                diagnostic += '\nNo case-completion marker; checks did not finish'
        except subprocess.TimeoutExpired:
            passed, diagnostic = False, 'Exceeded 10-second case timeout'
        cases.append({'case': name, 'points': 10 if passed else 0,
                      'max': 10, 'passed': passed, 'diagnostic': diagnostic})
    return {'automatic_score': sum(c['points'] for c in cases),
            'automatic_max': 80, 'cases': cases}


def check_manifest(run):
    manifest = read(run / 'operator/manifest.json')
    if manifest['bundle_sha256'] != bundle_hash():
        raise ValueError('Experiment bundle changed; evaluate using the original revision')
    current = files_hash(run / 'workspace')
    changed = [name for name, digest in manifest['protected_files'].items()
               if current.get(name) != digest]
    return manifest, changed


def evaluate(run):
    run = Path(run).resolve()
    manifest, changed = check_manifest(run)
    before = files_hash(run / 'workspace')
    result = evaluate_workspace(manifest['task'], run / 'workspace')
    after = files_hash(run / 'workspace')
    result.update(run_id=manifest['run_id'], protected_file_changes=changed,
                  artifact_sha256=after, artifacts_changed_during_evaluation=before != after)
    write(run / 'operator/automatic-score.json', result)
    return result


def summarize(run):
    run = Path(run).resolve()
    manifest, protected_changes = check_manifest(run)
    auto = read(run / 'operator/automatic-score.json')
    record = read(run / 'operator/record.json')
    manual = read(run / 'operator/manual-score.json')
    canonical = read(ROOT / 'evaluation/rubric.json')[manifest['task']]
    expected_cases = CASES.get(manifest['task'], [])
    expected_max = 10 * len(expected_cases)
    actual_cases = auto.get('cases')
    if (auto.get('run_id') != manifest['run_id'] or
            type(auto.get('automatic_max')) is not int or auto['automatic_max'] != expected_max or
            not isinstance(actual_cases, list) or len(actual_cases) != len(expected_cases)):
        raise ValueError('Automatic score record does not match the run/canonical cases')
    for case, expected in zip(actual_cases, expected_cases):
        if (not isinstance(case, dict) or case.get('case') != expected.__name__ or
                type(case.get('passed')) is not bool or type(case.get('max')) is not int or
                case['max'] != 10 or type(case.get('points')) is not int or
                case['points'] != (10 if case['passed'] else 0)):
            raise ValueError('Automatic case score is inconsistent with canonical scoring')
    if (type(auto.get('automatic_score')) is not int or
            auto['automatic_score'] != sum(c['points'] for c in actual_cases) or
            type(auto.get('artifacts_changed_during_evaluation')) is not bool):
        raise ValueError('Automatic score aggregate or evaluation state is invalid')
    if auto['artifact_sha256'] != files_hash(run / 'workspace'):
        raise ValueError('Artifacts changed after evaluation; evaluate again')
    if not isinstance(manual, list) or [x.get('id') for x in manual] != [x['id'] for x in canonical]:
        raise ValueError('Manual rubric IDs/order differ from canonical rubric')
    score = 0
    for entry, rule in zip(manual, canonical):
        value = entry.get('score')
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= rule['max']:
            raise ValueError(f'Missing/invalid manual score for {rule["id"]}')
        if not isinstance(entry.get('evidence'), str) or not entry['evidence'].strip():
            raise ValueError(f'Missing manual evidence for {rule["id"]}')
        if entry.get('max') != rule['max'] or entry.get('criterion') != rule['criterion']:
            raise ValueError('Do not modify the canonical rubric')
        score += value
    if record.get('run_id') != manifest['run_id'] or record.get('status') not in ('completed', 'timed_out', 'failed'):
        raise ValueError('Run record is not a completed, timed-out, or failed attempt')
    if any(type(record.get(k)) is not bool for k in ('architecture_valid', 'environment_valid')):
        raise ValueError('Explicit architecture/environment validity decisions required')
    for key in ('started_at_utc', 'ended_at_utc', 'stop_reason', 'validity_explanation', 'trace_evidence'):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f'Missing record field: {key}')
    if not record.get('raters'):
        raise ValueError('Record evaluator identity')
    elapsed = record.get('elapsed_seconds')
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError('Invalid elapsed time')
    if record['environment_valid']:
        if record.get('observed_root_model') != manifest['config']['model'] or record.get('observed_root_effort') != manifest['config']['reasoning_effort']:
            raise ValueError('A valid environment needs verified matching root model and effort')
    time_budget_exceeded = elapsed > manifest['config']['wall_clock_limit_minutes'] * 60
    eligible = (record['architecture_valid'] and record['environment_valid']
                and not protected_changes and not auto['artifacts_changed_during_evaluation']
                and not time_budget_exceeded)
    result = {'run_id': manifest['run_id'], 'task': manifest['task'],
              'architecture': manifest['architecture'], 'raw_task_score': score + auto['automatic_score'],
              'primary_comparison_eligible': eligible, 'elapsed_seconds': elapsed,
              'time_budget_exceeded': time_budget_exceeded,
              'protected_file_changes': protected_changes,
              'source_revision': manifest['source_revision'], 'bundle_sha256': manifest['bundle_sha256']}
    write(run / 'operator/summary.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('plan')
    prep = commands.add_parser('prepare')
    choice = prep.add_mutually_exclusive_group(required=True)
    choice.add_argument('--run-id')
    choice.add_argument('--all-pilot', action='store_true')
    for name in ('evaluate', 'summarize'):
        commands.add_parser(name).add_argument('--run-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'plan':
            print((ROOT / 'experiments/pilot.csv').read_text(), end='')
        elif args.command == 'prepare':
            ids = [r['run_id'] for r in rows() if r['phase'] == 'pilot'] if args.all_pilot else [args.run_id]
            for run_id in ids:
                print(prepare(run_id))
        else:
            fn = evaluate if args.command == 'evaluate' else summarize
            print(json.dumps(fn(args.run_dir), indent=2, allow_nan=False))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
