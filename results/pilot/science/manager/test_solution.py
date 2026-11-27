"""Contract and independent analytical checks for the elliptic solver.

All expected solutions below are analytical manufactured solutions, not data.
Run from the workspace root: python3.14 -m unittest test_solution -v
"""

import math
import unittest
from fractions import Fraction

from solver import solve


class ContractTests(unittest.TestCase):
    def test_plain_lists_grid_and_boundaries(self):
        x, u = solve(7, lambda x: 2, lambda x: 0, -3, 4)
        self.assertIs(type(x), list)
        self.assertIs(type(u), list)
        self.assertEqual(len(x), 8)
        self.assertEqual(len(u), 8)
        self.assertEqual(x[0], 0)
        self.assertEqual(x[-1], 1)
        for i, xi in enumerate(x):
            self.assertAlmostEqual(xi, i / 7, places=15)
        self.assertEqual(u[0], -3)
        self.assertEqual(u[-1], 4)
        self.assertLess(max(abs(ui - (-3 + 7 * xi)) for xi, ui in zip(x, u)), 1e-12)

    def test_smallest_grid_both_boundary_contributions(self):
        # k(1/4)=2, k(3/4)=4, h=1/2: 6*u_1=1/4*8+2*3+4*(-1).
        x, u = solve(2, lambda x: 1 + 4 * x, lambda x: 8, 3, -1)
        self.assertEqual(x, [0, 0.5, 1])
        self.assertEqual(u[0], 3)
        self.assertEqual(u[-1], -1)
        self.assertAlmostEqual(u[1], 2 / 3, places=14)

    def test_only_required_sample_locations(self):
        n = 8
        faces = {(j + 0.5) / n for j in range(n)}
        interior = {i / n for i in range(1, n)}
        seen_k, seen_f = set(), set()

        def coefficient(x):
            seen_k.add(x)
            # Invalid away from faces: no endpoint or node positivity required.
            return 1 + x if x in faces else -1

        def source(x):
            if x not in interior:
                raise AssertionError('source evaluated outside interior nodes')
            seen_f.add(x)
            return -2

        x, u = solve(n, coefficient, source, 2, 4)
        self.assertEqual(seen_k, faces)
        self.assertEqual(seen_f, interior)
        self.assertLess(max(abs(ui - (2 + 2 * xi)) for xi, ui in zip(x, u)), 1e-12)

    def test_invalid_n(self):
        for n in (True, False, 1, 0, -2, 2.0, 2.5, '2', None, complex(2)):
            with self.subTest(n=n), self.assertRaises(ValueError):
                solve(n, lambda x: 1, lambda x: 0)

    def test_noncallable_functions(self):
        for bad in (None, 0, 1.0, True, 'function', [], {}):
            with self.subTest(argument='k', value=bad), self.assertRaises(ValueError):
                solve(4, bad, lambda x: 0)
            with self.subTest(argument='f', value=bad), self.assertRaises(ValueError):
                solve(4, lambda x: 1, bad)

    def test_invalid_evaluated_values(self):
        invalid_real = (True, False, None, '1', complex(1), [], {},
                        float('nan'), float('inf'), -float('inf'))
        for bad in invalid_real:
            with self.subTest(argument='k', value=bad), self.assertRaises(ValueError):
                solve(4, lambda x, bad=bad: bad, lambda x: 0)
            with self.subTest(argument='f', value=bad), self.assertRaises(ValueError):
                solve(4, lambda x: 1, lambda x, bad=bad: bad)
            for side in ('left', 'right'):
                with self.subTest(argument=side, value=bad), self.assertRaises(ValueError):
                    solve(4, lambda x: 1, lambda x: 0, **{side: bad})
        for bad in (0, -0.0, -1, -0.1):
            with self.subTest(k=bad), self.assertRaises(ValueError):
                solve(4, lambda x, bad=bad: bad, lambda x: 0)

    def test_invalid_values_at_last_required_samples(self):
        # Catch implementations that validate only an initial sample.
        with self.assertRaises(ValueError):
            solve(8, lambda x: float('nan') if x == 15 / 16 else 1, lambda x: 0)
        with self.assertRaises(ValueError):
            solve(8, lambda x: 1, lambda x: float('inf') if x == 7 / 8 else 0)

    def test_callable_exceptions_propagate(self):
        class UserFailure(RuntimeError):
            pass

        def failing(x):
            raise UserFailure('user function failed')

        with self.assertRaises(UserFailure):
            solve(4, failing, lambda x: 0)
        with self.assertRaises(UserFailure):
            solve(4, lambda x: 1, failing)

    def test_other_standard_library_real_scalars(self):
        x, u = solve(8, lambda x: Fraction(1, 2), lambda x: Fraction(0),
                     Fraction(-1, 2), Fraction(3, 2))
        self.assertLess(max(abs(ui - (-0.5 + 2 * xi)) for xi, ui in zip(x, u)), 1e-12)


class NumericalTests(unittest.TestCase):
    def test_variable_coefficient_quadratic_exactness(self):
        # k=2+3x, u=x^2+2x-3 => -(k*u')'=-(12x+10).
        x, u = solve(33, lambda x: 2 + 3 * x, lambda x: -12 * x - 10, -3, 0)
        self.assertLess(max(abs(ui - (xi * xi + 2 * xi - 3))
                            for xi, ui in zip(x, u)), 2e-12)

    def test_variable_coefficient_affine_exactness(self):
        x, u = solve(63, lambda x: 0.1 + 9.9 * x, lambda x: -29.7, -2, 1)
        self.assertLess(max(abs(ui - (-2 + 3 * xi)) for xi, ui in zip(x, u)), 2e-12)

    def test_independent_exponential_second_order(self):
        # k=1+x/2, u=exp(x)+2x-1; f=-((1.5+x/2)*exp(x)+1).
        errors = []
        for n in (16, 32, 64):
            x, u = solve(n, lambda x: 1 + x / 2,
                         lambda x: -((1.5 + x / 2) * math.exp(x) + 1),
                         0, math.e + 1)
            errors.append(max(abs(ui - (math.exp(xi) + 2 * xi - 1))
                              for xi, ui in zip(x, u)))
        self.assertLess(errors[-1], 1e-4)
        for coarse, fine in zip(errors, errors[1:]):
            self.assertGreater(coarse / fine, 3.8)
            self.assertLess(coarse / fine, 4.2)

    def test_algebraic_residual_separate_from_solution_error(self):
        n = 64
        k = lambda x: 1 + x
        f = lambda x: (1 + x) * math.pi ** 2 * math.sin(math.pi * x) - math.pi * math.cos(math.pi * x) - 1
        x, u = solve(n, k, f, 0, 1)
        h = 1 / n
        residuals = [(k((i - 0.5) * h) * (u[i] - u[i - 1])
                      - k((i + 0.5) * h) * (u[i + 1] - u[i])) / h ** 2 - f(x[i])
                     for i in range(1, n)]
        error = max(abs(ui - (math.sin(math.pi * xi) + xi)) for xi, ui in zip(x, u))
        self.assertLess(max(map(abs, residuals)), 1e-9)
        self.assertGreater(error, 1e-6)
        self.assertLess(error, 1e-3)

    def test_max_supported_grid_and_input_magnitudes(self):
        n = 4096
        for coefficient, source, left, right in ((0.1, 100, -100, 100),
                                                  (10, -100, 100, -100)):
            with self.subTest(coefficient=coefficient):
                x, u = solve(n, lambda x, c=coefficient: c,
                             lambda x, s=source: s, left, right)
                self.assertEqual(len(x), n + 1)
                self.assertEqual(len(u), n + 1)
                self.assertEqual(u[0], left)
                self.assertEqual(u[-1], right)
                error = max(abs(ui - (left + (right - left) * xi
                                      + source / (2 * coefficient) * xi * (1 - xi)))
                            for xi, ui in zip(x, u))
                self.assertLess(error, 5e-7)


if __name__ == '__main__':
    unittest.main()
