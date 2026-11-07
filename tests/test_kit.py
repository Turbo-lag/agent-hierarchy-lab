import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from evaluation import checks, controls
from scripts import lab


class GraderTests(unittest.TestCase):
    def test_positive_controls(self):
        for kind, cases in checks.CASES.items():
            for case in cases:
                with self.subTest(kind=kind, case=case.__name__):
                    case(controls)

    def test_starter_fails_interacting_bugs(self):
        starter = checks.load(lab.ROOT / 'tasks/coding/scheduler.py')
        for case in (checks.coding_basic, checks.coding_order, checks.coding_immutable,
                     checks.coding_validation, checks.coding_dependencies):
            with self.subTest(case=case.__name__):
                with self.assertRaises(Exception):
                    case(starter)

    def test_minimum_instead_of_maximum_is_detected(self):
        text = (lab.ROOT / 'evaluation/controls.py').read_text()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'mutant.py'
            path.write_text(text.replace('start = max(', 'start = min('))
            with self.assertRaises(AssertionError):
                checks.coding_basic(checks.load(path))

    def test_boundary_and_source_sign_corruptions_are_detected(self):
        text = (lab.ROOT / 'evaluation/controls.py').read_text()
        for original, replacement, case in [
            ('rhs[0] += face[0]*left', 'rhs[0] -= face[0]*left', checks.science_affine),
            ('real(f((i+1)/n))/(n*n)', '-real(f((i+1)/n))/(n*n)', checks.science_polynomial),
        ]:
            with self.subTest(original=original), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'mutant.py'
                path.write_text(text.replace(original, replacement))
                with self.assertRaises(AssertionError):
                    case(checks.load(path))

    def test_unimplemented_science_fails(self):
        with self.assertRaises(NotImplementedError):
            checks.science_affine(checks.load(lab.ROOT / 'tasks/science/solver.py'))

    def test_numerical_oracle_independent_discrete_sine(self):
        # Exact eigenvector response of the discrete constant-coefficient operator.
        n = 20
        x, u = controls.solve(n, lambda x: 1., lambda x: math.pi**2*math.sin(math.pi*x))
        amplitude = math.pi**2 / (4*n*n*math.sin(math.pi/(2*n))**2)
        self.assertLess(max(abs(v-amplitude*math.sin(math.pi*t)) for t, v in zip(x, u)), 1e-12)

    def test_external_process_grading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy(lab.ROOT / 'evaluation/controls.py', root / 'scheduler.py')
            result = lab.evaluate_workspace('coding', root)
            self.assertEqual(result['automatic_score'], 80)
            (root / 'scheduler.py').write_text('raise RuntimeError("control import failure")\n')
            failed = lab.evaluate_workspace('coding', root)
            self.assertEqual(failed['automatic_score'], 0)
            self.assertTrue(all('control import failure' in c['diagnostic'] for c in failed['cases']))

    def test_research_schema_not_factual_grading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(len(checks.research_structure(root)), 2)
            (root / 'report.md').write_text('word ' * 1000)
            claims = [{'id': f'C{i}', 'claim': 'synthetic test claim', 'source_ids': ['S1'],
                       'support': 'direct', 'rationale': 'synthetic', 'limitation': 'synthetic'} for i in range(8)]
            lab.write(root / 'claims.json', claims)
            self.assertEqual(checks.research_structure(root), [])
            self.assertEqual(lab.evaluate_workspace('research', root)['automatic_max'], 0)
            claims[0]['source_ids'] = ['S99']
            lab.write(root / 'claims.json', claims)
            self.assertTrue(checks.research_structure(root))

    def test_multifile_submission_and_optimization_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy(lab.ROOT / 'evaluation/controls.py', root / 'helper.py')
            (root / 'scheduler.py').write_text('from helper import schedule\n')
            self.assertEqual(lab.evaluate_workspace('coding', root)['automatic_score'], 80)
            (root / 'scheduler.py').write_text('def schedule(tasks):\n    return {}\n')
            with mock.patch.dict(os.environ, {'PYTHONOPTIMIZE': '1'}):
                result = lab.evaluate_workspace('coding', root)
            self.assertLess(result['automatic_score'], 80)

    def test_premature_exit_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scheduler.py').write_text('raise SystemExit(0)\n')
            result = lab.evaluate_workspace('coding', root)
            self.assertEqual(result['automatic_score'], 0)
            self.assertTrue(all('No case-completion marker' in c['diagnostic'] for c in result['cases']))

    def test_dataclass_submission_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy(lab.ROOT / 'evaluation/controls.py', root / 'helper.py')
            (root / 'scheduler.py').write_text(
                'from __future__ import annotations\nfrom dataclasses import dataclass\n'
                '@dataclass\nclass Task:\n    name: str\nfrom helper import schedule\n')
            self.assertEqual(lab.evaluate_workspace('coding', root)['automatic_score'], 80)


class WorkflowTests(unittest.TestCase):
    def prepare_fixture(self, directory):
        with mock.patch.object(lab, 'git', side_effect=['', 'test-revision']):
            return lab.prepare('coding-solo-r1', Path(directory) / 'run')

    def test_schedule_complete(self):
        rows = lab.rows()
        self.assertEqual(len(rows), 45)
        self.assertEqual(len({r['run_id'] for r in rows}), 45)
        self.assertEqual(sum(r['phase'] == 'pilot' for r in rows), 15)
        for kind in ('coding', 'science', 'research'):
            for arch in ('solo', 'pipeline', 'manager', 'candidates', 'hierarchy'):
                self.assertEqual(sum(r['task'] == kind and r['architecture'] == arch for r in rows), 3)

    def test_prepare_isolated_and_not_started(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self.prepare_fixture(directory)
            self.assertFalse((run / 'workspace/evaluation').exists())
            self.assertFalse((run / 'workspace/controls.py').exists())
            self.assertEqual(lab.read(run / 'operator/record.json')['status'], 'not_started')
            self.assertIn('Do not spawn', (run / 'workspace/PROMPT.md').read_text())
            with mock.patch.object(lab, 'git', side_effect=['', 'test-revision']):
                with self.assertRaisesRegex(ValueError, 'overwrite'):
                    lab.prepare('coding-solo-r1', run)

    def test_dirty_authoring_tree_rejected(self):
        with mock.patch.object(lab, 'git', return_value=' M some-file'):
            with self.assertRaisesRegex(ValueError, 'Commit'):
                lab.prepare('coding-solo-r1')

    def test_missing_scores_and_modified_artifacts_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self.prepare_fixture(directory)
            lab.evaluate(run)
            with self.assertRaisesRegex(ValueError, 'manual score'):
                lab.summarize(run)
            (run / 'workspace/scheduler.py').write_text('changed\n')
            with self.assertRaisesRegex(ValueError, 'Artifacts changed'):
                lab.summarize(run)

    def test_completed_summary_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self.prepare_fixture(directory)
            shutil.copy(lab.ROOT / 'evaluation/controls.py', run / 'workspace/scheduler.py')
            lab.evaluate(run)
            manual = lab.read(run / 'operator/manual-score.json')
            for entry in manual:
                entry.update(score=entry['max'], evidence='synthetic workflow-control evidence; not a pilot score')
            lab.write(run / 'operator/manual-score.json', manual)
            record = lab.read(run / 'operator/record.json')
            record.update(status='completed', started_at_utc='2026-11-07T00:00:00Z',
                          ended_at_utc='2026-11-07T00:01:00Z', stop_reason='completed',
                          elapsed_seconds=60, architecture_valid=True, environment_valid=True,
                          observed_root_model='gpt-6-astra', observed_root_effort='high',
                          validity_explanation='synthetic control', trace_evidence='synthetic control',
                          raters=['test fixture'])
            lab.write(run / 'operator/record.json', record)
            summary = lab.summarize(run)
            self.assertEqual(summary['raw_task_score'], 100)
            self.assertTrue(summary['primary_comparison_eligible'])
            auto_path = run / 'operator/automatic-score.json'
            original_auto = lab.read(auto_path)
            for key, bad_value in [('run_id', 'wrong-run'), ('automatic_score', 800),
                                   ('automatic_max', 100)]:
                corrupted = dict(original_auto)
                corrupted[key] = bad_value
                lab.write(auto_path, corrupted)
                with self.assertRaisesRegex(ValueError, 'Automatic'):
                    lab.summarize(run)
            lab.write(auto_path, original_auto)
            record['elapsed_seconds'] = 1801
            lab.write(run / 'operator/record.json', record)
            self.assertFalse(lab.summarize(run)['primary_comparison_eligible'])
            record['elapsed_seconds'] = 60
            lab.write(run / 'operator/record.json', record)
            (run / 'workspace/TASK.md').write_text('tampered')
            lab.evaluate(run)
            self.assertFalse(lab.summarize(run)['primary_comparison_eligible'])
            manual[0]['score'] = float('inf')
            # Deliberately bypass strict JSON writer for malformed operator input.
            (run / 'operator/manual-score.json').write_text(json.dumps(manual))
            with self.assertRaisesRegex(ValueError, 'manual score'):
                lab.summarize(run)


if __name__ == '__main__':
    unittest.main()
