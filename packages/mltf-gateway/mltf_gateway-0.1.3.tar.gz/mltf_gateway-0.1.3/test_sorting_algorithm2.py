import unittest
from sorting_algorithm2 import sorting_algorithm2


class TestSortingAlgorithm2(unittest.TestCase):

    def test_sorted_list(self):
        self.assertEqual(sorting_algorithm2([1, 2, 3, 4, 5]), [1, 2, 3, 4, 5])

    def test_reverse_sorted_list(self):
        self.assertEqual(sorting_algorithm2([5, 4, 3, 2, 1]), [1, 2, 3, 4, 5])

    def test_unsorted_list(self):
        self.assertEqual(
            sorting_algorithm2([3, 1, 4, 1, 5, 9, 2, 6]), [1, 1, 2, 3, 4, 5, 6, 9]
        )

    def test_empty_list(self):
        self.assertEqual(sorting_algorithm2([]), [])

    def test_single_element(self):
        self.assertEqual(sorting_algorithm2([42]), [42])

    def test_duplicate_elements(self):
        self.assertEqual(sorting_algorithm2([2, 2, 2, 2]), [2, 2, 2, 2])

    def test_negative_numbers(self):
        self.assertEqual(sorting_algorithm2([-1, -5, 0, 3, -2]), [-5, -2, -1, 0, 3])

    def test_mixed_positive_negative(self):
        self.assertEqual(sorting_algorithm2([0, -1, 1]), [-1, 0, 1])


if __name__ == "__main__":
    unittest.main()
