## 2026-06-19 - Batch iteration over nested data lists
**Learning:** Multiple separate list comprehensions or sums over the same data structures (like fetching totals for GitHub API metrics) creates unnecessary O(n) loops.
**Action:** Always verify if multiple metric aggregations over the same list can be merged into a single pass loop.
