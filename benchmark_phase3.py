"""Reproducible library load/search benchmark; use before and after changes.

Usage: python benchmark_phase3.py --size 3000
       python -m cProfile -s tottime benchmark_phase3.py --size 3000
"""
import argparse
import time
from inventory import LibraryInventory
from models import Book


def make_book(i):
    return Book(
        id=f'PERF-{i:06d}',
        title=f'Guide to Knowledge Volume {i} and Data',
        author=f'Researcher {i % 257}',
        category=f'Category {i % 13}',
        year=1950 + i % 76,
        quantity=i % 8,
    )


def run(size=3000):
    inventory = LibraryInventory()
    start = time.perf_counter()
    for i in range(size):
        inventory.add_book(make_book(i))
    add_seconds = time.perf_counter() - start
    start = time.perf_counter()
    for _ in range(40):
        inventory.search_title('Guide to Knowledge')
        inventory.search_author('Researcher 1')
        inventory.search_year_range(1980, 1990)
        inventory.get_book('PERF-000500')
    query_seconds = time.perf_counter() - start
    print(f'RECORDS={len(inventory.books)} ADD_SECONDS={add_seconds:.6f} QUERY_SECONDS={query_seconds:.6f}')
    return inventory

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--size', type=int, default=3000)
    args = p.parse_args()
    run(args.size)
