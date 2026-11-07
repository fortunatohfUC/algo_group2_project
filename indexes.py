"""Stock availability and publication-year indexes for the library PoC.

LibraryInventory passes its own containers to the functions below. The original
StockYearIndexes class is also available for standalone use and existing tests.
Do not create a second StockYearIndexes object inside LibraryInventory: its
existing containers already hold the index data.

Stock updates take O(1) average time. Year updates take O(1) average time for
an existing year, but O(Y) when inserting or deleting a distinct sorted year.
The indexes use O(n + Y) space for n books and Y distinct years.
"""

from bisect import bisect_left, bisect_right, insort

from models import validate_quantity


def _check_year(year):
    if type(year) is not int:
        raise ValueError("Year must be an integer")


def add_stock(in_stock, out_of_stock, book_id, quantity):
    """Add or classify a book by quantity; average O(1)."""
    validate_quantity(quantity)
    # Keep each ID in only one stock set.
    in_stock.discard(book_id)
    out_of_stock.discard(book_id)
    if quantity > 0:
        in_stock.add(book_id)
    else:
        out_of_stock.add(book_id)


def update_stock(in_stock, out_of_stock, book_id, quantity):
    """Change stock classification for an indexed book; average O(1)."""
    validate_quantity(quantity)
    if book_id not in in_stock and book_id not in out_of_stock:
        raise KeyError(f"Book ID not found in stock index: {book_id}")
    add_stock(in_stock, out_of_stock, book_id, quantity)


def remove_stock(in_stock, out_of_stock, book_id):
    """Remove an ID from both stock sets; average O(1)."""
    in_stock.discard(book_id)
    out_of_stock.discard(book_id)


def get_in_stock(in_stock):
    """Return a copy of in-stock IDs; O(k) for k returned IDs."""
    return in_stock.copy()


def get_out_of_stock(out_of_stock):
    """Return a copy of out-of-stock IDs; O(k) for k returned IDs."""
    return out_of_stock.copy()


def add_year(year_buckets, sorted_years, year, book_id):
    """Add an ID by year; O(1) average existing year, O(Y) new year."""
    _check_year(year)
    if year not in year_buckets:
        year_buckets[year] = set()
        insort(sorted_years, year)
    year_buckets[year].add(book_id)


def remove_year(year_buckets, sorted_years, year, book_id):
    """Remove an ID; O(1) average or O(Y) if a year disappears."""
    _check_year(year)
    if year not in year_buckets:
        return
    year_buckets[year].discard(book_id)
    if not year_buckets[year]:
        # Remove the year only after its last book is gone.
        del year_buckets[year]
        position = bisect_left(sorted_years, year)
        sorted_years.pop(position)


def search_year_range(year_buckets, sorted_years, start, end):
    """Return IDs in inclusive years; O(log Y + Y' + k) average.

    Y' is the number of matching years and k is the number of matching IDs.
    """
    _check_year(start)
    _check_year(end)
    if start > end:
        raise ValueError("Start year cannot be greater than end year")
    left = bisect_left(sorted_years, start)
    right = bisect_right(sorted_years, end)
    results = set()
    for position in range(left, right):
        results.update(year_buckets[sorted_years[position]])
    return results
