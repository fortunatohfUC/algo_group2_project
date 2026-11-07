# Library Inventory Implementation Notes

## Built and design change

This proof of concept implements the inherited read-heavy library catalog in Python. A Book represents one edition, and quantity counts its copies. The internal ID is the primary key. The one design extension is optional normalized ISBN lookup, following the original team's clarification. ISBN is separate from the internal ID; duplicate normalized ISBNs are rejected. ISBN-10 and ISBN-13 are not converted into equivalent keys. Checksum validation does not verify a title against a publishing database.

## Structure and operations

LibraryInventory owns the Book dictionary, ISBN-to-ID dictionary, three Tries, stock sets, year buckets, and sorted distinct years. The catalog, Trie, and index modules provide operations over these structures. Secondary indexes contain IDs, which resolve to the current Book records. The 11 public methods cover add, remove, ID and ISBN lookup, three prefix searches, inclusive year-range search, two stock reports, and quantity updates.

## Run and demonstrate

Use Python 3.10 or later, with no third-party packages. From the repository root, run the commands below. Demo mode 1 accepts user inputs. Mode 2 shows six raw fictional records in a table and pauses between operations. It demonstrates empty results, stock changes, removal preserving shared indexes, and expected input errors.

```sh
python3 demo.py
python3 -m unittest discover -s . -v
python3 -m unittest discover -s tests -v
```

## Tests and consistency

Run both test commands: root discovery runs 39 component tests, and tests-directory discovery runs 14 integration tests. All 53 pass with the actual modules. Coverage includes duplicate IDs and ISBNs, invalid quantities, normalized searches, inclusive ranges, shared Trie paths, empty year-bucket removal, and cross-index consistency. Expected invalid inputs are checked before changes. Removal validates the catalog, clears secondary indexes, then deletes the record and ISBN mapping. Quantity changes replace the frozen Book and update stock membership.

## Complexity and tradeoffs

Dictionary lookups and set membership are average constant time. Prefix search traverses the prefix and matching subtree, then sorts matching IDs. A year-range query costs expected O(log Y + Yprime + k), where Y is distinct years, Yprime is matching years, and k is returned books. Inserting or deleting a distinct year may shift O(Y) list entries. This corrects the inherited brief's constant-time year-update claim. Quantity replacement also revalidates text, so its complete cost includes text length. Additional indexes trade memory and update work for faster reads.

## Limits and next team

Storage is in memory only. Metadata editing, patron circulation, persistent storage, concurrency, and rollback after unexpected runtime failures are not implemented. Stock and year results are unordered; prefix results are sorted by ID. Text normalization removes original capitalization and punctuation. The next team should profile actual workloads before optimizing, preserve the tested invariants, and distinguish measured results from complexity estimates. No scalability or latency benchmark is claimed for the six-record demonstration.

## AI Usage Appendix

### Tools and contributions

ChatGPT was used for inherited-design review and explanations of the architecture, ISBN validation, and dictionary lookup. OpenAI Codex assisted with the inventory integration, regression tests, demonstration script, README, handoff drafting, and verification.

### Significant prompts used with ChatGPT

"Review the inherited Phase 1 Library Inventory Tracker design. Identify all proposed data structures, their responsibilities, expected time complexities, and dependencies. Explain how they work together."
"Evaluate the proposed dictionary, Trie, stock sets, and year-bucket architecture. What assumptions, ambiguities, or potential weaknesses should we resolve before implementation?"
"Explain how to implement ISBN-10 and ISBN-13 normalization and check-digit validation. What edge cases should we consider?"
"How should we use Python dictionaries to support O(1) average book lookup by internal ID and ISBN, while keeping the main catalog as the single source of truth?"

### Corrections and limitations

In the Codex-assisted integration, the initial code assumed standalone stock/year helper functions, while the first teammate implementation exposed a class. Passing tests against private stand-ins did not establish compatibility with that implementation. The shared interface was reconciled, the stale stock/year test import was repaired, and all 53 tests were rerun against the real modules. An earlier explanation also simplified quantity updates to constant time, overlooking text revalidation when constructing the replacement Book. The handoff now states that qualification. AI output required review against actual code and observed results rather than acceptance from passing stand-in tests alone.


## Phase 3 — Optimization and monitoring dashboard handoff (November 7, 2026)

**Scope:** The inherited library catalog remains the source of truth. Phase 3 adds a read-only Top-K query and optimizes read-heavy prefix searches. Previous Phase 2 implementation decisions and documentation remain above for historical context.

**Curveball API:** `LibraryInventory.top_k_low_stock(k)` returns up to `k` book records sorted by `(quantity, book.id)` ascending. A smaller nonnegative quantity is treated as more urgent (out-of-stock first). Ties break deterministically by book ID. `k` must be a nonnegative integer (booleans rejected); `k=0` returns an empty list. There is no persistent mutation, reservation or stock adjustment. This metric must be checked against the exact written Blackboard requirements before final tagging.

**Optimization:** Trie nodes now maintain matching-ID sets along each indexed prefix, making a typical prefix search approximately O(m + r) rather than traversing descendant nodes, where `m` is prefix length and `r` is matching record count. This improves repeated reads but **increases memory consumption and insertion/removal work**. The catalog's three Tries and the rest of the inventory interfaces remain intact. The `trie.py` insertion path also avoids eager construction of temporary `TrieNode` objects.

**Verification:** The 39 inherited root-level unit tests and 7 new Phase 3 tests passed on the prepared project (46 total); the user also observed `Ran 46 tests ... OK` locally in Windows VS Code. The original repository contains an additional `tests/` directory documenting 14 integration tests; it was absent from the separately uploaded project files and must be rerun against the combined GitHub repository before final acceptance.

**Performance:** Run `py benchmark_phase3.py --size 3000` from the repo root. A single controlled environment measurement found Phase 2 query workload 0.213003 s and Phase 3 query workload 0.032281 s (~6.6x faster). These are **separate from** the Windows result observed during the group demonstration: `RECORDS=3000 ADD_SECONDS=0.099452 QUERY_SECONDS=0.034367`. Do not present either as a guaranteed service-level performance improvement. For details and limitations see `PHASE3_PROFILE_REPORT.md`.

**How to hand off:** Preserve the original design document and the repository `tests/` directory. Review the changed files, run all root and integration tests, rerun the benchmark multiple times on identical data/hardware, document any failures, then create the instructor-required Phase 3 tag only after team approval.

### Phase 3 AI usage (separate from inherited Phase 2 AI history)

AI assistance was used to inspect the inherited architecture, suggest a profiling approach, generate a candidate Trie optimization and dynamic Top-K implementation, prepare tests and benchmark scripts, and draft the handoff. The team is responsible for verifying behavior against the actual inherited code, rerunning tests and profiling on its own machine, evaluating the memory trade-off, and correcting documentation. Representative actual requests included: 'What exactly should our Group 2 do for Phase 3?', 'What files do you want from this repository?', and help to run tests, demo, benchmark and prepare files for GitHub upload. A limitation identified during verification was that only 39 inherited component tests were present in the uploaded project files, so the other 14 integration tests were not verified by the AI-assisted run. The team should not mistake the improved synthetic benchmark for production performance, or assume that low stock matches the Blackboard urgency rule without checking.


## Official Group 2 Phase 3 correction

Use `LibraryInventory.top_k_scarce(k)`: **only quantity > 0**, sorted by
`(quantity, book.id)` ascending. The initial example including zero-stock
books was incorrect under the professor's written Group 2 curveball and has
been superseded. The version in this package excludes out-of-stock books.
Run `py benchmark_topk_group2.py --size 10000` and `--size 100000` for
500 interleaved updates and queries with k=10 and a seeded reproducible dataset.
Keep the inherited `tests/` folder intact and rerun its integration tests.
