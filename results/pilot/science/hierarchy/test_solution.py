"""Independent contract and manufactured-solution checks; standard library only."""

import math
import unittest
from fractions import Fraction

from solver import solve


class SolverContract(unittest.TestCase):
    def test_plain_lists_grid_and_boundary_values(self):
        x, u = solve(7, lambda t: 1, lambda t: 0, -2, 3)
        self.assertIs(type(x), list)
        self.assertIs(type(u), list)
        self.assertEqual(len(x), 8)
        self.assertEqual(len(u), 8)
        self.assertEqual(x[0], 0)
        self.assertEqual(x[-1], 1)
        self.assertEqual(u[0], -2)
        self.assertEqual(u[-1], 3)
        for i, point in enumerate(x):
            self.assertAlmostEqual(point, i / 7, places=15)

    def test_n_two_includes_both_boundary_contributions(self):
        # h=1/2, k_left=5/4, k_right=7/4, f=3.
        # 3*u_mid = h*h*f + (5/4)*2 + (7/4)*(-1).
        x, u = solve(2, lambda t: 1 + t, lambda t: 3, 2, -1)
        self.assertEqual(x, [0.0, 0.5, 1.0])
        self.assertAlmostEqual(u[1], 0.5, places=14)
        self.assertEqual(u[0], 2)
        self.assertEqual(u[2], -1)

    def test_only_face_and_interior_sampling(self):
        n = 8
        allowed_faces = {(i + 0.5) / n for i in range(n)}
        allowed_nodes = {i / n for i in range(1, n)}
        seen_faces, seen_nodes = [], []

        def k(t):
            seen_faces.append(t)
            # In particular, k is invalid at boundaries and grid nodes.
            return 1.0 if t in allowed_faces else -1.0

        def f(t):
            seen_nodes.append(t)
            if t not in allowed_nodes:
                raise AssertionError("source evaluated outside interior nodes")
            return 0.0

        solve(n, k, f)
        self.assertEqual(set(seen_faces), allowed_faces)
        self.assertEqual(set(seen_nodes), allowed_nodes)

    def test_invalid_n(self):
        for n in [True, False, -1, 0, 1, 2.0, 3.5, None, "8", complex(3)]:
            with self.subTest(n=n), self.assertRaises(ValueError):
                solve(n, lambda t: 1, lambda t: 0)

    def test_noncallable_functions(self):
        for value in [None, 0, "function", []]:
            with self.subTest(value=value, role="k"), self.assertRaises(ValueError):
                solve(4, value, lambda t: 0)
            with self.subTest(value=value, role="f"), self.assertRaises(ValueError):
                solve(4, lambda t: 1, value)

    def test_invalid_real_values(self):
        invalid = [True, False, 1 + 0j, 1 + 2j, "1", None,
                   float("inf"), float("-inf"), float("nan")]
        for value in invalid:
            for role in ["left", "right", "k", "f"]:
                with self.subTest(value=value, role=role), self.assertRaises(ValueError):
                    if role in ("left", "right"):
                        solve(4, lambda t: 1, lambda t: 0, **{role: value})
                    elif role == "k":
                        solve(4, lambda t: value, lambda t: 0)
                    else:
                        solve(4, lambda t: 1, lambda t: value)

    def test_nonpositive_coefficients_at_each_face(self):
        for face in range(4):
            for bad in [0.0, -0.1]:
                with self.subTest(face=face, bad=bad), self.assertRaises(ValueError):
                    solve(4, lambda t: bad if t == (face + 0.5) / 4 else 1,
                          lambda t: 0)

    def test_bad_source_at_each_interior_node(self):
        for i in range(1, 4):
            with self.subTest(node=i), self.assertRaises(ValueError):
                solve(4, lambda t: 1,
                      lambda t: float("nan") if t == i / 4 else 0)

    def test_real_fraction_inputs(self):
        _, u = solve(4, lambda t: Fraction(1, 2), lambda t: Fraction(0),
                     Fraction(-1, 2), Fraction(3, 2))
        for i, value in enumerate(u):
            self.assertAlmostEqual(value, -0.5 + 2 * i / 4, places=13)

    def test_user_callback_exceptions_propagate(self):
        class CallbackFailure(RuntimeError):
            pass

        failure = CallbackFailure("intentional user callback failure")

        def fail(t):
            raise failure

        for k, f in [(fail, lambda t: 0), (lambda t: 1, fail)]:
            with self.assertRaises(CallbackFailure) as caught:
                solve(4, k, f)
            self.assertIs(caught.exception, failure)


class NumericalVerification(unittest.TestCase):
    def test_nonzero_affine_constant_and_variable_coefficients(self):
        for coefficient in [0.1, 1.0, 10.0]:
            with self.subTest(coefficient=coefficient):
                x, u = solve(57, lambda t: coefficient, lambda t: 0, -3, 5)
                self.assertLess(max(abs(v - (-3 + 8*t)) for t, v in zip(x, u)), 2e-11)
        # u=-3+8x and k=1+x imply f=-8, so this also tests flux signs.
        x, u = solve(57, lambda t: 1+t, lambda t: -8, -3, 5)
        self.assertLess(max(abs(v - (-3 + 8*t)) for t, v in zip(x, u)), 2e-11)

    def test_quadratic_exactness_and_coefficient_scale(self):
        # For constant k, centered flux differences reproduce a quadratic exactly.
        for coefficient in [0.1, 1.0, 10.0]:
            with self.subTest(coefficient=coefficient):
                x, u = solve(31, lambda t: coefficient, lambda t: 2*coefficient,
                             2, -1)
                self.assertLess(max(abs(v - (2 - 2*t - t*t)) for t, v in zip(x, u)),
                                2e-11)

    def test_unseen_smooth_cases_second_order(self):
        cases = [
            ("polynomial", lambda t: 0.2+2*t,
             lambda t: 1-2*t+t*t+t**3,
             lambda t: -2*(-2+2*t+3*t*t) - (0.2+2*t)*(2+6*t)),
            ("exponential", lambda t: 2+math.cos(t),
             lambda t: math.exp(t)+t*t-2,
             lambda t: math.sin(t)*(math.exp(t)+2*t)
             - (2+math.cos(t))*(math.exp(t)+2)),
            ("oscillatory", lambda t: 1+0.2*math.sin(math.pi*t),
             lambda t: math.sin(2*math.pi*t)+0.3*t-0.2,
             lambda t: -0.2*math.pi*math.cos(math.pi*t)
             * (2*math.pi*math.cos(2*math.pi*t)+0.3)
             + (1+0.2*math.sin(math.pi*t))*4*math.pi**2*math.sin(2*math.pi*t)),
        ]
        for name, k, exact, f in cases:
            with self.subTest(case=name):
                errors = []
                l2_errors = []
                for n in [32, 64, 128]:
                    x, u = solve(n, k, f, exact(0), exact(1))
                    differences = [abs(v-exact(t)) for t, v in zip(x, u)]
                    errors.append(max(differences))
                    l2_errors.append(math.sqrt(sum(e*e for e in differences[1:-1]) / n))
                    self.assertEqual(u[0], exact(0))
                    self.assertEqual(u[-1], exact(1))
                    # This checks the specified discrete equation, not continuum accuracy.
                    residual = max(abs((k((i-0.5)/n)*(u[i]-u[i-1])
                                        - k((i+0.5)/n)*(u[i+1]-u[i]))*n*n
                                       - f(x[i])) for i in range(1, n))
                    self.assertLess(residual, 2e-8)
                self.assertLess(errors[-1], 0.002)
                for norm_errors in [errors, l2_errors]:
                    for coarse, fine in zip(norm_errors, norm_errors[1:]):
                        order = math.log2(coarse/fine)
                        self.assertGreater(order, 1.85)
                        self.assertLess(order, 2.15)

    def test_largest_supported_grid_and_coefficients(self):
        for coefficient in [0.1, 10.0]:
            with self.subTest(coefficient=coefficient):
                x, u = solve(4096, lambda t: coefficient, lambda t: 0, -100, 100)
                self.assertEqual(len(u), 4097)
                self.assertLess(max(abs(v-(-100+200*t)) for t, v in zip(x, u)), 2e-6)
                self.assertTrue(all(math.isfinite(v) for v in u))


if __name__ == "__main__":
    unittest.main()
