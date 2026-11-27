"""Contract, independent discrete-system, and manufactured-solution tests."""

from fractions import Fraction
import math
import unittest

from solver import solve
from verify import build_verification, residuals


class ContractTests(unittest.TestCase):
    def test_shape_grid_and_boundaries(self):
        x, u = solve(7, lambda x: 1, lambda x: 0, -2, 3)
        self.assertIs(type(x), list)
        self.assertIs(type(u), list)
        self.assertEqual(x, [i / 7 for i in range(8)])
        self.assertEqual(len(u), 8)
        self.assertEqual((u[0], u[-1]), (-2, 3))
        self.assertLess(max(abs(v - (-2 + 5 * t)) for t, v in zip(x, u)), 1e-13)

    def test_sampling_locations_and_counts(self):
        k_nodes, f_nodes = [], []

        def k(x):
            k_nodes.append(x)
            self.assertTrue(0 < x < 1)
            return 1 if x in (0.125, 0.375, 0.625, 0.875) else -1

        def f(x):
            f_nodes.append(x)
            self.assertTrue(0 < x < 1)
            return 0

        solve(4, k, f)
        self.assertEqual(k_nodes, [0.125, 0.375, 0.625, 0.875])
        self.assertEqual(f_nodes, [0.25, 0.5, 0.75])

    def test_invalid_n(self):
        for n in (True, False, -2, 0, 1, 2.0, "8", None, math.nan, math.inf):
            with self.subTest(n=n), self.assertRaises(ValueError):
                solve(n, lambda x: 1, lambda x: 0)

    def test_noncallable_functions(self):
        for value in (None, 0, True, [], "function"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    solve(4, value, lambda x: 0)
                with self.assertRaises(ValueError):
                    solve(4, lambda x: 1, value)

    def test_invalid_scalar_values(self):
        for value in (True, False, None, [], "1", 1 + 0j, math.nan,
                      math.inf, -math.inf, 10 ** 1000):
            for argument in ("left", "right", "k", "f"):
                with self.subTest(argument=argument, value=repr(value)), self.assertRaises(ValueError):
                    args = {"n": 4, "k": lambda x: 1, "f": lambda x: 0}
                    args[argument] = (lambda x, v=value: v) if argument in ("k", "f") else value
                    solve(**args)

    def test_every_sample_validated(self):
        for bad_face in range(5):
            for bad in (0, -1, math.nan, math.inf, False):
                with self.subTest(face=bad_face, bad=bad), self.assertRaises(ValueError):
                    solve(5, lambda x: bad if abs(x - (bad_face + 0.5) / 5) < 1e-12 else 1,
                          lambda x: 0)
        for bad_node in range(1, 5):
            with self.subTest(node=bad_node), self.assertRaises(ValueError):
                solve(5, lambda x: 1, lambda x: math.nan if x == bad_node / 5 else 0)

    def test_callback_exceptions_propagate(self):
        error = RuntimeError("callback failure")

        def broken(x):
            raise error

        for k, f in ((broken, lambda x: 0), (lambda x: 1, broken)):
            with self.assertRaises(RuntimeError) as caught:
                solve(4, k, f)
            self.assertIs(caught.exception, error)

    def test_other_real_scalars(self):
        x, u = solve(8, lambda x: Fraction(1, 2), lambda x: Fraction(0),
                     Fraction(-1, 2), Fraction(3, 2))
        self.assertLess(max(abs(v - (2 * t - 0.5)) for t, v in zip(x, u)), 1e-14)


class NumericalTests(unittest.TestCase):
    def test_single_interior_unknown(self):
        k = lambda x: 1 + x
        x, u = solve(2, k, lambda x: 3, 2, -1)
        expected = (0.25 * 3 + k(0.25) * 2 + k(0.75) * -1) / (k(0.25) + k(0.75))
        self.assertAlmostEqual(u[1], expected, places=14)

    def test_two_unknowns_by_determinant(self):
        k = lambda x: 0.1 + 9.9 * x
        f = lambda x: 2 - x
        x, u = solve(3, k, f, -3, 2)
        a, b, c = (k((j + 0.5) / 3) for j in range(3))
        r1, r2 = f(1 / 3) / 9 - 3 * a, f(2 / 3) / 9 + 2 * c
        determinant = (a + b) * (b + c) - b * b
        self.assertAlmostEqual(u[1], ((b + c) * r1 + b * r2) / determinant, places=13)
        self.assertAlmostEqual(u[2], (b * r1 + (a + b) * r2) / determinant, places=13)

    def test_quadratic_with_linear_coefficient(self):
        # Face-centered differences and the flux divergence are exact here.
        k = lambda x: 0.1 + 9.9 * x
        exact = lambda x: x * x + 2 * x - 1
        f = lambda x: -2 * k(x) - 9.9 * (2 * x + 2)
        for n in (2, 7, 32, 128):
            with self.subTest(n=n):
                x, u = solve(n, k, f, -1, 2)
                self.assertLess(max(abs(v - exact(t)) for t, v in zip(x, u)), 1e-11)

    def test_smooth_exponential_manufactured_solution(self):
        # k=e^x, u=e^x, hence -(k u')'=-2 e^(2x).
        errors = []
        for n in (16, 32, 64):
            x, u = solve(n, math.exp, lambda x: -2 * math.exp(2 * x), 1, math.e)
            errors.append(max(abs(v - math.exp(t)) for t, v in zip(x, u)))
        for coarse, fine in zip(errors, errors[1:]):
            self.assertTrue(1.9 < math.log2(coarse / fine) < 2.1)

    def test_supported_maximum_grid_and_coefficient_extremes(self):
        for coefficient in (0.1, 10.0):
            with self.subTest(k=coefficient):
                x, u = solve(4096, lambda x: coefficient, lambda x: 0, -100, 100)
                self.assertEqual(len(u), 4097)
                self.assertLess(max(abs(v - (-100 + 200 * t)) for t, v in zip(x, u)), 1e-7)

    def test_discontinuous_faces_conserve_flux(self):
        k = lambda x: 0.1 if x < 0.37 else 10.0
        x, u = solve(64, k, lambda x: 0, -1, 1)
        fluxes = [k((j + 0.5) / 64) * (u[j + 1] - u[j]) * 64 for j in range(64)]
        self.assertLess(max(fluxes) - min(fluxes), 1e-10)
        self.assertLess(max(map(abs, residuals(x, u, k, lambda x: 0))), 1e-10)
        self.assertTrue(all(a < b for a, b in zip(u, u[1:])))

    def test_required_verification_study(self):
        result = build_verification()
        self.assertTrue(result["all_checks_passed"], result["checks"])
        for case in result["cases"]:
            self.assertEqual([row["n"] for row in case["grids"]], [16, 32, 64, 128])
            for row in case["grids"]:
                self.assertLess(row["max_algebraic_residual"], row["max_error"] * 1e-5)


if __name__ == "__main__":
    unittest.main()
