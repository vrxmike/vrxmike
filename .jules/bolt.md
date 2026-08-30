## 2024-05-18 - Multiple O(N) traversals combined into O(N) single pass
**Learning:** In `sync_stats.py`, the `process_stats` function performs multiple O(N) traversals over `repo_nodes`: once to compute `total_stars`, once to compute `total_forks`, once to compute `language_sizes`, and once more (potentially) to determine if there are private repos. While each is O(N), combining them into a single loop reduces the iteration overhead significantly in Python.
**Action:** Combine multiple independent list comprehensions/generator expressions over the same list into a single loop.
