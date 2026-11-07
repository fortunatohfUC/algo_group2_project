"""Dictionary helpers. LibraryInventory owns and passes both dictionaries.

books maps an internal ID to a Book. isbn_index maps an ISBN to an internal ID.
These helpers do not change the trie, stock or year indexes.

For additions, call validate_add before changing any index.
For removals, call validate_remove first, remove the book's entries from the
trie, stock and year indexes, then call remove_book. Do not delete the ISBN
entry separately: remove_book owns both the ISBN and primary-record deletion.
This groups the plan's two dictionary deletions at the end of removal.
Only LibraryInventory exposes changes.
In inventory.py, import this module as catalog and import Book from models.
Keep self.books and self.isbn_index in LibraryInventory. For example:
    catalog.validate_add(self.books, self.isbn_index, book)
    catalog.add_book(self.books, self.isbn_index, book)
    # LibraryInventory also adds book.id to its tries, stock and year indexes.

For a quantity update, use dataclasses.replace(existing_book, quantity=quantity),
assign the new Book to self.books[book_id], and update stock membership.
The ISBN-to-ID link does not change. Do not assign book.quantity directly.
Tries and stock/year indexes return IDs; inventory resolves them using self.books.
Prefix queries must use normalize_text from models, just like stored records.

Invalid input leaves these dictionaries unchanged. Unexpected runtime failures
and concurrent changes are not covered by rollback in this proof of concept.

Dictionary access is O(1) average and O(n) worst case; insertion is amortized
because dictionaries sometimes resize. ISBN normalization takes O(L) for L
input characters. The dictionaries use O(n) space, excluding the book text.
"""

from typing import Dict, Optional
from models import Book, DuplicateID, NotFound
from models import normalize_isbn, validate_isbn


def validate_add(books: Dict[str, Book], isbn_index: Dict[str, str], book: Book) -> None:
    """Reject a wrong record type or duplicate ID/ISBN without writing data."""
    if not isinstance(book, Book):
        raise ValueError("add_book requires a Book record.")
    if book.id in books:
        raise DuplicateID(f"Book ID already exists: {book.id}")
    if book.isbn is not None and book.isbn in isbn_index:
        raise ValueError(f"ISBN already exists: {book.isbn}")


def add_book(books: Dict[str, Book], isbn_index: Dict[str, str], book: Book) -> None:
    """Store a Book and its optional ISBN-to-ID link."""
    validate_add(books, isbn_index, book)
    books[book.id] = book
    if book.isbn is not None:
        isbn_index[book.isbn] = book.id


def get_book(books: Dict[str, Book], book_id: str) -> Optional[Book]:
    """Return a Book, or None when the ID is not present."""
    if not isinstance(book_id, str):
        raise ValueError("Book ID must be a string.")
    return books.get(book_id)


def require_book(books: Dict[str, Book], book_id: str) -> Book:
    """Return an existing Book, or raise NotFound."""
    book = get_book(books, book_id)
    if book is None:
        raise NotFound(f"Book ID not found: {book_id}")
    return book


def get_book_by_isbn(books: Dict[str, Book], isbn_index: Dict[str, str], isbn: Optional[str]) -> Optional[Book]:
    """Return the matching Book or None; invalid ISBNs raise ValueError."""
    isbn = normalize_isbn(isbn)
    validate_isbn(isbn)
    if isbn is None:
        return None
    book_id = isbn_index.get(isbn)
    if book_id is None:
        return None
    return books.get(book_id)


def validate_remove(books: Dict[str, Book], isbn_index: Dict[str, str], book_id: str) -> Book:
    """Return the Book without deleting it; check that its ISBN entry is correct."""
    book = require_book(books, book_id)
    if book.isbn is not None and isbn_index.get(book.isbn) != book.id:
        raise ValueError("ISBN index is inconsistent with the catalog.")
    return book


def remove_book(books: Dict[str, Book], isbn_index: Dict[str, str], book_id: str) -> None:
    """Remove the record and its ISBN link; other indexes are handled by inventory."""
    book = validate_remove(books, isbn_index, book_id)
    if book.isbn is not None:
        del isbn_index[book.isbn]
    del books[book_id]
