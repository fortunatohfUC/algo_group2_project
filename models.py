"""Book records and validation for Person 1, Vern.

One Book represents one edition; quantity is its number of copies.
IDs keep their uppercase and lowercase letters. Searchable text is cleaned.
ISBN is optional. Text processing takes O(L) time for L input characters.
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


def normalize_text(value: str) -> str:
    """Use lowercase, remove punctuation and extra spaces; Sci-Fi becomes scifi."""
    if not isinstance(value, str):
        raise ValueError("Searchable text must be a string.")
    characters = []
    for character in value.lower():
        if not unicodedata.category(character).startswith("P"):  # Unicode categories beginning with P are punctuation.
            characters.append(character)
    text = "".join(characters)
    return " ".join(text.split())


def normalize_isbn(value: Optional[str]) -> Optional[str]:
    """Remove whitespace and hyphens; convert a final x to X."""
    if value is None:
        return None
    if not isinstance(value, str):  # ISBNs are strings to preserve leading zeroes.
        raise ValueError("ISBN must be a string or None.")
    without_spaces = "".join(value.split())
    return without_spaces.replace("-", "").upper()


def _is_digits(value: str) -> bool:
    """Accept only the ordinary digits 0 through 9."""
    return value.isascii() and value.isdigit()


def _validate_isbn10(isbn: str) -> None:
    """Check the characters and use the final digit to check for typing errors."""
    if not _is_digits(isbn[:9]) or isbn[-1] not in "0123456789X":
        raise ValueError("ISBN-10 must contain nine digits and a digit or X.")
    total = 0
    for position, character in enumerate(isbn):
        digit = 10 if character == "X" else int(character)  # ISBN-10 allows X as a final check digit worth 10.
        total += digit * (10 - position)
    if total % 11 != 0:
        raise ValueError("ISBN-10 has an invalid check digit.")


def _validate_isbn13(isbn: str) -> None:
    """Check the prefix and digits, then calculate the ISBN-13 check total."""
    if not _is_digits(isbn) or not isbn.startswith(("978", "979")):
        raise ValueError("ISBN-13 must contain 13 digits and start with 978 or 979.")
    total = 0
    for position, character in enumerate(isbn):
        weight = 1 if position % 2 == 0 else 3  # ISBN-13 uses alternating weights of 1 and 3.
        total += int(character) * weight
    if total % 10 != 0:
        raise ValueError("ISBN-13 has an invalid check digit.")


def validate_isbn(value: Optional[str]) -> None:
    """Accept None or a valid ISBN-10/13; checks do not prove a book exists."""
    isbn = normalize_isbn(value)
    if isbn is None:
        return
    if len(isbn) == 10:
        _validate_isbn10(isbn)
    elif len(isbn) == 13:
        _validate_isbn13(isbn)
    else:
        raise ValueError("ISBN must have 10 or 13 characters.")


def validate_quantity(quantity: int) -> None:
    """Accept zero or a positive integer, but not True or False."""
    if type(quantity) is not int or quantity < 0:  # Reject bool as well as non-integers and negative quantities.
        raise InvalidQuantity("Quantity must be a nonnegative integer.")


def _required_text(value: str, name: str) -> str:
    """Clean a required text field and reject it if nothing is left."""
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

    def __post_init__(self) -> None:
        """Check the fields, then save cleaned text before blocking further edits."""
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
        object.__setattr__(self, "title", title)  # Normalize only during construction; later field assignments stay blocked.
        object.__setattr__(self, "author", author)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "isbn", isbn)
