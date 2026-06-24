## 2023-10-27 - Fast SVG generation inside nested loops
**Learning:** Extracting coordinate calculations out of nested loops gives substantial performance boosts in Python. This is especially true when creating large HTML/SVG blocks dynamically inside nested loops. Precalculating `Y_POSITIONS` avoids duplicate computation 53 times per day.
**Action:** When dynamically constructing HTML/SVG nodes inside a loop, pre-calculate constant coordinate maps (like `Y_POSITIONS`).

## 2023-10-27 - Markdown Injection with Regex vs String Slicing
**Learning:** Using regex `re.sub` with lambdas for simple start/end marker string replacements is incredibly slow compared to standard string slicing. String slicing operations (`str.find` + `str[:]`) run approximately ~95% faster than compiling a regex and executing a dynamic lambda on match objects.
**Action:** Always prefer basic string search and slice capabilities when simply replacing content bounded by static text markers (e.g. `<!-- START -->` / `<!-- END -->`) rather than resorting to regex, especially on large texts.
