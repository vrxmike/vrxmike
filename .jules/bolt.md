## 2024-03-24 - Optimizing multiple passes in Python loop
**Learning:** Consolidating multiple list comprehensions (`sum(gen_expr)`, `any(gen_expr)`) and nested loops into a single explicit loop over `repo_nodes` combined with `defaultdict` provides a measurable speedup for data aggregation tasks by avoiding redundant iterations over large JSON-like lists.
**Action:** Replace multiple O(N) generator expressions with a single O(N) loop when aggregating multiple statistics from the same list of dictionaries.
