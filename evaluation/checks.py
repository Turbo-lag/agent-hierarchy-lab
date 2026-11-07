"""External checks. Run a single named case against a submitted workspace."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys

if not __debug__:
    raise RuntimeError('Grading requires assertions; do not use optimized Python')


def load(path):
    # Permit ordinary multi-file submissions, including sibling helper imports.
    sys.path.insert(0, str(Path(path).resolve().parent))
    spec = importlib.util.spec_from_file_location('submission', path)
    module = importlib.util.module_from_spec(spec)
    # Dataclasses and other decorators look up their defining module by name.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rejects(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ValueError:
        return
    raise AssertionError('Expected ValueError')


def close(actual, expected, tol=1e-10):
    assert math.isfinite(actual) and abs(actual - expected) <= tol, (actual, expected)


def task(name, duration, deps=()):
    return dict(id=name, duration=duration, deps=list(deps))


def coding_basic(m):
    assert m.schedule([]) == {}
    got = m.schedule([task('d', 1, ['b', 'c']), task('c', 5, ['a']),
                      task('b', 2, ['a']), task('a', 3)])
    assert got == {'a': {'start': 0, 'finish': 3}, 'b': {'start': 3, 'finish': 5},
                   'c': {'start': 3, 'finish': 8}, 'd': {'start': 8, 'finish': 9}}


def coding_order(m):
    data = [task('z', 2), task('b', 9, ['a']), task('a', 1), task('c', 1, ['z'])]
    assert list(m.schedule(data)) == ['a', 'b', 'z', 'c']
    assert list(m.schedule(list(reversed(data)))) == ['a', 'b', 'z', 'c']


def coding_dependencies(m):
    out = m.schedule([task('a', 0, ['z', 'z']), task('z', 2)])
    assert list(out) == ['z', 'a'] and out['a']['finish'] == 2
    rejects(m.schedule, [task('a', 1, ['missing'])])
    rejects(m.schedule, [task('a', 1, [2])])


def coding_validation(m):
    for data in (None, {}, (), [None], [{}], [task('', 1)],
                 [task('a', 1), task('a', 2)], [task(4, 1)]):
        rejects(m.schedule, data)
    for duration in (-1, float('nan'), float('inf'), -float('inf'), True, '2', None):
        rejects(m.schedule, [task('a', duration)])
    rejects(m.schedule, [{'id': 'a', 'duration': 1, 'deps': 'b'}])
    rejects(m.schedule, [{'id': 'a', 'duration': 1, 'deps': [['b']]}])


def coding_cycles(m):
    rejects(m.schedule, [task('a', 1, ['a'])])
    rejects(m.schedule, [task('a', 1, ['b']), task('b', 1, ['a'])])
    rejects(m.schedule, [task('z', 0), task('a', 1, ['b']), task('b', 1, ['c']),
                         task('c', 1, ['a'])])


def coding_immutable(m):
    data = [task('z', 2), task('a', 3), task('b', 1, ['z', 'a', 'z'])]
    before = copy.deepcopy(data)
    m.schedule(data)
    assert data == before
    bad = [task('z', 1, ['missing']), task('a', 1)]
    before = copy.deepcopy(bad)
    rejects(m.schedule, bad)
    assert bad == before


def coding_chain(m):
    data = [task(f't{i:04}', 1, [f't{i-1:04}'] if i else []) for i in range(2000)]
    out = m.schedule(list(reversed(data)))
    assert len(out) == 2000 and out['t1999']['finish'] == 2000


def coding_arithmetic(m):
    got = m.schedule([task('a', 0.25), task('b', 0, ['a']), task('c', .5, ['b'])])
    close(got['c']['finish'], .75)
    rejects(m.schedule, [task('a', 1e308), task('b', 1e308, ['a'])])
    rejects(m.schedule, [task('a', 10**400)])
    rejects(m.schedule, [task('a', 10**308), task('b', 10**308, ['a'])])


def solution(m, n, k, f, left=0., right=0.):
    x, u = m.solve(n, k, f, left, right)
    assert isinstance(x, list) and isinstance(u, list)
    assert len(x) == len(u) == n + 1
    for i, v in enumerate(x):
        close(v, i / n, 1e-14)
    assert all(math.isfinite(v) for v in u)
    close(u[0], left, 1e-12)
    close(u[-1], right, 1e-12)
    return x, u


def science_affine(m):
    x, u = solution(m, 13, lambda x: 2., lambda x: 0., 2., -1.)
    for a, b in zip(x, u):
        close(b, 2 - 3*a)


def science_polynomial(m):
    x, u = solution(m, 19, lambda x: 3., lambda x: 6., 1., 2.)
    for a, b in zip(x, u):
        close(b, 1 + 2*a - a*a, 1e-10)


def science_convergence(m):
    errors = []
    for n in (16, 32, 64, 128):
        x, u = solution(m, n, lambda x: 1., lambda x: math.pi**2*math.sin(math.pi*x))
        errors.append(max(abs(v-math.sin(math.pi*t)) for t, v in zip(x, u)))
    assert errors[-1] < 6e-5, errors
    assert all(1.9 < math.log2(a/b) < 2.1 for a, b in zip(errors, errors[1:])), errors


def science_variable(m):
    k = lambda x: 1+x
    f = lambda x: (1+x)*math.pi**2*math.sin(math.pi*x)-math.pi*math.cos(math.pi*x)-1
    errors = []
    for n in (16, 32, 64):
        x, u = solution(m, n, k, f, 0., 1.)
        errors.append(max(abs(v-(math.sin(math.pi*t)+t)) for t, v in zip(x, u)))
        for i in range(1, n):
            residual = n*n*(k((i-.5)/n)*(u[i]-u[i-1])-k((i+.5)/n)*(u[i+1]-u[i]))-f(x[i])
            close(residual, 0., 1e-8)
    assert all(1.8 < math.log2(a/b) < 2.2 for a, b in zip(errors, errors[1:])), errors


def science_general(m):
    # Independent manufactured case: k=1+x^2, u=exp(x), so f=-(k+2x)exp(x).
    errors = []
    for n in (24, 48):
        x, u = solution(m, n, lambda x: 1+x*x,
                        lambda x: -(1+x*x+2*x)*math.exp(x), 1., math.e)
        errors.append(max(abs(v-math.exp(t)) for t, v in zip(x, u)))
    assert errors[1] < 2e-4 and 3.5 < errors[0]/errors[1] < 4.5, errors


def science_validation(m):
    for n in (0, 1, -1, 3.5, True, '8'):
        rejects(m.solve, n, lambda x: 1, lambda x: 0)
    for k in (0, -1, float('nan'), float('inf'), True):
        rejects(m.solve, 4, lambda x: k, lambda x: 0)
    for f in (float('nan'), float('inf'), True):
        rejects(m.solve, 4, lambda x: 1, lambda x: f)
    for value in (float('nan'), float('inf'), True, '0'):
        rejects(m.solve, 4, lambda x: 1, lambda x: 0, left=value)
        rejects(m.solve, 4, lambda x: 1, lambda x: 0, right=value)
    rejects(m.solve, 4, None, lambda x: 0)
    rejects(m.solve, 4, lambda x: 1, None)


def science_smallest(m):
    x, u = solution(m, 2, lambda x: 1., lambda x: 2., 1., 3.)
    close(u[1], 2.25)


def science_large(m):
    # A size feasibility check, not a measured asymptotic-performance proof.
    x, u = solution(m, 4096, lambda x: .5, lambda x: 0., -2., 3.)
    assert max(abs(v-(-2+5*t)) for t, v in zip(x, u)) < 1e-7


CASES = {
    'coding': [coding_basic, coding_order, coding_dependencies, coding_validation,
               coding_cycles, coding_immutable, coding_chain, coding_arithmetic],
    'science': [science_affine, science_polynomial, science_convergence, science_variable,
                science_general, science_validation, science_smallest, science_large],
}


def research_structure(root):
    issues = []
    report = root / 'report.md'
    if not report.is_file():
        issues.append('Missing report.md')
    elif not 900 <= len(report.read_text().split()) <= 1400:
        issues.append('report.md outside 900-1400 whitespace-delimited words')
    try:
        claims = json.loads((root / 'claims.json').read_text())
        assert isinstance(claims, list) and 8 <= len(claims) <= 12
        ids = set()
        for claim in claims:
            assert isinstance(claim, dict)
            for key in ('id', 'claim', 'rationale', 'limitation'):
                assert isinstance(claim.get(key), str) and claim[key].strip()
            assert claim['id'] not in ids
            ids.add(claim['id'])
            assert claim.get('support') in ('direct', 'inference')
            refs = claim.get('source_ids')
            assert isinstance(refs, list) and refs
            assert all(isinstance(s, str) and s in {'S1','S2','S3','S4','S5','S6'} for s in refs)
    except (OSError, ValueError, AssertionError, TypeError):
        issues.append('claims.json missing or violates the documented schema')
    return issues


if __name__ == '__main__':
    kind, root, name = sys.argv[1:]
    module = load(Path(root) / ('scheduler.py' if kind == 'coding' else 'solver.py'))
    case = next(fn for fn in CASES[kind] if fn.__name__ == name)
    case(module)
    # A zero exit alone is insufficient: a submission could exit during import.
    print(f'CASE_COMPLETED:{name}')
