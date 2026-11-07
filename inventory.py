"""Core integration for the in-memory library inventory."""

from dataclasses import replace

import indexes
from models import (
    Book,
    DuplicateID,
    InvalidQuantity,
    NotFound,
    normalize_isbn,
    normalize_text,
    validate_isbn,
)
from trie import Trie


class LibraryInventory:
    """Coordinate the catalog and all secondary indexes.

    The ``books`` dictionary is the single source of truth. Every other
    structure stores book IDs that resolve back to that dictionary.
    """

    def __init__(self) -> None:
        self.books: dict[str, Book] = {}
        self.isbn_index: dict[str, str] = {}
        self.title_trie = Trie()
        self.author_trie = Trie()
        self.category_trie = Trie()
        self.in_stock: set[str] = set()
        self.out_of_stock: set[str] = set()
        self.year_buckets: dict[int, set[str]] = {}
        self.sorted_years: list[int] = []

    @staticmethod
    def _validate_quantity(quantity: int) -> None:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
            raise InvalidQuantity("Quantity must be a nonnegative integer")

    @staticmethod
    def _validate_book_fields(book: Book) -> tuple[str, str, str]:
        required_text = {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "category": book.category,
        }
        for field_name, value in required_text.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a nonempty string")

        if isinstance(book.year, bool) or not isinstance(book.year, int):
            raise ValueError("year must be an integer")

        LibraryInventory._validate_quantity(book.quantity)
        return (
            normalize_text(book.title),
            normalize_text(book.author),
            normalize_text(book.category),
        )

    def _books_for_ids(self, book_ids: set[str]) -> list[Book]:
        return [self.books[book_id] for book_id in book_ids]

    def _search(self, trie: Trie, prefix: str) -> list[Book]:
        """Return sorted prefix matches in O(m + s + k log k) time."""

        normalized_prefix = normalize_text(prefix)
        if not normalized_prefix:
            return []
        book_ids = trie.search_prefix(normalized_prefix)
        return [self.books[book_id] for book_id in sorted(book_ids)]

    def add_book(self, book: Book) -> None:
        """Add one validated book and update every index.

        Under normal hashing, the expected cost is O(L) for an existing year
        and O(L + Y) for a new year. The sorted list can shift Y entries.
        """

        if not isinstance(book, Book):
            raise TypeError("book must be a Book instance")

        title, author, category = self._validate_book_fields(book)
        validate_isbn(book.isbn)
        normalized_isbn = normalize_isbn(book.isbn) if book.isbn is not None else None

        if book.id in self.books:
            raise DuplicateID(f"Book ID already exists: {book.id}")
        if normalized_isbn is not None and normalized_isbn in self.isbn_index:
            raise ValueError(f"ISBN already exists: {normalized_isbn}")

        self.books[book.id] = book
        if normalized_isbn is not None:
            self.isbn_index[normalized_isbn] = book.id

        self.title_trie.insert(title, book.id)
        self.author_trie.insert(author, book.id)
        self.category_trie.insert(category, book.id)
        indexes.add_stock(
            self.in_stock,
            self.out_of_stock,
            book.id,
            book.quantity,
        )
        indexes.add_year(
            self.year_buckets,
            self.sorted_years,
            book.year,
            book.id,
        )

    def get_book(self, book_id: str) -> Book | None:
        """Return a book by internal ID in O(1) average time."""

        return self.books.get(book_id)

    def get_book_by_isbn(self, isbn: str) -> Book | None:
        """Return a book by normalized ISBN in O(1) average time."""

        if isbn is None:
            return None
        book_id = self.isbn_index.get(normalize_isbn(isbn))
        return self.books.get(book_id) if book_id is not None else None

    def search_title(self, prefix: str) -> list[Book]:
        """Return title-prefix matches sorted by internal ID."""

        return self._search(self.title_trie, prefix)

    def search_author(self, prefix: str) -> list[Book]:
        """Return author-prefix matches sorted by internal ID."""

        return self._search(self.author_trie, prefix)

    def search_category(self, prefix: str) -> list[Book]:
        """Return category-prefix matches sorted by internal ID."""

        return self._search(self.category_trie, prefix)

    def search_year_range(self, start: int, end: int) -> list[Book]:
        """Return books in the inclusive year range.

        Selecting and collecting buckets costs O(log Y + Y' + k).
        """

        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
        ):
            raise ValueError("start and end must be integers")
        if start > end:
            raise ValueError("start cannot be greater than end")

        matches = indexes.search_year_range(
            self.year_buckets,
            self.sorted_years,
            start,
            end,
        )
        return self._books_for_ids(matches)

    def get_in_stock(self) -> list[Book]:
        """Return positive-quantity books in O(k) time."""

        return self._books_for_ids(indexes.get_in_stock(self.in_stock))

    def get_out_of_stock(self) -> list[Book]:
        """Return zero-quantity books in O(k) time."""

        return self._books_for_ids(indexes.get_out_of_stock(self.out_of_stock))

    def update_quantity(self, book_id: str, quantity: int) -> None:
        """Replace quantity and update stock membership in O(1) average time."""

        book = self.books.get(book_id)
        if book is None:
            raise NotFound(f"Book ID not found: {book_id}")
        self._validate_quantity(quantity)

        updated_book = replace(book, quantity=quantity)
        self.books[book_id] = updated_book
        indexes.update_stock(
            self.in_stock,
            self.out_of_stock,
            book_id,
            quantity,
        )

    def remove_book(self, book_id: str) -> None:
        """Remove indexes in expected O(L + Y) time under normal hashing.

        Deleting the final book for a year can shift Y entries in the sorted
        year list.
        """

        book = self.books.get(book_id)
        if book is None:
            raise NotFound(f"Book ID not found: {book_id}")

        normalized_isbn = normalize_isbn(book.isbn) if book.isbn is not None else None
        if normalized_isbn is not None:
            self.isbn_index.pop(normalized_isbn, None)

        self.title_trie.remove(normalize_text(book.title), book_id)
        self.author_trie.remove(normalize_text(book.author), book_id)
        self.category_trie.remove(normalize_text(book.category), book_id)
        indexes.remove_stock(self.in_stock, self.out_of_stock, book_id)
        indexes.remove_year(
            self.year_buckets,
            self.sorted_years,
            book.year,
            book_id,
        )

        del self.books[book_id]
