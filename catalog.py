"""Helpers for the main book dictionary and the ISBN-to-ID dictionary.

LibraryInventory passes its own dictionaries to these functions and handles
trie, stock and year changes. Validate before changing any index. For removal,
call validate_remove, remove the other index entries, then call remove_book.
Only remove_book deletes the ISBN entry and the main record.

Dictionary access takes O(1) average time and O(n) worst-case time. Occasional
resizing costs are spread over many additions. The dictionaries use O(n) space,
excluding book text. Cleaning an ISBN takes O(L) for L input characters.
Unexpected runtime failures and concurrent changes are not handled here.
"""

from typing import Dict, Optional
from models import Book, DuplicateID, NotFound
from models import normalize_isbn, validate_isbn


# Check for a Book object, an unused ID, and an unused ISBN when supplied.
# A valid Book can still duplicate an ID or ISBN already in the catalog.
# Change nothing here so inventory can check before updating other indexes.
# Duplicate IDs raise DuplicateID; duplicate ISBNs raise ValueError.
def validate_add(books: Dict[str, Book], isbn_index: Dict[str, str], book: Book) -> None:
    if not isinstance(book, Book):
        raise ValueError("add_book requires a Book record.")
    if book.id in books:
        raise DuplicateID(f"Book ID already exists: {book.id}")
    if book.isbn is not None and book.isbn in isbn_index:
        raise ValueError(f"ISBN already exists: {book.isbn}")


# Check first, then store the Book under its ID in the supplied dictionary.
# The ISBN dictionary stores only the ID, not another copy of the Book.
# Multiple books may have no ISBN. This function returns None on success;
# inventory handles the trie, stock and year entries separately.
def add_book(books: Dict[str, Book], isbn_index: Dict[str, str], book: Book) -> None:
    validate_add(books, isbn_index, book)
    books[book.id] = book
    if book.isbn is not None:
        isbn_index[book.isbn] = book.id


# Reject an ID that is not text, then look up that exact key.
# Dictionary .get returns the Book or None, without scanning every record.
# It does not raise an error just because a valid string ID is missing.
def get_book(books: Dict[str, Book], book_id: str) -> Optional[Book]:
    if not isinstance(book_id, str):
        raise ValueError("Book ID must be a string.")
    return books.get(book_id)


# Use the usual ID lookup, but raise NotFound if nothing matches.
# Call this before a change that requires an existing book.
def require_book(books: Dict[str, Book], book_id: str) -> Book:
    book = get_book(books, book_id)
    if book is None:
        raise NotFound(f"Book ID not found: {book_id}")
    return book


# Clean and validate the ISBN, then follow ISBN -> ID -> current Book.
# Looking up the main record means quantity replacements are seen too.
# None or an unknown valid ISBN returns None; invalid input raises ValueError.
# A link to a missing record also returns None; this does not repair the index.
def get_book_by_isbn(books: Dict[str, Book], isbn_index: Dict[str, str], isbn: Optional[str]) -> Optional[Book]:
    isbn = normalize_isbn(isbn)
    validate_isbn(isbn)
    if isbn is None:
        return None
    book_id = isbn_index.get(isbn)
    if book_id is None:
        return None
    return books.get(book_id)


# Require an existing Book and check that its ISBN points to the same ID.
# A missing or wrong ISBN link raises ValueError before any deletion.
# Return the Book without changing either dictionary so inventory can
# remove the trie, stock and year entries before the catalog entries.
def validate_remove(books: Dict[str, Book], isbn_index: Dict[str, str], book_id: str) -> Book:
    book = require_book(books, book_id)
    if book.isbn is not None and isbn_index.get(book.isbn) != book.id:
        raise ValueError("ISBN index is inconsistent with the catalog.")
    return book


# Check again, then delete the ISBN link (if present) and the main record.
# Inventory first calls validate_remove, removes trie/stock/year entries,
# then calls this function. It must not delete the ISBN link itself.
# The freed ID and ISBN can be used again. This is not a rollback system.
def remove_book(books: Dict[str, Book], isbn_index: Dict[str, str], book_id: str) -> None:
    book = validate_remove(books, isbn_index, book_id)
    if book.isbn is not None:
        del isbn_index[book.isbn]
    del books[book_id]

