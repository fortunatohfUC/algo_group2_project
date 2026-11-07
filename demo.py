"""Run a small library inventory demonstration with fictional book records."""

from dataclasses import replace

from inventory import LibraryInventory
from models import Book, DuplicateID, InvalidQuantity, NotFound


def sample_books() -> list[Book]:
    """Return fictional metadata; the example ISBN is checksum-valid only."""
    return [
        Book(id="LIB-002", title="Field Guide to Stars", author="Alex Reed",
             category="Science", year=2020, quantity=3, isbn="9780306406157"),
        Book(id="LIB-001", title="Field Guide to Rivers", author="Alex Reed",
             category="Science", year=2015, quantity=0),
        Book(id="LIB-003", title="City Stories", author="Maya Lane",
             category="Fiction", year=2020, quantity=2, isbn="9780134685991"),
        Book(id="LIB-004", title="City Stories: Volume Two", author="Maya Lane",
             category="Fiction", year=2024, quantity=0),
        Book(id="LIB-005", title="Garden Notes", author="Sam Park",
             category="Reference", year=2010, quantity=1),
        Book(id="LIB-006", title="Early Maps", author="Sam Park",
             category="History", year=2005, quantity=4),
    ]


def show_books(label: str, books: list[Book | None]) -> None:
    """Sort for readable display, without changing the inventory results."""
    print(f"\n{label}")
    records = [book for book in books if book is not None]
    if not records:
        print("  No matching books.")
        return
    print(f"  {'ID':<9} {'Title':<30} {'Year':>4} {'Copies':>6}")
    for book in sorted(records, key=lambda record: record.id):
        print(f"  {book.id:<9} {book.title:<30} {book.year:>4} {book.quantity:>6}")


def expect_error(label, error_type, operation) -> None:
    """Show an expected rejection; stop if invalid input is accepted."""
    try:
        operation()
    except error_type as error:
        print(f"  {label}: {type(error).__name__}: {error}")
    else:
        raise RuntimeError(f"Expected rejection did not occur: {label}")


def main() -> None:
    inventory = LibraryInventory()
    books = sample_books()
    print("Library Inventory Tracker")
    print("Six fictional records, held in memory. No files or services are changed.")

    for book in books:
        inventory.add_book(book)
    show_books("1. Add six books (four without ISBNs)", list(inventory.books.values()))

    show_books("2. Find internal ID LIB-002", [inventory.get_book("LIB-002")])
    show_books("Find formatted ISBN 978-0-306-40615-7",
               [inventory.get_book_by_isbn("978-0-306-40615-7")])
    show_books("Find missing ID LIB-999", [inventory.get_book("LIB-999")])

    show_books("3. Title prefix: FIELD GUIDE", inventory.search_title("FIELD GUIDE"))
    show_books("Author prefix: alex", inventory.search_author("alex"))
    show_books("Category prefix: sci", inventory.search_category("sci"))
    show_books("Empty title prefix", inventory.search_title(""))
    show_books("Unmatched title prefix: ocean", inventory.search_title("ocean"))

    show_books("4. Years 2015 through 2020 (both boundaries included)",
               inventory.search_year_range(2015, 2020))
    show_books("Year range with no results: 1990 through 1999",
               inventory.search_year_range(1990, 1999))

    show_books("5. In stock", inventory.get_in_stock())
    show_books("Out of stock", inventory.get_out_of_stock())

    inventory.update_quantity("LIB-002", 0)
    show_books("6. Set LIB-002 quantity from 3 to 0", [inventory.get_book("LIB-002")])
    show_books("Out of stock now includes LIB-002", inventory.get_out_of_stock())
    inventory.update_quantity("LIB-001", 5)
    show_books("Restock LIB-001 from 0 to 5", [inventory.get_book("LIB-001")])
    show_books("In stock now includes LIB-001", inventory.get_in_stock())

    inventory.remove_book("LIB-002")
    show_books("7. Remove LIB-002; internal ID no longer resolves",
               [inventory.get_book("LIB-002")])
    show_books("Its ISBN no longer resolves", [inventory.get_book_by_isbn("9780306406157")])
    show_books("Shared title prefix still finds LIB-001", inventory.search_title("field guide"))
    show_books("Shared year 2020 still finds LIB-003", inventory.search_year_range(2020, 2020))

    print("\n8. Reject invalid changes and queries")
    before = inventory.books.copy()
    expect_error("Duplicate ID", DuplicateID, lambda: inventory.add_book(books[1]))
    expect_error("Duplicate ISBN", ValueError,
                 lambda: inventory.add_book(replace(books[2], id="LIB-007")))
    expect_error("Negative quantity", InvalidQuantity,
                 lambda: inventory.update_quantity("LIB-001", -1))
    expect_error("Missing removal target", NotFound,
                 lambda: inventory.remove_book("LIB-999"))
    expect_error("Reversed year range", ValueError,
                 lambda: inventory.search_year_range(2024, 2010))
    expect_error("Invalid ISBN", ValueError,
                 lambda: inventory.get_book_by_isbn("not-an-isbn"))
    if inventory.books != before:
        raise RuntimeError("The catalog changed during invalid-input checks")
    print("  Catalog is unchanged after the rejected operations.")
    print("\nDemo complete.")


if __name__ == "__main__":
    main()
