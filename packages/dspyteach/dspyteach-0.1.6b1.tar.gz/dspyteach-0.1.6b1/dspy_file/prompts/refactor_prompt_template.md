# dspy-file_refactor-prompt_template

Task: From the given Markdown ($1), output a reusable prompt template that:

- Mirrors the section/layout structure.
- Replaces every instance-specific span with numbered placeholders `$1..$N` (verbatim).
- Includes a top comment mapping of placeholder semantics.
- Introduces missing, commonly expected sections when context implies them (e.g., analysis → Affected files, Root cause, Proposed fix, Tests, Docs gaps, Open questions).
- Contains no copied facts from $1.

Inputs

- $1 = source Markdown text
- $2 = template name to embed (optional; defaults to inferred genre)
- $3 = maximum placeholders (1–9; default 7)

## **Algorithm**

1) Classify genre (analysis/planning/summary/how-to/other) from headings + verbs.
2) Extract candidate fields (title, summary, bullets, code, paths, IDs, dates, metrics). Rank by importance; cap to $3.
3) Emit:
   <!-- $1=..., $2=..., ... -->
   **{$2 or Inferred Name}**

   (preserved headings/lists with leaves replaced by $1..$N)
   Optional “Output format” block if genre=analysis or planning.
4) Validation pass:
    **ensure**
   - ≤$3 placeholders
   - no verbatim sentences from input
   - and literal `$` tokens remain.

Output only the final template Markdown.
