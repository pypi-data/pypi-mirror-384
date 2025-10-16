# gemini-cli-command_prompt-template_v2

Task: From {prompt_or_md} and {user_context}, synthesize a Gemini CLI custom command TOML that generalizes the task via inferred placeholders.

Heuristics

1) Mark user-changeable text (queries, titles) → {{query}}
2) Paths/globs → {{path}}
3) Targets/entities (repo/service/ticket) → {{target}}
4) Quantities/limits → {{limit}}
If uncertainty remains, collapse everything into {{args}}. Never exceed 3 distinct placeholders unless the text explicitly lists more inputs.

Transformations

- Preserve order and intent; remove fluff.
- If the source includes code or CLI calls, render them as `!{...}` lines inside the prompt.
- Prefer imperative voice (“Do X, then Y”). Add brief, testable acceptance lines inside the prompt if helpful.

Deliverable (only TOML; no extra prose)

# Command: /{namespace:=user}:{command:=auto-from-title}

# Usage: /{namespace}:{command} "example value(s)"

# Args

# - {{query}}: what to search or summarize

# - {{path}}: file or directory (optional)

prompt = """
<final instruction with placeholders and any !{...} inserts>
"""

Checks

- Valid TOML; balanced triple quotes.
- Includes ≥1 placeholder with matching Usage.
- Names are lowercase, kebab-case.
- No commentary outside TOML.
