"""Contract and numerical checks using only Python's standard library."""

import math
import unittest
from decimal import Decimal
from fractions import Fraction

from solver import solve


class SolverTests(unittest.TestCase):
    def test_zero_and_return_contract(self):
        x, u = solve(4, lambda x: 1, lambda x: 0)
        self.assertIs(type(x), list)
        self.assertIs(type(u), list)
        self.assertEqual(x, [0, 0.25, 0.5, 0.75, 1])
        self.assertEqual(u, [0] * 5)

    def test_two_intervals_both_boundary_terms(self):
        x, u = solve(2, lambda x: 1, lambda x: 4, 2, 6)
        self.assertEqual(x, [0.0, 0.5, 1.0])
        self.assertEqual(u, [2.0, 4.5, 6.0])

    def test_affine_nonzero_boundaries(self):
        for k in (0.1, 1.0, 10.0):
            with self.subTest(k=k):
                x, u = solve(257, lambda x: k, lambda x: 0, -12, 23)
                self.assertEqual((u[0], u[-1]), (-12, 23))
                self.assertLess(max(abs(v - (-12 + 35*t)) for t, v in zip(x, u)), 1e-10)

    def test_variable_coefficient_quadratic(self):
        x, u = solve(129, lambda x: 0.5 + 2*x, lambda x: -1 + 24*x, 1, 0)
        self.assertLess(max(abs(v - (1 + 2*t - 3*t*t)) for t, v in zip(x, u)), 1e-11)

    def test_other_smooth_manufactured_solution(self):
        # u=cos(2x)+x, k=2+sin(x); independently differentiated RHS.
        exact = lambda x: math.cos(2*x) + x
        k = lambda x: 2 + math.sin(x)
        f = lambda x: -math.cos(x)*(1 - 2*math.sin(2*x)) + 4*k(x)*math.cos(2*x)
        errors = []
        for n in (32, 64, 128):
            x, u = solve(n, k, f, exact(0), exact(1))
            errors.append(max(abs(v-exact(t)) for t, v in zip(x, u)))
        for old, new in zip(errors, errors[1:]):
            self.assertGreater(old / new, 3.9)
            self.assertLess(old / new, 4.1)

    def test_largest_supported_grid(self):
        x, u = solve(4096, lambda x: 0.1 + 9.9*x,
                     lambda x: -9.9, -1, 0)
        self.assertEqual(len(u), 4097)
        self.assertLess(max(abs(v - (t - 1)) for t, v in zip(x, u)), 2e-9)

    def test_heterogeneous_faces_against_constant_flux_solution(self):
        n = 37
        faces = [0.1 + 9.9 * ((17*j + 3) % n)/(n-1) for j in range(n)]
        _, u = solve(n, lambda x: faces[min(int(n*x), n-1)], lambda x: 0, -30, 80)
        resistance = math.fsum(1/value for value in faces)
        for i, value in enumerate(u):
            expected = -30 + 110 * math.fsum(1/v for v in faces[:i])/resistance
            self.assertLess(abs(value - expected), 1e-10)

    def test_sampling_locations_and_counts(self):
        faces, nodes = [], []
        def k(x):
            faces.append(x)
            return 1 if x not in (0, 1) else -1
        def f(x):
            nodes.append(x)
            if x in (0, 1):
                raise AssertionError("Source called at boundary")
            return 0
        solve(8, k, f)
        self.assertEqual(faces, [(i + .5)/8 for i in range(8)])
        self.assertEqual(nodes, [i/8 for i in range(1, 8)])

    def test_invalid_n(self):
        for n in (True, False, 0, 1, -4, 2.0, "4", None, math.nan, 2+0j):
            with self.subTest(n=n), self.assertRaises(ValueError):
                solve(n, lambda x: 1, lambda x: 0)

    def test_noncallables(self):
        for k, f in ((1, lambda x: 0), (lambda x: 1, None), (None, None)):
            with self.assertRaises(ValueError):
                solve(4, k, f)

    def test_invalid_evaluated_and_boundary_values(self):
        invalid = (True, False, None, "1", 1+0j, [], math.inf, -math.inf, math.nan)
        for value in invalid:
            for position in ("k", "f", "left", "right"):
                args = dict(k=lambda x: 1, f=lambda x: 0, left=0, right=0)
                args[position] = (lambda x, value=value: value) if position in ("k", "f") else value
                with self.subTest(value=value, position=position), self.assertRaises(ValueError):
                    solve(4, **args)
        for value in (0, -1):
            with self.assertRaises(ValueError):
                solve(4, lambda x: value, lambda x: 0)

    def test_bad_last_sample_is_rejected(self):
        with self.assertRaises(ValueError):
            solve(4, lambda x: math.nan if x > .8 else 1, lambda x: 0)
        with self.assertRaises(ValueError):
            solve(4, lambda x: 1, lambda x: math.inf if x > .7 else 0)

    def test_callback_exceptions_propagate(self):
        def broken(x):
            raise RuntimeError("user callback failure")
        with self.assertRaisesRegex(RuntimeError, "user callback failure"):
            solve(4, broken, lambda x: 0)
        with self.assertRaisesRegex(RuntimeError, "user callback failure"):
            solve(4, lambda x: 1, broken)

    def test_other_real_types(self):
        x, u = solve(4, lambda x: Fraction(1, 2), lambda x: Decimal("0"),
                     Fraction(1, 3), Decimal("1.5"))
        self.assertLess(max(abs(v - (1/3 + (1.5-1/3)*t)) for t, v in zip(x, u)), 1e-14)


if __name__ == "__main__":
    unittest.main()
