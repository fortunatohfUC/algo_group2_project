"""Person 1 tests. From the project root: python -m unittest discover -s tests -v.

These check Vern's model and dictionary helpers, not teammates' indexes.
"""

import unittest
from dataclasses import FrozenInstanceError, replace
import catalog
from models import Book, DuplicateID, InvalidQuantity, NotFound
from models import normalize_isbn, normalize_text, validate_isbn


def make_book(**changes):
    """Create a new book for each test so tests do not change each other's data."""
    fields = {
        "id": "LIB-00042",
        "title": "The Hobbit!",
        "author": "J.R.R. Tolkien",
        "category": "Fantasy",
        "year": 2012,
        "quantity": 3,
        "isbn": "978-0-547-92822-7",
    }
    fields.update(changes)
    return Book(**fields)


class ModelTests(unittest.TestCase):
    """Check that invalid book details are rejected when creating a Book."""

    def test_normalization(self):
        self.assertEqual(normalize_text("  Sci-Fi,  STORIES! "), "scifi stories")
        self.assertEqual(normalize_text("Alice’s Adventures"), "alices adventures")
        self.assertEqual(normalize_text("  "), "")

    def test_normalized_book(self):
        book = make_book()
        self.assertEqual(book.title, "the hobbit")
        self.assertEqual(book.author, "jrr tolkien")
        self.assertEqual(book.category, "fantasy")
        self.assertEqual(book.isbn, "9780547928227")

    def test_immutable_record(self):
        book = make_book()
        with self.assertRaises(FrozenInstanceError):
            book.quantity = 8

    def test_quantity_replacement(self):
        original = make_book()
        updated = replace(original, quantity=0)
        self.assertEqual((original.quantity, updated.quantity), (3, 0))
        self.assertEqual(updated.isbn, original.isbn)
        with self.assertRaises(InvalidQuantity):
            replace(original, quantity=-1)

    def test_invalid_quantities(self):
        for value in (-1, 1.5, "2", True, False, None):
            with self.subTest(quantity=value):
                with self.assertRaises(InvalidQuantity):
                    make_book(quantity=value)

    def test_required_text(self):
        for field in ("title", "author", "category"):
            for value in ("", "   ", "!—?", None, 12):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        make_book(**{field: value})

    def test_id_validation(self):
        for value in ("", "  ", None, 42):
            with self.subTest(id=value):
                with self.assertRaises(ValueError):
                    make_book(id=value)
        self.assertEqual(make_book(id="Lib-A").id, "Lib-A")

    def test_year_validation(self):
        for value in (2012.0, "2012", True, None):
            with self.subTest(year=value):
                with self.assertRaises(ValueError):
                    make_book(year=value)

    def test_optional_isbn(self):
        self.assertIsNone(make_book(isbn=None).isbn)
        book = Book(
            id="OLD-1",
            title="Hamlet",
            author="Shakespeare",
            category="Drama",
            year=1603,
            quantity=0,
        )
        self.assertIsNone(book.isbn)

    def test_valid_isbn_checks(self):
        for value in ("978-0-547-92822-7", "0-306-40615-2", "0-8044-2957-x", "979-10-90636-07-1", None):
            with self.subTest(isbn=value):
                self.assertIsNone(validate_isbn(value))
        self.assertEqual(normalize_isbn(" 0-8044 2957-x "), "080442957X")

    def test_invalid_isbn_checks(self):
        for value in ("", "123", "9780547928228", "0306406153", "X306406152", "978054792822X", "4006381333931", "９７８０５４７９２８２２７", 9780547928227):
            with self.subTest(isbn=value):
                with self.assertRaises(ValueError):
                    validate_isbn(value)

    def test_normalizers_reject_types(self):
        with self.assertRaises(ValueError):
            normalize_text(25)
        with self.assertRaises(ValueError):
            normalize_isbn(25)


class CatalogTests(unittest.TestCase):
    """Test the book dictionary and ISBN-to-ID dictionary together."""

    def setUp(self):
        self.books = {}
        self.isbn_index = {}
        self.book = make_book()

    def add(self, book):
        return catalog.add_book(self.books, self.isbn_index, book)

    def test_add_lookup(self):
        self.assertIsNone(self.add(self.book))
        self.assertIs(catalog.get_book(self.books, self.book.id), self.book)
        self.assertEqual(self.isbn_index, {"9780547928227": "LIB-00042"})
        found = catalog.get_book_by_isbn(self.books, self.isbn_index, "978-0-547-92822-7")
        self.assertIs(found, self.book)

    def test_missing_lookups(self):
        self.assertIsNone(catalog.get_book(self.books, "MISSING"))
        self.assertIsNone(catalog.get_book_by_isbn(self.books, self.isbn_index, "0306406152"))
        self.assertIsNone(catalog.get_book_by_isbn(self.books, self.isbn_index, None))

    def test_duplicate_id_unchanged(self):
        self.add(self.book)
        before = (self.books.copy(), self.isbn_index.copy())
        with self.assertRaises(DuplicateID):
            self.add(make_book(isbn="0306406152"))
        self.assertEqual((self.books, self.isbn_index), before)

    def test_duplicate_isbn_unchanged(self):
        self.add(self.book)
        before = (self.books.copy(), self.isbn_index.copy())
        with self.assertRaises(ValueError):
            self.add(make_book(id="OTHER", isbn="978 0547928227"))
        self.assertEqual((self.books, self.isbn_index), before)

    def test_multiple_missing_isbns(self):
        self.add(make_book(id="OLD-1", isbn=None))
        self.add(make_book(id="OLD-2", isbn=None))
        self.assertEqual(len(self.books), 2)
        self.assertEqual(self.isbn_index, {})

    def test_shared_titles_separate_editions(self):
        self.add(self.book)
        self.add(make_book(id="EDITION-2", isbn="0306406152", year=1980))
        self.assertEqual(len(self.books), 2)

    def test_remove_and_reuse(self):
        self.add(self.book)
        self.assertIsNone(catalog.remove_book(self.books, self.isbn_index, self.book.id))
        self.assertEqual((self.books, self.isbn_index), ({}, {}))
        self.add(self.book)
        self.assertIs(catalog.get_book(self.books, self.book.id), self.book)

    def test_remove_without_isbn(self):
        self.add(make_book(isbn=None))
        catalog.remove_book(self.books, self.isbn_index, self.book.id)
        self.assertEqual((self.books, self.isbn_index), ({}, {}))

    def test_missing_mutations(self):
        with self.assertRaises(NotFound):
            catalog.require_book(self.books, "MISSING")
        with self.assertRaises(NotFound):
            catalog.remove_book(self.books, self.isbn_index, "MISSING")
        self.assertEqual((self.books, self.isbn_index), ({}, {}))

    def test_preflight_does_not_insert(self):
        catalog.validate_add(self.books, self.isbn_index, self.book)
        self.assertEqual((self.books, self.isbn_index), ({}, {}))

    def test_remove_preflight_does_not_delete(self):
        self.add(self.book)
        self.assertIs(catalog.validate_remove(self.books, self.isbn_index, self.book.id), self.book)
        self.assertIn(self.book.id, self.books)
        self.assertIn(self.book.isbn, self.isbn_index)

    def test_invalid_record_and_query(self):
        with self.assertRaises(ValueError):
            self.add({"id": "RAW"})
        with self.assertRaises(ValueError):
            catalog.get_book_by_isbn(self.books, self.isbn_index, "bad")
        with self.assertRaises(ValueError):
            catalog.get_book(self.books, [])
        self.assertEqual((self.books, self.isbn_index), ({}, {}))

    def test_inconsistent_isbn_delete_stops(self):
        self.add(self.book)
        self.isbn_index[self.book.isbn] = "WRONG-ID"
        before = (self.books.copy(), self.isbn_index.copy())
        with self.assertRaises(ValueError):
            catalog.remove_book(self.books, self.isbn_index, self.book.id)
        self.assertEqual((self.books, self.isbn_index), before)

    def test_quantity_replace_keeps_isbn_reference(self):
        self.add(self.book)
        previous = catalog.require_book(self.books, self.book.id)
        updated = replace(previous, quantity=0)
        self.books[updated.id] = updated
        found = catalog.get_book_by_isbn(self.books, self.isbn_index, updated.isbn)
        self.assertIs(found, updated)
        self.assertEqual(found.quantity, 0)


if __name__ == "__main__":
    unittest.main()
