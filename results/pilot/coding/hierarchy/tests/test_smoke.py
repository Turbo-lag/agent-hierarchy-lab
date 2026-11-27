import unittest
from scheduler import schedule


class Smoke(unittest.TestCase):
    def test_single_task(self):
        self.assertEqual(schedule([{'id': 'a', 'duration': 2, 'deps': []}]),
                         {'a': {'start': 0, 'finish': 2}})


if __name__ == '__main__':
    unittest.main()
