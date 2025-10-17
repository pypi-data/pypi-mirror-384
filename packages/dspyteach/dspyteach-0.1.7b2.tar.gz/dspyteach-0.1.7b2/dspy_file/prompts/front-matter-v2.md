<!-- $1 = source Markdown text; $2 = template name/title (optional; infer if missing); $3 = maximum placeholders allowed (1–9; default 7); $4 = input parameters block; $5 = controlled taxonomy/list block; $6 = stage mapping/rules block; $7 = output examples block -->

# $2

Task: Given $1, produce a structured **metadata block** and then emit the original body unchanged. The metadata must expose identifiers, categories, optional lifecycle/stage, optional dependencies, optional provided artifacts, and a concise summary. Output = metadata, blank line, then $1.

## Inputs

$4

## Canonical taxonomy (exact strings)

$5

### Stage hints (for inference)

$6

## Algorithm

1. Extract signals from $1

   * Titles/headings, imperative verbs, intent sentences, explicit tags, and dependency phrasing.

2. Determine the primary identifier

   * Prefer explicit input; otherwise infer from main action + object.
   * Normalize (lowercase, kebab-case, length-capped, starts with a letter).
   * De-duplicate.

3. Determine categories

   * Prefer explicit input; otherwise infer from verbs/headings vs $5.
   * Validate, sort deterministically, and de-dupe (≤3).

4. Determine lifecycle/stage (optional)

   * Prefer explicit input; otherwise map categories via $6.
   * Omit if uncertain.

5. Determine dependencies (optional)

   * Parse phrases implying order or prerequisites; keep id-shaped items (≤5).

6. Determine provided artifacts (optional)

   * Short list (≤3) of unlocked outputs.

7. Compose summary

   * One sentence (≤120 chars): “Do <verb> <object> to achieve <outcome>.”

8. Produce metadata in the requested format

   * Default to a human-readable serialization; honor any requested alternative.

9. Reconcile if input already contains metadata

   * Merge: explicit inputs > existing > inferred.
   * Validate lists; move unknowns to an extension field if needed.
   * Remove empty keys.

## Assumptions & Constraints

* Emit exactly one document: metadata, a single blank line, then $1.
* Limit distinct placeholders to ≤ $3.

## Validation

* Identifier matches a normalized id pattern.
* Categories non-empty and drawn from $5 (≤3).
* Stage, if present, is one of the allowed stages implied by $6.
* Dependencies, if present, are id-shaped (≤5).
* Summary ≤120 chars; punctuation coherent.
* Body text $1 is not altered.

## Output format examples

$7
