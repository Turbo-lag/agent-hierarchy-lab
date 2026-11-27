import unittest
from solver import solve


class Smoke(unittest.TestCase):
    def test_zero(self):
        x, u = solve(4, lambda x: 1, lambda x: 0)
        self.assertEqual(x, [0, 0.25, 0.5, 0.75, 1])
        self.assertLess(max(abs(v) for v in u), 1e-12)


if __name__ == '__main__':
    unittest.main()
