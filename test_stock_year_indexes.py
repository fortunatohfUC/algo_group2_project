"""Automated tests for stock and year indexes (standard library only)."""
import unittest
from stock_year_indexes import StockYearIndexes


class TestStockYearIndexes(unittest.TestCase):
    def setUp(self):
        self.idx = StockYearIndexes()

    def test_add_stock(self):
        self.idx.add_stock("A", 2)
        self.idx.add_stock("B", 0)
        self.assertEqual(self.idx.get_in_stock(), {"A"})
        self.assertEqual(self.idx.get_out_of_stock(), {"B"})

    def test_update_stock_both_directions(self):
        self.idx.add_stock("A", 0)
        self.idx.update_stock("A", 4)
        self.assertEqual(self.idx.get_in_stock(), {"A"})
        self.idx.update_stock("A", 0)
        self.assertEqual(self.idx.get_out_of_stock(), {"A"})
        self.assertFalse(self.idx.get_in_stock())

    def test_update_missing_book(self):
        with self.assertRaises(KeyError):
            self.idx.update_stock("missing", 1)

    def test_remove_stock(self):
        self.idx.add_stock("A", 2)
        self.idx.remove_stock("A")
        self.assertFalse(self.idx.get_in_stock())

    def test_invalid_quantities_do_not_mutate(self):
        self.idx.add_stock("A", 1)
        for quantity in (-1, 1.5, True, "3"):
            with self.assertRaises(ValueError):
                self.idx.update_stock("A", quantity)
        self.assertEqual(self.idx.get_in_stock(), {"A"})

    def test_stock_results_are_copies(self):
        self.idx.add_stock("A", 1)
        result = self.idx.get_in_stock()
        result.clear()
        self.assertEqual(self.idx.get_in_stock(), {"A"})

    def test_add_year_sorted_unique(self):
        self.idx.add_year(2023, "A")
        self.idx.add_year(2020, "B")
        self.idx.add_year(2023, "C")
        self.assertEqual(self.idx.sorted_years, [2020, 2023])
        self.assertEqual(self.idx.year_buckets[2023], {"A", "C"})

    def test_inclusive_year_range(self):
        for year, book in [(2020, "A"), (2022, "B"), (2024, "C")]:
            self.idx.add_year(year, book)
        self.assertEqual(self.idx.search_year_range(2020, 2022), {"A", "B"})
        self.assertEqual(self.idx.search_year_range(2021, 2021), set())

    def test_remove_year_preserves_shared_bucket(self):
        self.idx.add_year(2020, "A")
        self.idx.add_year(2020, "B")
        self.idx.remove_year(2020, "A")
        self.assertEqual(self.idx.search_year_range(2020, 2020), {"B"})
        self.assertEqual(self.idx.sorted_years, [2020])

    def test_remove_last_book_removes_year(self):
        self.idx.add_year(2020, "A")
        self.idx.remove_year(2020, "A")
        self.assertEqual(self.idx.sorted_years, [])
        self.assertNotIn(2020, self.idx.year_buckets)

    def test_invalid_year_range(self):
        with self.assertRaises(ValueError):
            self.idx.search_year_range(2025, 2020)
        with self.assertRaises(ValueError):
            self.idx.search_year_range("2020", 2025)

    def test_invalid_year_does_not_mutate(self):
        with self.assertRaises(ValueError):
            self.idx.add_year(True, "A")
        self.assertEqual(self.idx.year_buckets, {})

    def test_full_add_update_remove_sequence(self):
        self.idx.add_stock("A", 0)
        self.idx.add_year(2022, "A")
        self.idx.update_stock("A", 2)
        self.assertEqual(self.idx.get_in_stock(), {"A"})
        self.assertEqual(self.idx.search_year_range(2022, 2022), {"A"})
        self.idx.remove_stock("A")
        self.idx.remove_year(2022, "A")
        self.assertEqual(self.idx.get_in_stock(), set())
        self.assertEqual(self.idx.get_out_of_stock(), set())
        self.assertEqual(self.idx.search_year_range(2022, 2022), set())


if __name__ == "__main__":
    unittest.main()
