# gemini-cli_commands-prompt-template_v1

Goal: Produce a parameterized template from {source_text} using positional placeholders and a machine-checkable Arg spec.

Requirements

- Use {placeholder_syntax} (default: `$1..$9`).
- Insert ≤ {max_placeholders} high-impact placeholders; deduplicate repeats.
- Emit JSON Arg spec immediately after the templated text, with this shape:
    {
      "args": [
        { "id": "$1", "name": "{name}", "hint": "{short_hint}", "example": "{example}", "required": true, "validate": "{regex|rule}" }
      ]
    }
- Preserve markdown/code formatting byte-for-byte except at replacement spans.
- Do not change meaning, tone, or constraints of {source_text}.

Heuristics (apply in order)

1) User-owned identifiers: paths, repo/org names, endpoints, secrets placeholders.
2) Content slots: problem statement, target audience/domain, primary input.
3) Tunables: N/limits/timeouts only if not hard requirements.
4) Repeated literals → one arg; propagate to all occurrences.
5) Skip boilerplate constants (e.g., license names, standard flags) unless context marks them variable.

Edge cases

- If already templated, extend only with missing args; do not renumber existing placeholders.
- If no clear candidates, introduce `$1` as `topic_or_input` at the primary noun phrase of the opening sentence and document it.
- For JSON/YAML in code fences, ensure placeholders remain valid strings (quote if needed).

Acceptance tests (must pass)

- T1: All placeholders appear in the Arg spec; counts match.
- T2: Substituting provided examples yields valid markdown and runnable snippets.
- T3: Repeated concepts map to a single placeholder consistently.
- T4: Total placeholders ≤ {max_placeholders}; none are trivial.

Deliverables

1) **Templated Text** — {source_text} with placeholders inserted per heuristics.
2) **Args JSON** — machine-checkable spec as shown above.
