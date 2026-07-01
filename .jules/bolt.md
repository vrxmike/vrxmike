## 2026-07-01 - Optimizing Multi-Pass List Traversals
**Learning:** Combining redundant generator/list comprehensions over the same collection (e.g. stars, forks, languages, private status from GraphQL nodes) into a single iteration pass significantly reduces Python loop overhead, reducing O(4N) time complexity to O(N).
**Action:** Always check if multiple aggregates over the same API response array can be consolidated into a single pass.
