"""Numerical and input-contract tests; standard-library unittest only."""

from decimal import Decimal
from fractions import Fraction
import math
import unittest

from solver import solve


class SolverContract(unittest.TestCase):
    def test_lists_grid_and_boundaries(self):
        x, u = solve(7, lambda x: 1, lambda x: 0, -3, 4)
        self.assertIs(type(x), list)
        self.assertIs(type(u), list)
        self.assertEqual(len(x), 8)
        self.assertEqual(len(u), 8)
        self.assertEqual(x, [i / 7 for i in range(8)])
        self.assertEqual((u[0], u[-1]), (-3, 4))

    def test_single_interior_both_boundaries(self):
        x, u = solve(2, lambda x: 3, lambda x: 0, -2, 6)
        self.assertEqual(x, [0, 0.5, 1])
        self.assertEqual(u, [-2, 2, 6])

    def test_exact_sampling_locations(self):
        k_samples, f_samples = [], []
        n = 11
        faces = [(j + 0.5) / n for j in range(n)]
        nodes = [i / n for i in range(1, n)]

        def coefficient(x):
            k_samples.append(x)
            return 1 if x in faces else -1

        def source(x):
            f_samples.append(x)
            self.assertIn(x, nodes)
            return 0

        solve(n, coefficient, source)
        self.assertEqual(k_samples, faces)
        self.assertEqual(f_samples, nodes)

    def test_real_scalar_types(self):
        x, u = solve(8, lambda x: Decimal("1.5"),
                     lambda x: Fraction(0, 1), Fraction(1, 2), Decimal("2.5"))
        self.assertLess(max(abs(ui - (0.5 + 2 * xi)) for xi, ui in zip(x, u)), 1e-14)

    def test_invalid_n(self):
        for n in (True, False, 1, 0, -3, 4.0, "4", None, 2j):
            with self.subTest(n=n), self.assertRaises(ValueError):
                solve(n, lambda x: 1, lambda x: 0)

    def test_noncallable_functions(self):
        for k, f in ((1, lambda x: 0), (lambda x: 1, 0), (None, None)):
            with self.subTest(k=k, f=f), self.assertRaises(ValueError):
                solve(4, k, f)

    def test_invalid_scalars_every_position(self):
        invalid = (True, False, float("nan"), float("inf"), -float("inf"),
                   complex(1, 0), "1", None, [], {},
                   Decimal("NaN"), Decimal("Infinity"), 10 ** 1000)
        for value in invalid:
            for position in ("left", "right", "k", "f"):
                with self.subTest(value=value, position=position), self.assertRaises(ValueError):
                    k = (lambda x: value) if position == "k" else lambda x: 1
                    f = (lambda x: value) if position == "f" else lambda x: 0
                    solve(5, k, f,
                          value if position == "left" else 0,
                          value if position == "right" else 0)

    def test_nonpositive_coefficients(self):
        for value in (0, -0.0, -1, -100):
            with self.subTest(value=value), self.assertRaises(ValueError):
                solve(8, lambda x: value, lambda x: 0)

    def test_late_invalid_samples(self):
        with self.assertRaises(ValueError):
            solve(8, lambda x: 0 if x > 0.9 else 1, lambda x: 0)
        with self.assertRaises(ValueError):
            solve(8, lambda x: 1, lambda x: float("nan") if x > 0.8 else 0)

    def test_user_exceptions_propagate(self):
        class UserFailure(RuntimeError):
            pass

        def broken(x):
            raise UserFailure("a user callable failed")

        with self.assertRaisesRegex(UserFailure, "a user callable failed"):
            solve(4, broken, lambda x: 0)
        with self.assertRaisesRegex(UserFailure, "a user callable failed"):
            solve(4, lambda x: 1, broken)


class SolverNumerics(unittest.TestCase):
    def assert_exact(self, n, k, f, exact, tolerance=2e-12):
        x, u = solve(n, k, f, exact(0), exact(1))
        error = max(abs(ui - exact(xi)) for xi, ui in zip(x, u))
        self.assertLess(error, tolerance)
        return x, u

    def test_constant_coefficient_quadratic(self):
        self.assert_exact(47, lambda x: 2.5, lambda x: -5,
                          lambda x: x * x - 3 * x + 2)

    def test_variable_coefficient_affine(self):
        self.assert_exact(63, lambda x: 1 + x, lambda x: -5,
                          lambda x: -2 + 5 * x)

    def test_discontinuous_positive_coefficient_discrete_flux(self):
        n = 29
        k = lambda x: 0.1 if x < 0.42 else 10.0
        x, u = solve(n, k, lambda x: 0, -1, 2)
        resistances = [1 / k((j + 0.5) / n) for j in range(n)]
        total = math.fsum(resistances)
        accumulated = 0.0
        expected = [-1.0]
        for resistance in resistances:
            accumulated += resistance
            expected.append(-1 + 3 * accumulated / total)
        self.assertLess(max(abs(a - b) for a, b in zip(u, expected)), 1e-12)

    def test_manufactured_convergence(self):
        pi = math.pi
        cases = [
            (lambda x: 1, lambda x: pi ** 2 * math.sin(pi * x),
             lambda x: math.sin(pi * x)),
            (lambda x: 1 + x,
             lambda x: (1 + x) * pi ** 2 * math.sin(pi * x) - pi * math.cos(pi * x) - 1,
             lambda x: math.sin(pi * x) + x),
            (lambda x: 2 + x, lambda x: -(3 + x) * math.exp(x), math.exp),
        ]
        for case_number, (k, f, exact) in enumerate(cases):
            previous = None
            for n in (16, 32, 64, 128):
                with self.subTest(case=case_number, n=n):
                    x, u = solve(n, k, f, exact(0), exact(1))
                    errors = [abs(ui - exact(xi)) for xi, ui in zip(x, u)]
                    norms = (max(errors), math.sqrt(math.fsum(e * e for e in errors[1:-1]) / n))
                    if previous is not None:
                        for prior, current in zip(previous, norms):
                            self.assertGreater(math.log2(prior / current), 1.9)
                            self.assertLess(math.log2(prior / current), 2.1)
                    previous = norms

    def test_independent_algebraic_residual(self):
        n = 93
        k = lambda x: 0.2 + 7 * x * x
        f = lambda x: 3 * math.cos(4 * x) - 2
        x, u = solve(n, k, f, -4, 1.5)
        for i in range(1, n):
            left_term = k((i - 0.5) / n) * (u[i] - u[i - 1]) * n * n
            right_term = k((i + 0.5) / n) * (u[i + 1] - u[i]) * n * n
            residual = abs(left_term - right_term - f(x[i]))
            scale = max(1.0, abs(left_term), abs(right_term), abs(f(x[i])))
            self.assertLess(residual, 1e-10 * scale)

    def test_supported_largest_grid_and_coefficient_limits(self):
        for coefficient in (0.1, 10.0):
            with self.subTest(coefficient=coefficient):
                self.assert_exact(4096, lambda x: coefficient, lambda x: 0,
                                  lambda x: -10 + 30 * x, tolerance=2e-8)


if __name__ == "__main__":
    unittest.main()
