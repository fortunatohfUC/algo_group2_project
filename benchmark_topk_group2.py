"""Group 2 reproducible dashboard bake-off, Python stdlib only.

    py benchmark_topk_group2.py --size 10000
    py benchmark_topk_group2.py --size 100000
    py -m cProfile -s tottime benchmark_topk_group2.py --size 10000

Generate seeded realistic quantities. Time 500 query calls with k=10 and
interleave 500 quantity updates. Compare full-sort against heap selection on
IDENTICAL update sequences and states; assert exact result equality.
"""
import argparse
import random
import time
from inventory import LibraryInventory
from models import Book


def make_dataset(n: int, seed: int):
    rng = random.Random(seed)
    quantities = [rng.randrange(0, 51) for _ in range(n)]
    return [Book(id=f'LIB-{i:07d}', title=f'Library Edition {i%251}', author=f'Author {i%173}',
                 category=f'Category {i%19}', year=1950+i%75, quantity=quantities[i])
            for i in range(n)]


def top_k_full_sort(inventory: LibraryInventory, k: int):
    """Baseline: full sort every live in-stock book: O(n log n)."""
    return sorted((inventory.books[bid] for bid in inventory.in_stock),
                  key=lambda b: (b.quantity, b.id))[:k]


def run(size=10000, seed=532, queries=500, k=10):
    if size < 0 or queries < 0 or k < 0:
        raise ValueError('size, queries and k must be nonnegative')
    inv = LibraryInventory()
    books = make_dataset(size, seed)
    start = time.perf_counter()
    for book in books:
        inv.add_book(book)
    build = time.perf_counter() - start
    rng = random.Random(seed + 1)
    changes = [(rng.randrange(size), rng.randrange(0, 51)) for _ in range(queries)] if size else []
    original = [book.quantity for book in books]

    def trial(query_func):
        query_elapsed = 0.0
        update_elapsed = 0.0
        signatures = []
        for i, new_qty in changes:
            ts = time.perf_counter()
            inv.update_quantity(books[i].id, new_qty)
            update_elapsed += time.perf_counter() - ts
            ts = time.perf_counter()
            found = query_func(inv, k)
            query_elapsed += time.perf_counter() - ts
            signatures.append(tuple((b.id, b.quantity) for b in found))
        return query_elapsed, update_elapsed, signatures

    naive_query, naive_update, expected = trial(top_k_full_sort)
    # Restore the initial dataset outside timed trials.
    for i, qty in enumerate(original):
        if inv.books[books[i].id].quantity != qty:
            inv.update_quantity(books[i].id, qty)
    heap_query, heap_update, actual = trial(lambda inventory, k: inventory.top_k_scarce(k))
    assert expected == actual, 'Optimized Top-K differs from baseline'
    print(f'N={size} SEED={seed} QUERIES={len(changes)} K={k} BUILD_SECONDS={build:.6f}')
    print(f'FULL_SORT_QUERY_SECONDS={naive_query:.6f} FULL_SORT_UPDATE_SECONDS={naive_update:.6f}')
    print(f'HEAP_QUERY_SECONDS={heap_query:.6f} HEAP_UPDATE_SECONDS={heap_update:.6f}')
    print(f'QUERY_SPEEDUP={naive_query / heap_query:.2f}x' if heap_query else 'QUERY_SPEEDUP=N/A')
    print('IDENTICAL_RESULTS=True; BOTH_RUNS_INTERLEAVE_500_UPDATES_AND_QUERIES' if len(changes)==500 else 'IDENTICAL_RESULTS=True')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=532)
    parser.add_argument('--queries', type=int, default=500)
    parser.add_argument('--k', type=int, default=10)
    args = parser.parse_args()
    run(args.size, args.seed, args.queries, args.k)
