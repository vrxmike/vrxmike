## 2026-07-03 - O(n) Single-Pass Loop Optimization in sync_stats.py
**Learning:** Found an opportunity to collapse multiple separate loops (generator expressions and a standard for-loop) iterating over the same dataset into a single pass. While built-in `sum()` and `any()` run fast in C, multiple passes over `repo_nodes` incur generator overhead and duplicate memory accesses.
**Action:** Always look for O(n * k) sequential iterations over the same collection that can be safely collapsed into an O(n) single pass to reduce execution time and algorithmic overhead.
