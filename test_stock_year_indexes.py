"""Automated tests for stock and year indexes (standard library only)."""
import unittest
import indexes


class TestStockYearIndexes(unittest.TestCase):
    def setUp(self):
        self.in_stock = set()
        self.out_of_stock = set()
        self.year_buckets = {}
        self.sorted_years = []

    def test_add_stock(self):
        indexes.add_stock(self.in_stock, self.out_of_stock, "A", 2)
        indexes.add_stock(self.in_stock, self.out_of_stock, "B", 0)
        self.assertEqual(indexes.get_in_stock(self.in_stock), {"A"})
        self.assertEqual(indexes.get_out_of_stock(self.out_of_stock), {"B"})

    def test_update_stock_both_directions(self):
        indexes.add_stock(self.in_stock, self.out_of_stock, "A", 0)
        indexes.update_stock(self.in_stock, self.out_of_stock, "A", 4)
        self.assertEqual(indexes.get_in_stock(self.in_stock), {"A"})
        indexes.update_stock(self.in_stock, self.out_of_stock, "A", 0)
        self.assertEqual(indexes.get_out_of_stock(self.out_of_stock), {"A"})
        self.assertFalse(indexes.get_in_stock(self.in_stock))

    def test_update_missing_book(self):
        with self.assertRaises(KeyError):
            indexes.update_stock(self.in_stock, self.out_of_stock, "missing", 1)

    def test_remove_stock(self):
        indexes.add_stock(self.in_stock, self.out_of_stock, "A", 2)
        indexes.remove_stock(self.in_stock, self.out_of_stock, "A")
        self.assertFalse(indexes.get_in_stock(self.in_stock))

    def test_invalid_quantities_do_not_mutate(self):
        indexes.add_stock(self.in_stock, self.out_of_stock, "A", 1)
        for quantity in (-1, 1.5, True, "3"):
            with self.assertRaises(ValueError):
                indexes.update_stock(self.in_stock, self.out_of_stock, "A", quantity)
        self.assertEqual(indexes.get_in_stock(self.in_stock), {"A"})

    def test_stock_results_are_copies(self):
        indexes.add_stock(self.in_stock, self.out_of_stock, "A", 1)
        result = indexes.get_in_stock(self.in_stock)
        result.clear()
        self.assertEqual(indexes.get_in_stock(self.in_stock), {"A"})

    def test_add_year_sorted_unique(self):
        indexes.add_year(self.year_buckets, self.sorted_years, 2023, "A")
        indexes.add_year(self.year_buckets, self.sorted_years, 2020, "B")
        indexes.add_year(self.year_buckets, self.sorted_years, 2023, "C")
        self.assertEqual(self.sorted_years, [2020, 2023])
        self.assertEqual(self.year_buckets[2023], {"A", "C"})

    def test_inclusive_year_range(self):
        for year, book in [(2020, "A"), (2022, "B"), (2024, "C")]:
            indexes.add_year(self.year_buckets, self.sorted_years, year, book)
        self.assertEqual(indexes.search_year_range(self.year_buckets, self.sorted_years, 2020, 2022), {"A", "B"})
        self.assertEqual(indexes.search_year_range(self.year_buckets, self.sorted_years, 2021, 2021), set())

    def test_remove_year_preserves_shared_bucket(self):
        indexes.add_year(self.year_buckets, self.sorted_years, 2020, "A")
        indexes.add_year(self.year_buckets, self.sorted_years, 2020, "B")
        indexes.remove_year(self.year_buckets, self.sorted_years, 2020, "A")
        self.assertEqual(indexes.search_year_range(self.year_buckets, self.sorted_years, 2020, 2020), {"B"})
        self.assertEqual(self.sorted_years, [2020])

    def test_remove_last_book_removes_year(self):
        indexes.add_year(self.year_buckets, self.sorted_years, 2020, "A")
        indexes.remove_year(self.year_buckets, self.sorted_years, 2020, "A")
        self.assertEqual(self.sorted_years, [])
        self.assertNotIn(2020, self.year_buckets)

    def test_invalid_year_range(self):
        with self.assertRaises(ValueError):
            indexes.search_year_range(self.year_buckets, self.sorted_years, 2025, 2020)
        with self.assertRaises(ValueError):
            indexes.search_year_range(self.year_buckets, self.sorted_years, "2020", 2025)

    def test_invalid_year_does_not_mutate(self):
        with self.assertRaises(ValueError):
            indexes.add_year(self.year_buckets, self.sorted_years, True, "A")
        self.assertEqual(self.year_buckets, {})

    def test_full_add_update_remove_sequence(self):
        indexes.add_stock(self.in_stock, self.out_of_stock, "A", 0)
        indexes.add_year(self.year_buckets, self.sorted_years, 2022, "A")
        indexes.update_stock(self.in_stock, self.out_of_stock, "A", 2)
        self.assertEqual(indexes.get_in_stock(self.in_stock), {"A"})
        self.assertEqual(indexes.search_year_range(self.year_buckets, self.sorted_years, 2022, 2022), {"A"})
        indexes.remove_stock(self.in_stock, self.out_of_stock, "A")
        indexes.remove_year(self.year_buckets, self.sorted_years, 2022, "A")
        self.assertEqual(indexes.get_in_stock(self.in_stock), set())
        self.assertEqual(indexes.get_out_of_stock(self.out_of_stock), set())
        self.assertEqual(indexes.search_year_range(self.year_buckets, self.sorted_years, 2022, 2022), set())


if __name__ == "__main__":
    unittest.main()
