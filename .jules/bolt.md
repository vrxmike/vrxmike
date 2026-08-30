## 2026-06-12 - Generator Expressions vs Single Passes
**Learning:** While Python generator expressions (e.g. `sum(x for x in list)`) are elegant, executing multiple of them over the same large list (like `repo_nodes`) causes redundant O(n) passes. In contexts where many metrics are derived from the same list of dicts, a single explicit loop is significantly faster.
**Action:** When extracting multiple aggregates from a large list of objects, consolidate the logic into a single `for` loop rather than using multiple generator expressions or list comprehensions.
