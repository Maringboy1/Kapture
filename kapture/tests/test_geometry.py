import unittest
from kapture.core.geometry import even, clamp, contains, union_rects


class TestGeometry(unittest.TestCase):
    def test_even(self):
        self.assertEqual(even(863), 862)
        self.assertEqual(even(1920), 1920)
        self.assertEqual(even(1), 2)
        self.assertEqual(even(0), 0)

    def test_clamp(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-1, 0, 10), 0)
        self.assertEqual(clamp(99, 0, 10), 10)

    def test_contains(self):
        self.assertTrue(contains((10, 10, 20, 20), 15, 15))
        self.assertFalse(contains((10, 10, 20, 20), 5, 5))

    def test_union(self):
        self.assertEqual(union_rects([(0, 0, 10, 10), (5, 5, 10, 10)]), (0, 0, 15, 15))
        self.assertIsNone(union_rects([]))
