"""Stock availability and publication-year indexes for the library PoC."""

from bisect import bisect_left, bisect_right, insort


class StockYearIndexes:
    """Store book IDs in stock sets and publication-year buckets."""

    def __init__(self):
        self.in_stock = set()
        self.out_of_stock = set()
        self.year_buckets = {}  # year -> set of book IDs
        self.sorted_years = []  # distinct years in ascending order

    @staticmethod
    def _check_quantity(quantity):
        # bool is rejected even though bool is a subclass of int.
        if type(quantity) is not int or quantity < 0:
            raise ValueError("Quantity must be a non-negative integer")

    @staticmethod
    def _check_year(year):
        if type(year) is not int:
            raise ValueError("Year must be an integer")

    def add_stock(self, book_id, quantity):
        """Add or classify a book by quantity; average O(1)."""
        self._check_quantity(quantity)
        # Ensure a book ID is never in both stock sets.
        self.in_stock.discard(book_id)
        self.out_of_stock.discard(book_id)
        if quantity > 0:
            self.in_stock.add(book_id)
        else:
            self.out_of_stock.add(book_id)

    def update_stock(self, book_id, quantity):
        """Change stock classification for an indexed book; average O(1)."""
        self._check_quantity(quantity)
        if book_id not in self.in_stock and book_id not in self.out_of_stock:
            raise KeyError(f"Book ID not found in stock index: {book_id}")
        self.add_stock(book_id, quantity)

    def remove_stock(self, book_id):
        """Remove an ID from both stock sets; average O(1)."""
        self.in_stock.discard(book_id)
        self.out_of_stock.discard(book_id)

    def get_in_stock(self):
        """Return a COPY of in-stock IDs; O(k) for k returned IDs."""
        return self.in_stock.copy()

    def get_out_of_stock(self):
        """Return a COPY of out-of-stock IDs; O(k) for k returned IDs."""
        return self.out_of_stock.copy()

    def add_year(self, year, book_id):
        """Index an ID by year; O(1) average existing year, O(Y) new year."""
        self._check_year(year)
        if year not in self.year_buckets:
            self.year_buckets[year] = set()
            # Keep distinct years sorted for binary search.
            insort(self.sorted_years, year)
        self.year_buckets[year].add(book_id)

    def remove_year(self, year, book_id):
        """Remove an ID; O(1) average or O(Y) if a year disappears."""
        self._check_year(year)
        if year not in self.year_buckets:
            return
        self.year_buckets[year].discard(book_id)
        if not self.year_buckets[year]:
            # Delete empty bucket and its entry in the sorted list.
            del self.year_buckets[year]
            position = bisect_left(self.sorted_years, year)
            self.sorted_years.pop(position)

    def search_year_range(self, start, end):
        """Return IDs within inclusive years; O(log Y + Y' + k) average."""
        self._check_year(start)
        self._check_year(end)
        if start > end:
            raise ValueError("Start year cannot be greater than end year")
        # Binary search finds the first and last relevant year positions.
        left = bisect_left(self.sorted_years, start)
        right = bisect_right(self.sorted_years, end)
        results = set()
        for year in self.sorted_years[left:right]:
            results.update(self.year_buckets[year])
        return results
