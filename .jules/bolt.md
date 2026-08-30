## 2023-10-27 - Single Pass Repository Parsing
**Learning:** Found an O(4N) anti-pattern where a list of dictionaries (`repo_nodes`) was being iterated over four times using separate generators (`sum()`, `any()`) and a loop to extract different metrics.
**Action:** When aggregating multiple statistics from a single list of objects (like GraphQL response nodes), always combine the extractions into a single `for` loop to reduce overhead, even if it means replacing concise generator expressions with standard variable accumulation.
