> **IMPORTANT GROUP 2 CORRECTION (official Blackboard curveball):**
> The required operation is `top_k_scarce(k)`, including **only books with
> quantity > 0**, ranked `(quantity, book.id)` ascending. A prior demo and
> earlier descriptions of `top_k_low_stock` included out-of-stock books;
> those descriptions are superseded. Do not cite that earlier output as
> satisfying the final curveball.
> The 3,000-book figures below measure **prefix-search improvement**, not
> the professor's required 500-query Top-K bake-off.

# Group 2 — Phase 3 Optimization and Top-K Report

## Inherited baseline

The supplied implementation includes book/ISBN dictionaries, title/author/category
Tries, stock sets, and publication-year buckets. The Phase 2 README documents
39 component and 14 integration tests; only the root-level component test files
were uploaded here, so the 14 integration tests were **not available** for local
execution. The original 39 component tests passed before any changes.

### Benchmark method

Run `python benchmark_phase3.py --size 3000` from the repository root. The
synthetic dataset creates 3,000 books with realistic overlapping title, author,
category, and publication-year values. It executes 40 repetitions of four
read operations: title prefix, author prefix, publication-year range, ID lookup.
Use the same generator and command in original and optimized versions.

### Measurements (local container; not target Windows laptop)

| Metric | Original Phase 2 | Modified Phase 3 |
| --- | ---: | ---: |
| Books | 3,000 | 3,000 |
| Load time (normal run) | 0.143236 s | 0.150223 s |
| Query workload (normal run) | 0.213003 s | 0.032281 s |
| `cProfile` total runtime | 1.796 s | 0.595 s |
| `cProfile` calls | 6,585,131 | 1,983,587 |

The query workload improved by about **6.60×** in this single local comparison.
Normal-run load time slightly increased. Profiling itself imposes overhead,
so never compare profiled time to ordinary elapsed time. Re-run multiple trials
on the group's own machine to get reliable medians and label those separately.

### Bottleneck and targeted fix

`trie.py` `Trie.search_prefix` repeatedly visited every descendant node after
finding a prefix. `cProfile` showed ~0.697 s of internal time in that function
(80 calls). The Phase 3 implementation caches ID sets along each prefix path,
so prefix queries directly copy the matching ID set rather than walking a large
subtree. Insertion and removal update this cache; regression tests verify
search results after removal. `Trie.insert` was also changed to avoid eager
construction of throwaway child nodes inside `dict.setdefault`.

**Trade-off:** this is optimized for a *read-heavy* workload. Caching ID sets
increases memory usage and index-maintenance work. Profile memory before using
this design for a much larger catalog.

### Curveball: dynamic read-only Top-K

Method: `LibraryInventory.top_k_low_stock(k)`.
Ranking: ascending `(quantity, book.id)` (out-of-stock first), ties by ID.
Uses a bounded heap from Python's `heapq.nsmallest`. Returns up to `k` Book
objects, in priority order, with **no application state mutations**.
Validates `k`, including zero and larger-than-catalog values.

**Confirm the exact Blackboard Group 2 priority metric:** low stock is a natural
library inventory urgency measure but may need adjustment if the instructor
specifies another ranking in the written curveball.

### Testing and known limits

- Before: 39 provided component tests passed.
- After: all 39 component tests plus 7 new Phase 3 tests passed (46 total).
- The 14 documented Phase 2 integration tests were not included in the
  conversation uploads and have not been rerun here.
- No persistent storage, workload isolation, or true multi-user concurrency.
- Benchmark uses synthetic data and one machine; timings are not a SLA.
- Full deep-memory footprint was not measured.

## Suggested 7-minute walkthrough

1. Show original architecture and the baseline benchmark (1 minute).
2. Show `cProfile` locating `trie.py:search_prefix` (1 minute).
3. Explain caching on prefix nodes and demonstrate timing improvement (2 minutes).
4. Show `top_k_low_stock(k)` with different `k` values, ordering and read-only behavior (2 minutes).
5. Show all 46 tests passing and outline memory trade-off (1 minute).

## AI usage disclosure

The Phase 3 changes, synthetic benchmark, tests, and initial write-up were
prepared with ChatGPT assistance. They must be reviewed and understood by the
student team. The code was executed locally against the available uploaded
files, and measured results are reported above. No claim is made that the
missing integration tests or professor-specific priority rubric were verified.


## Group Windows demonstration — November 7, 2026

The group ran `py benchmark_phase3.py --size 3000` from VS Code PowerShell. The terminal displayed:

```text
RECORDS=3000 ADD_SECONDS=0.099452 QUERY_SECONDS=0.034367
```

The same session showed `Ran 46 tests in 0.011s` and `OK`, and the interactive demo returned `LIB-001` (0 copies), `LIB-004` (0 copies), and `LIB-005` (1 copy) for Top-K with `k=3`. These observations support the candidate implementation but do not replace running the missing integration suite or validating the instructor's exact urgency definition.


## Exact Group 2 dashboard bake-off (required separate measurement)

Use `benchmark_topk_group2.py`, a seeded generator which constructs n=10,000
and n=100,000 inventories, interleaves 500 updates and 500 queries (`k=10`)
per trial, and compares naive full sorting to the read-only bounded heap
`top_k_scarce(k)` on identical updates. It asserts exact output equivalence.

```powershell
py benchmark_topk_group2.py --size 10000
py benchmark_topk_group2.py --size 100000
```

Capture output from the group's own machine for the 6 PM live benchmark.
These timings are **not** the same as the earlier Trie optimization numbers.

**Complexity:** full sort O(n log n) per call, bounded nsmallest O(n log k)
for typical small `k`, O(k) heap workspace. Both scan only in-stock IDs;
quantity updates maintain their membership. More aggressive maintained-order
indexes could improve repeated queries but require O(n) or O(log n) update work
and extra memory/complexity.
## Group 2 — Final Top-K Benchmark Results

**Project:** Library Inventory Tracker  
**Phase:** 3 — Optimization  
**Required operation:** `top_k_scarce(k)`  
**Test date:** November 7, 2026

### Benchmark Configuration

- Dataset sizes: 10,000 and 100,000 books
- Random seed: 532
- Top-K value: 10
- Number of queries: 500
- Number of interleaved updates: 500
- Comparison: Full sorting versus heap-based selection

### Measured Performance

| Measurement | 10,000 Books | 100,000 Books |
|---|---:|---:|
| Full-sort query time | 6.539284 seconds | 227.717827 seconds |
| Heap-based query time | 2.729441 seconds | 29.231667 seconds |
| Full-sort update time | 0.028750 seconds | 0.056577 seconds |
| Heap-based update time | 0.032972 seconds | 0.032349 seconds |
| Query speedup | 2.40x | 7.79x |
| Identical results | True | True |

### Optimization Explanation

The original baseline sorts all eligible books by quantity and book ID to return the K scarcest books.

The optimized implementation uses heap-based selection to identify the K lowest-quantity in-stock books without sorting the entire collection.

Full sorting requires O(n log n) time, while heap-based selection requires O(n log k) time for a query, where n is the number of eligible records.

Both approaches return the same results without modifying inventory data.

### Correctness Validation

- All 47 included automated unit tests passed.
- The Top-K demo returned the correct in-stock books.
- Books with zero available copies were excluded.
- The returned books were ordered by ascending quantity.
- Ties are resolved by book ID.
- Both benchmark approaches produced identical results.

### Conclusion

The optimized approach improved Top-K query performance by 2.40x for 10,000 books and 7.79x for 100,000 books in the measured workloads.

The results demonstrate that heap-based selection is more efficient than repeatedly sorting the entire inventory when K is small relative to the number of books.

### Update Performance and Correctness Verification

| Measurement | 10,000 Books | 100,000 Books |
|---|---:|---:|
| Full-sort update time | 0.028750 seconds | 0.056577 seconds |
| Heap-based update time | 0.032972 seconds | 0.032349 seconds |
| Number of updates | 500 | 500 |
| Number of queries | 500 | 500 |
| K value | 10 | 10 |
| Identical results | True | True |

### Validation Summary

Both implementations returned identical Top-K results.

Terminal verification:
IDENTICAL_RESULTS=True

Both implementations completed 500 Top-K queries
interleaved with 500 inventory updates.

The optimized function excludes books with zero copies,
sorts eligible books by ascending quantity, and uses
book ID as the tie-breaker.

All 47 included automated tests passed successfully.