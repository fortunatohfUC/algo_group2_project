"""Book records, text cleanup and input checks.

One Book represents one edition, with quantity giving its number of copies.
Text cleanup takes O(L) time for L input characters. ISBN is optional.
"""

from dataclasses import dataclass
from typing import Optional
import unicodedata


class DuplicateID(ValueError):
    """The internal ID already belongs to a book."""


class NotFound(LookupError):
    """The book to update or remove does not exist."""


class InvalidQuantity(ValueError):
    """Quantity must be a whole number of zero or more."""


# Clean stored text and search text in the same way so they can match.
# Lowercase the letters, leave out punctuation, and join words with one space.
# Punctuation is removed, not replaced: "Sci-Fi" becomes "scifi".
# Empty text is allowed here; required book fields are checked separately.
def normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Searchable text must be a string.")
    characters = []
    for character in value.lower():
        if not unicodedata.category(character).startswith("P"):
            characters.append(character)
    text = "".join(characters)
    return " ".join(text.split())


# Keep ISBNs as text so leading zeros are not lost. None means no ISBN.
# Remove whitespace and hyphens, and change x to X so equivalent ISBNs match.
# For example, "0-8044 2957-x" becomes "080442957X".
# This cleans the input; validate_isbn checks whether its format is valid.
def normalize_isbn(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("ISBN must be a string or None.")
    without_spaces = "".join(value.split())
    return without_spaces.replace("-", "").upper()


# Accept only ordinary digits 0 through 9. isdigit() alone also accepts
# some other numeral characters, so isascii() checks the character set too.
def _is_digits(value: str) -> bool:
    return value.isascii() and value.isdigit()


# validate_isbn calls this helper only after checking the length is 10.
# The first nine characters must be digits; the last may also be X (10).
# enumerate gives each character and its position, starting at zero.
# Multiply by weights 10 down to 1. A nonzero remainder after division
# by 11 means the check digit is wrong.
def _validate_isbn10(isbn: str) -> None:
    if not _is_digits(isbn[:9]) or isbn[-1] not in "0123456789X":
        raise ValueError("ISBN-10 must contain nine digits and a digit or X.")
    total = 0
    for position, character in enumerate(isbn):
        digit = 10 if character == "X" else int(character)
        total += digit * (10 - position)
    if total % 11 != 0:
        raise ValueError("ISBN-10 has an invalid check digit.")


# validate_isbn calls this helper only after checking the length is 13.
# Require digits and the prefix 978 or 979. Multiply digits by 1 and 3
# in turn: position % 2 tells us whether the position is even or odd.
# The total must divide evenly by 10 for the check digit to pass.
def _validate_isbn13(isbn: str) -> None:
    if not _is_digits(isbn) or not isbn.startswith(("978", "979")):
        raise ValueError("ISBN-13 must contain 13 digits and start with 978 or 979.")
    total = 0
    for position, character in enumerate(isbn):
        weight = 1 if position % 2 == 0 else 3
        total += int(character) * weight
    if total % 10 != 0:
        raise ValueError("ISBN-13 has an invalid check digit.")


# Clean the input, allow None, and choose the check for its length.
# Success returns None; invalid input raises ValueError. This function
# does not return the cleaned ISBN, so callers use normalize_isbn for that.
# A check digit can detect many typing errors, but does not prove a book exists.
def validate_isbn(value: Optional[str]) -> None:
    isbn = normalize_isbn(value)
    if isbn is None:
        return
    if len(isbn) == 10:
        _validate_isbn10(isbn)
    elif len(isbn) == 13:
        _validate_isbn13(isbn)
    else:
        raise ValueError("ISBN must have 10 or 13 characters.")


# Accept an integer of zero or more; do not convert text such as "3".
# The exact type check also rejects True and False, which Python can treat
# like 1 and 0. Zero means no copies in stock, not a deleted record.
def validate_quantity(quantity: int) -> None:
    if type(quantity) is not int or quantity < 0:
        raise InvalidQuantity("Quantity must be a nonnegative integer.")


# Reuse the text cleanup, then reject a blank or punctuation-only result.
# The name argument identifies the field in the error message.
# The leading underscore marks this as a helper for this module.
def _required_text(value: str, name: str) -> str:
    text = normalize_text(value)
    if not text:
        raise ValueError(f"{name} must contain nonpunctuation text.")
    return text


@dataclass(frozen=True)
class Book:
    """Supply named fields, such as id="B1"; use dataclasses.replace to change quantity.

    Years may be any whole number: the plan sets no year limits. IDs stay unchanged.
    Original capitals and punctuation are not kept in searchable text.
    """

    id: str
    title: str
    author: str
    category: str
    year: int
    quantity: int
    isbn: Optional[str] = None

    # The dataclass calls this after assigning the supplied fields. self is
    # the Book being created. Check its ID, year, quantity, text, then ISBN.
    # ID is checked but not cleaned; year has no minimum or maximum here.
    # object.__setattr__ saves cleaned fields during creation because normal
    # assignment is blocked by frozen=True. A quantity change uses replace()
    # to create another Book; inventory must store it and update stock indexes.
    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Book ID must be a nonempty string.")
        if type(self.year) is not int:
            raise ValueError("Publication year must be an integer.")
        validate_quantity(self.quantity)
        title = _required_text(self.title, "Title")
        author = _required_text(self.author, "Author")
        category = _required_text(self.category, "Category")
        isbn = normalize_isbn(self.isbn)
        validate_isbn(isbn)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "author", author)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "isbn", isbn)

