"""Integration tests for the public LibraryInventory contract."""

import unittest

from inventory import LibraryInventory
from models import Book, DuplicateID, InvalidQuantity, NotFound


class LibraryInventoryIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = LibraryInventory()
        # These are synthetic records chosen to exercise search and ISBN rules.
        self.hobbit = Book(
            id="LIB-002",
            isbn="978-0-13-468599-1",
            title="The Hobbit",
            author="J. R. R. Tolkien",
            category="Fantasy",
            year=1937,
            quantity=2,
        )
        self.algorithms = Book(
            id="LIB-001",
            isbn="9780262046305",
            title="Introduction to Algorithms",
            author="Thomas H. Cormen",
            category="Computer Science",
            year=2022,
            quantity=0,
        )

    def test_add_and_lookup_by_id_and_isbn(self) -> None:
        self.inventory.add_book(self.hobbit)

        self.assertIs(self.inventory.get_book("LIB-002"), self.hobbit)
        self.assertIs(
            self.inventory.get_book_by_isbn("9780134685991"),
            self.hobbit,
        )
        self.assertIsNone(self.inventory.get_book("MISSING"))
        self.assertIsNone(self.inventory.get_book_by_isbn("0134685997"))

    def test_add_without_isbn(self) -> None:
        book = Book(
            id="LIB-003",
            isbn=None,
            title="A Wizard of Earthsea",
            author="Ursula K. Le Guin",
            category="Fantasy",
            year=1968,
            quantity=1,
        )

        self.inventory.add_book(book)

        self.assertIs(self.inventory.get_book("LIB-003"), book)
        self.assertEqual(self.inventory.isbn_index, {})

    def test_duplicate_id_and_normalized_isbn_leave_state_unchanged(self) -> None:
        self.inventory.add_book(self.hobbit)
        duplicate_id = Book(
            id="LIB-002",
            isbn="0134685997",
            title="Effective Python",
            author="Brett Slatkin",
            category="Computer Science",
            year=2019,
            quantity=1,
        )
        duplicate_isbn = Book(
            id="LIB-004",
            isbn="9780134685991",
            title="Another Edition",
            author="Another Author",
            category="Reference",
            year=2020,
            quantity=1,
        )

        with self.assertRaises(DuplicateID):
            self.inventory.add_book(duplicate_id)
        with self.assertRaises(ValueError):
            self.inventory.add_book(duplicate_isbn)

        self.assertEqual(list(self.inventory.books), ["LIB-002"])
        self.assertEqual(self.inventory.in_stock, {"LIB-002"})
        self.assertEqual(self.inventory.sorted_years, [1937])

    def test_invalid_isbn_is_rejected_before_inventory_mutation(self) -> None:
        invalid = Book(
            id="LIB-005",
            isbn=None,
            title="Invalid ISBN Fixture",
            author="Example Author",
            category="Reference",
            year=2026,
            quantity=1,
        )
        # Bypass constructor validation to verify that add_book rechecks first.
        object.__setattr__(invalid, "isbn", "9780262046306")

        with self.assertRaises(ValueError):
            self.inventory.add_book(invalid)

        self.assertEqual(self.inventory.books, {})
        self.assertEqual(self.inventory.isbn_index, {})
        self.assertEqual(self.inventory.in_stock, set())
        self.assertEqual(self.inventory.year_buckets, {})

    def test_prefix_searches_normalize_and_sort_by_id(self) -> None:
        other_hobbit = Book(
            id="LIB-000",
            isbn=None,
            title="The Hobbit: Illustrated Edition",
            author="J. R. R. Tolkien",
            category="Fantasy Classics",
            year=2023,
            quantity=1,
        )
        self.inventory.add_book(self.hobbit)
        self.inventory.add_book(other_hobbit)
        self.inventory.add_book(self.algorithms)

        self.assertEqual(
            [book.id for book in self.inventory.search_title("THE HOBBIT")],
            ["LIB-000", "LIB-002"],
        )
        self.assertEqual(
            [book.id for book in self.inventory.search_author("j. r. r.")],
            ["LIB-000", "LIB-002"],
        )
        self.assertEqual(
            [book.id for book in self.inventory.search_category("fantasy")],
            ["LIB-000", "LIB-002"],
        )
        self.assertEqual(self.inventory.search_title(""), [])
        self.assertEqual(self.inventory.search_author("missing"), [])

    def test_year_range_is_inclusive_and_validated(self) -> None:
        self.inventory.add_book(self.hobbit)
        self.inventory.add_book(self.algorithms)

        self.assertCountEqual(
            [book.id for book in self.inventory.search_year_range(1937, 2022)],
            ["LIB-001", "LIB-002"],
        )
        self.assertEqual(
            [book.id for book in self.inventory.search_year_range(1937, 1937)],
            ["LIB-002"],
        )
        self.assertEqual(self.inventory.search_year_range(1950, 1960), [])
        with self.assertRaises(ValueError):
            self.inventory.search_year_range(2022, 1937)

    def test_stock_queries_use_stock_sets(self) -> None:
        self.inventory.add_book(self.hobbit)
        self.inventory.add_book(self.algorithms)

        self.assertCountEqual(
            [book.id for book in self.inventory.get_in_stock()],
            ["LIB-002"],
        )
        self.assertCountEqual(
            [book.id for book in self.inventory.get_out_of_stock()],
            ["LIB-001"],
        )

    def test_update_quantity_replaces_frozen_record_and_stock_status(self) -> None:
        self.inventory.add_book(self.hobbit)
        original = self.inventory.get_book("LIB-002")

        self.inventory.update_quantity("LIB-002", 0)
        updated = self.inventory.get_book("LIB-002")

        self.assertIsNot(updated, original)
        self.assertEqual(original.quantity, 2)
        self.assertEqual(updated.quantity, 0)
        self.assertEqual(self.inventory.get_in_stock(), [])
        self.assertCountEqual(
            [book.id for book in self.inventory.get_out_of_stock()],
            ["LIB-002"],
        )

    def test_invalid_quantity_and_missing_update_leave_state_unchanged(self) -> None:
        self.inventory.add_book(self.hobbit)
        original = self.inventory.get_book("LIB-002")

        with self.assertRaises(InvalidQuantity):
            self.inventory.update_quantity("LIB-002", -1)
        with self.assertRaises(InvalidQuantity):
            self.inventory.update_quantity("LIB-002", 1.5)
        with self.assertRaises(NotFound):
            self.inventory.update_quantity("MISSING", 1)

        self.assertIs(self.inventory.get_book("LIB-002"), original)
        self.assertEqual(self.inventory.in_stock, {"LIB-002"})
        self.assertEqual(self.inventory.out_of_stock, set())

    def test_remove_book_clears_every_index(self) -> None:
        shared = Book(
            id="LIB-003",
            isbn="0134685997",
            title="The Hobbit Companion",
            author="J. R. R. Tolkien",
            category="Fantasy",
            year=1937,
            quantity=0,
        )
        self.inventory.add_book(self.hobbit)
        self.inventory.add_book(shared)

        self.inventory.remove_book("LIB-002")

        self.assertIsNone(self.inventory.get_book("LIB-002"))
        self.assertIsNone(self.inventory.get_book_by_isbn("9780134685991"))
        self.assertEqual(
            [book.id for book in self.inventory.search_title("the hobbit")],
            ["LIB-003"],
        )
        self.assertEqual(
            [book.id for book in self.inventory.search_author("j. r.")],
            ["LIB-003"],
        )
        self.assertEqual(self.inventory.in_stock, set())
        self.assertEqual(self.inventory.out_of_stock, {"LIB-003"})
        self.assertEqual(self.inventory.year_buckets, {1937: {"LIB-003"}})
        self.assertEqual(self.inventory.sorted_years, [1937])

        self.inventory.remove_book("LIB-003")
        self.assertEqual(self.inventory.year_buckets, {})
        self.assertEqual(self.inventory.sorted_years, [])
        with self.assertRaises(NotFound):
            self.inventory.remove_book("MISSING")

    def test_sequence_preserves_cross_index_consistency(self) -> None:
        self.inventory.add_book(self.hobbit)
        self.inventory.add_book(self.algorithms)
        self.inventory.update_quantity("LIB-001", 3)
        self.inventory.remove_book("LIB-002")

        self.assertEqual(set(self.inventory.books), {"LIB-001"})
        self.assertEqual(self.inventory.isbn_index, {"9780262046305": "LIB-001"})
        self.assertEqual(self.inventory.in_stock, {"LIB-001"})
        self.assertEqual(self.inventory.out_of_stock, set())
        self.assertEqual(self.inventory.year_buckets, {2022: {"LIB-001"}})
        self.assertEqual(self.inventory.sorted_years, [2022])
        self.assertEqual(
            [book.id for book in self.inventory.search_title("introduction")],
            ["LIB-001"],
        )
        self.assertEqual(self.inventory.search_category("fantasy"), [])


if __name__ == "__main__":
    unittest.main()
