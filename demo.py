"""Run an interactive demo for a small library inventory demonstration with fictional book records."""

from dataclasses import replace

from inventory import LibraryInventory
from models import Book, DuplicateID, InvalidQuantity, NotFound


SAMPLE_RECORDS = [
    {"id": "LIB-002", "title": "Field Guide to Stars", "author": "Alex Reed",
     "category": "Science", "year": 2020, "quantity": 3, "isbn": "9780306406157"},
    {"id": "LIB-001", "title": "Field Guide to Rivers", "author": "Alex Reed",
     "category": "Science", "year": 2015, "quantity": 0, "isbn": None},
    {"id": "LIB-003", "title": "City Stories", "author": "Maya Lane",
     "category": "Fiction", "year": 2020, "quantity": 2, "isbn": "9780134685991"},
    {"id": "LIB-004", "title": "City Stories: Volume Two", "author": "Maya Lane",
     "category": "Fiction", "year": 2024, "quantity": 0, "isbn": None},
    {"id": "LIB-005", "title": "Garden Notes", "author": "Sam Park",
     "category": "Reference", "year": 2010, "quantity": 1, "isbn": None},
    {"id": "LIB-006", "title": "Early Maps", "author": "Sam Park",
     "category": "History", "year": 2005, "quantity": 4, "isbn": None},
]


def sample_books() -> list[Book]:
    """Build Books from fictional metadata with checksum-valid example ISBNs."""
    return [Book(**record) for record in SAMPLE_RECORDS]


def show_sample_records() -> None:
    """Display all original fields before constructing normalized Books."""
    print("\nRaw sample dataset (before validation and normalization):")
    columns = ("id", "title", "author", "category", "year", "quantity", "isbn")
    row_format = "{:<9} | {:<26} | {:<12} | {:<10} | {:>4} | {:>6} | {:<13}"
    heading = row_format.format("ID", "Title", "Author", "Category", "Year", "Copies", "ISBN")
    print(heading)
    print("-" * len(heading))
    for record in SAMPLE_RECORDS:
        values = [record[key] if record[key] is not None else "(none)" for key in columns]
        print(row_format.format(*values))


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


def guided_demo() -> None:
    print("Library Inventory Tracker")
    print("Six fictional records, held in memory. No files or services are changed.")
    show_sample_records()

    input("\nPress Enter to continue: Add six sample books...")
    inventory = LibraryInventory()
    books = sample_books()
    for book in books:
        inventory.add_book(book)
    show_books("1. Add six books (four without ISBNs)", list(inventory.books.values()))

    input("\nPress Enter to continue: Find books by ID and ISBN...")
    show_books("2. Find internal ID LIB-002", [inventory.get_book("LIB-002")])
    show_books("Find formatted ISBN 978-0-306-40615-7",
               [inventory.get_book_by_isbn("978-0-306-40615-7")])
    show_books("Find missing ID LIB-999", [inventory.get_book("LIB-999")])

    input("\nPress Enter to continue: Search by title, author, and category...")
    show_books("3. Title prefix: FIELD GUIDE", inventory.search_title("FIELD GUIDE"))
    show_books("Author prefix: alex", inventory.search_author("alex"))
    show_books("Category prefix: sci", inventory.search_category("sci"))
    show_books("Empty title prefix", inventory.search_title(""))
    show_books("Unmatched title prefix: ocean", inventory.search_title("ocean"))

    input("\nPress Enter to continue: Search by publication year...")
    show_books("4. Years 2015 through 2020 (both boundaries included)",
               inventory.search_year_range(2015, 2020))
    show_books("Year range with no results: 1990 through 1999",
               inventory.search_year_range(1990, 1999))

    input("\nPress Enter to continue: Show stock status...")
    show_books("5. In stock", inventory.get_in_stock())
    show_books("Out of stock", inventory.get_out_of_stock())

    input("\nPress Enter to continue: Change quantities and show the updated stock lists...")
    inventory.update_quantity("LIB-002", 0)
    show_books("6. Set LIB-002 quantity from 3 to 0", [inventory.get_book("LIB-002")])
    show_books("Out of stock now includes LIB-002", inventory.get_out_of_stock())
    inventory.update_quantity("LIB-001", 5)
    show_books("Restock LIB-001 from 0 to 5", [inventory.get_book("LIB-001")])
    show_books("In stock now includes LIB-001", inventory.get_in_stock())

    input("\nPress Enter to continue: Remove a book and check the remaining matches...")
    inventory.remove_book("LIB-002")
    show_books("7. Remove LIB-002; internal ID no longer resolves",
               [inventory.get_book("LIB-002")])
    show_books("Its ISBN no longer resolves", [inventory.get_book_by_isbn("9780306406157")])
    show_books("Shared title prefix still finds LIB-001", inventory.search_title("field guide"))
    show_books("Shared year 2020 still finds LIB-003", inventory.search_year_range(2020, 2020))

    input("\nPress Enter to continue: Show how invalid requests are rejected...")
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



def ask(label: str, default: str = "") -> str:
    """Use the shown example when the user presses Enter."""
    hint = f" [{default}]" if default else ""
    answer = input(f"{label}{hint}: ").strip()
    return answer or default


def ask_number(label: str, default: int) -> int:
    """Keep asking until the user enters a whole number."""
    while True:
        try:
            return int(ask(label, str(default)))
        except ValueError:
            print("Please enter a whole number.")


def add_from_input(inventory: LibraryInventory) -> None:
    """Collect a book's details, then let the model validate them."""
    number = 7
    while f"LIB-{number:03d}" in inventory.books:
        number += 1
    book = Book(
        id=ask("Book ID", f"LIB-{number:03d}"),
        title=ask("Title", "New Library Book"),
        author=ask("Author", "Taylor Green"),
        category=ask("Category", "Reference"),
        year=ask_number("Publication year", 2026),
        quantity=ask_number("Number of copies", 1),
        isbn=ask("ISBN (optional; Enter leaves it blank)") or None,
    )
    inventory.add_book(book)
    show_books("Book added", [book])


def perform_action(inventory: LibraryInventory, choice: str) -> None:
    """Run one menu choice using the existing inventory methods."""
    if choice == "1":
        show_books("All books", list(inventory.books.values()))
    elif choice == "2":
        add_from_input(inventory)
    elif choice == "3":
        book_id = ask("Book ID", "LIB-002")
        show_books("ID lookup", [inventory.get_book(book_id)])
    elif choice == "4":
        isbn = ask("ISBN", "978-0-306-40615-7")
        show_books("ISBN lookup", [inventory.get_book_by_isbn(isbn)])
    elif choice in ("5", "6", "7"):
        searches = {
            "5": ("Title prefix", "field guide", inventory.search_title),
            "6": ("Author prefix", "alex", inventory.search_author),
            "7": ("Category prefix", "sci", inventory.search_category),
        }
        label, default, search = searches[choice]
        show_books(label, search(ask(label, default)))
    elif choice == "8":
        start = ask_number("First year (included)", 2015)
        end = ask_number("Last year (included)", 2020)
        show_books("Year matches", inventory.search_year_range(start, end))
    elif choice == "9":
        show_books("In stock", inventory.get_in_stock())
        show_books("Out of stock", inventory.get_out_of_stock())
    elif choice == "10":
        book_id = ask("Book ID", "LIB-002")
        quantity = ask_number("New total copies (not an amount to add)", 0)
        inventory.update_quantity(book_id, quantity)
        show_books("Quantity updated", [inventory.get_book(book_id)])
    elif choice == "12":
        k = ask_number("How many scarce in-stock books? (K)", 3)
        results = inventory.top_k_scarce(k)
        print("\nTop-K scarce IN-STOCK books (quantity > 0; fewest copies first):")
        for rank, book in enumerate(results, start=1):
            print(f"  {rank}. {book.id}: {book.title} | copies={book.quantity}")
        if not results:
            print("  No records requested or available.")
    elif choice == "11":
        book_id = ask("Book ID", "LIB-002")
        book = inventory.get_book(book_id)
        if book is None:
            raise NotFound(f"Book not found: {book_id}")
        show_books("Book to remove", [book])
        if ask("Remove this book? Type yes to confirm", "no").lower() == "yes":
            inventory.remove_book(book_id)
            print(f"Removed {book_id} from the catalog and its indexes.")
        else:
            print("Removal canceled.")
    else:
        print("Choose a number from 0 to 12.")


def interactive_demo() -> None:
    """Keep changes in memory while the user tries different operations."""
    inventory = LibraryInventory()
    for book in sample_books():
        inventory.add_book(book)
    print("\nLoaded six fictional sample books.")
    print("Type your own values, or press Enter to use the shown examples.")
    print("Book text is normalized by the model, so it displays in lowercase.")
    while True:
        print("\n1. List all books        2. Add a book")
        print("3. Find by ID            4. Find by ISBN")
        print("5. Search title          6. Search author")
        print("7. Search category       8. Search year range")
        print("9. Show stock lists     10. Change total copies")
        print("11. Remove a book       12. Top-K scarce in-stock books")
        print("0. Exit")
        choice = ask("Choose an option", "1")
        if choice == "0":
            print("Demo closed. Changes were kept only in memory.")
            return
        try:
            perform_action(inventory, choice)
        except (ValueError, DuplicateID, InvalidQuantity, NotFound) as error:
            print(f"Request rejected: {error}")
        input("\nPress Enter to return to the menu...")


def main() -> None:
    print("Library Inventory Tracker")
    print("No files or services are changed. All data is held in memory.")
    print("1. Interactive menu with your own inputs")
    print("2. Guided walkthrough with sample values and Enter pauses")
    print("0. Exit")
    while True:
        mode = ask("Choose a mode", "1")
        if mode == "1":
            interactive_demo()
            return
        if mode == "2":
            guided_demo()
            return
        if mode == "0":
            return
        print("Choose 0, 1, or 2.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nDemo closed. No data was saved.")
